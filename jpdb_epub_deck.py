import os
import sys
import zipfile
import argparse
import requests
import glob
from dotenv import load_dotenv
from html.parser import HTMLParser

# load environment variables from .env file
load_dotenv()

# ---- Find required mingw binaries, load c++ module ----
#--------------------------------------------------------
MINGW_BIN_PATH = os.environ.get("MINGW_BIN_PATH")
MECAB_ROOT = os.environ.get("MECAB_ROOT")
JPDB_API_KEY = os.environ.get("JPDB_API_KEY")

if not JPDB_API_KEY:
    print("Error: 'JPDB_API_KEY' environment variable not set.")
    print("Please find your API key (jpdb.io -> settings -> Account Information) and set it to an environment variable.")
    sys.exit(1)

if MINGW_BIN_PATH:
    try:
        os.add_dll_directory(MINGW_BIN_PATH)
    except AttributeError:
        print("Warning: os.add_dll_directory() not found . This script requires python 3.8+ on Windows.")
else:
    print("Warning: MINGW_BIN_PATH environment variable not set.")
    print("This script may fail to import the C++ module if MinGW's bin directory is not on your system PATH.")


if MECAB_ROOT: 
    try:
        mecab_bin_path = os.path.join(MECAB_ROOT, "bin")
        os.add_dll_directory(mecab_bin_path)
    except AttributeError:
        print("Warning: unable to add the dll directory for MeCab!")
else:
    print("Warning: 'MECAB_ROOT' environment variable not set.")

sys.path.append('build')

try:
    import jp_epub_parser
    print("Successfully imported C++ module.")
except ImportError as e:
    print(f"Error importing C++ module: {e}")
    print("Did you forget to cmake and build in the build directory?")
    sys.exit(1)
#--------------------------------------------------------

class EpubTextExtractor(HTMLParser):
    """
    Wrapper class for the HTMLParser to extract words from our epub files.
    """
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return "".join(self.text_parts)


def get_text_from_epub(epub_path):
    """
    Function to open an epub file, find all .xhtml content, and return as a single string.
    """
    print(f"\nAttempting to read epub: {epub_path}")

    parser = EpubTextExtractor()

    with zipfile.ZipFile(epub_path, 'r') as epub:
        for item in epub.infolist():
            if item.filename.endswith(('.html', '.xhtml')):
                with epub.open(item) as file_content:
                    html_bytes = file_content.read()
                    parser.feed(html_bytes.decode('utf-8'))

    return parser.get_text()

def post_to_api(api_url, headers, data):
    """
    Helper function to handle API requests.
    """

    try:
        response = requests.post(api_url, headers=headers, json=data)

        response.raise_for_status()

        response_json = response.json()
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"A connection error occured: {e}")
        return None
    
    return response_json

def create_jpdb_deck(api_key, deck_name, deck_position):
    """
    Creates a new empty deck on jpdb.io with the specified name.
    Returns the ID of the newly created deck.
    https://jpdb.stoplight.io/docs/jpdb/fca8dbc1b3fad-create-a-new-empty-deck
    """
    print(f"Attempting to create new deck with name '{deck_name}'")

    api_url = "https://jpdb.io/api/v1/deck/create-empty"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "name": deck_name,
        "position": deck_position
    }

    response_json = post_to_api(api_url, headers, data)

    if "id" in response_json:
        print(f"Successfully created deck {deck_name}. Deck ID: {response_json["id"]}")
        return response_json["id"]
    else:
        print("Error: API response did not contain a deck ID.")
        return None


def jpdb_parse_text(api_key, words):
    """
    Function to call the /parse endpoint of jpdb api to get the vid and sid of vocab so we can add to deck.
    Returns an array of arrays of size 2, that contain the vid and sid of the words we've looked up.
    https://jpdb.stoplight.io/docs/jpdb/609bb98ccd378-parse-text
    """
    api_url = "https://jpdb.io/api/v1/parse"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "text": words,
        "token_fields": [],
        "vocabulary_fields": [
            "vid",
            "sid"
        ]
    }

    response_json = post_to_api(api_url, headers, data)

    if "vocabulary" in response_json:
        print(f"Successfully parsed {len(response_json["vocabulary"])} words.")
        return response_json["vocabulary"]
    else:
        print("Error: API response did not contain any vocabulary data.")
        return None


def jpdb_add_vocabulary_to_deck(api_key, deck_id, vocabulary_array):
    """
    Function to call the add-vocabulary JPDB API end point.
    We must supply the deck id, plus the vid and sid of the words in the form of a an array of arrays.
    https://jpdb.stoplight.io/docs/jpdb/b1df38104bc32-add-vocabulary-to-a-deck
    """
    api_url = "https://jpdb.io/api/v1/deck/add-vocabulary"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "id": deck_id,
        "vocabulary": vocabulary_array
    }

    print(f"Adding {len(vocabulary_array)} to deck with id: {deck_id}")
    # response contains no json data, don't do anything with it
    post_to_api(api_url, headers, data)


def jpdb_list_user_decks(api_key):
    """
    Function to retrieve the user's decks, and then retrieve the number of cards 
    for the provided deck id.
    https://jpdb.stoplight.io/docs/jpdb/cfe08d68ca570-list-user-decks
    """
    api_url = "https://jpdb.io/api/v1/list-user-decks"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "fields": ["id", "name", "vocabulary_count", "vocabulary_known_coverage"]
    }

    print(f"Retrieving user deck information...")
    json_response = post_to_api(api_url, headers, data)
    if "decks" in json_response:
        print(f"Successfully retrieved information for {len(json_response["decks"])} decks.")
        return json_response["decks"]
    else:
        print(f"Unable to find any decks for the API key's associated user!")
        return None


def create_new_deck_from_epub(deck_name, epub_file, deck_position):
    # Create the new deck
    deck_id = create_jpdb_deck(JPDB_API_KEY, deck_name, deck_position)
    if not deck_id:
        print("Error: failed to create deck, exiting.")
        sys.exit(1)

    
    book_text = get_text_from_epub(epub_file)
    print(f"successfully read {len(book_text)} characters")

    print(f"Calling C++ text parser...")
    word_counts = jp_epub_parser.unique_word_count(book_text)
    print(f"Parsing complete. Found {len(word_counts)} unique words.")

    # Sort the words by word count
    sorted_words = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)

    # First we must get the vid and sid for every vocab item by parsing the text
    processed_words = 0

    # Process in batches of 1000 vocabulary items (any higher and API returns too many requests)
    request_size = 1000

    # Process the batches
    while (processed_words < len(sorted_words)):
        # Create a string of just the keys (words) from our sorted words list
        words_for_lookup = ""
        for word, count in sorted_words[processed_words:processed_words+request_size]:
            words_for_lookup += word
            words_for_lookup += " "


        # Fetch the IDs using the parse-text endpoint
        print(f"Fetching IDs for words {processed_words} to {processed_words+request_size}.")
        # API returns a list of lists of length 2, containing the vid and sid
        vocabulary_id_lists = jpdb_parse_text(JPDB_API_KEY, words_for_lookup)

        # Add the batch to the deck
        jpdb_add_vocabulary_to_deck(JPDB_API_KEY, deck_id, vocabulary_id_lists)

        # Move onto the next request
        processed_words += request_size

    # Double check that we've successfully added all the words
    # First get the list array of decks
    decks = jpdb_list_user_decks(JPDB_API_KEY)

    # Find the deck we created, check the contents
    # Reponse is of format [id, number of words, user coverage]
    print(f"----------------------------")
    for deck in decks:
        if deck[0] == deck_id:
            return deck
    
    print(f"----------------------------")
    print("Failed to find newly created deck!")
    return None


def process_directory_of_epubs(epub_directory):
    # Get the list of decks, we'll skip over any that have the same name.
    decks = jpdb_list_user_decks(JPDB_API_KEY)

    # Get list of all .epub files
    epub_files = glob.glob(os.path.join(epub_directory, "*.epub"))
    print("Found these files for processing: ")
    for file in epub_files:
        print(os.path.basename(file))
    
    results = []

    # Process each file
    for file in epub_files:
        deck_name = os.path.basename(file)
        deck_name = os.path.splitext(deck_name)[0]
        deck_position = 0

        # Check if a deck with the same name already exists.
        skip = False
        for deck in decks:
            if deck_name == deck[1]:
                print(f"Found deck with name: {deck[1]} and ID:{deck[0]}, skipping this file.")
                skip = True
            
        if not skip:            
            try:
                new_deck_data = create_new_deck_from_epub(deck_name, file, deck_position)
                if new_deck_data:
                    results.append(new_deck_data)
                else:
                    print("ERROR: Script failed to create new deck successfully!")

            except FileNotFoundError: 
                print(f"Error: File not found at {file}")
            except zipfile.BadZipFile:
                print(f"Error: ZipFile could not read {file}")
            except RuntimeError as e:
                print(f"A C++ runtime error ocurred: {e}")
    
    print("================ RESULTS ================")
    for result in results:
        print(f"Successfully created new deck: {result[1]} with ID: {result[0]}")
        print(f"Total unique words added: {result[2]}")
        print(f"Current user coverage of words: {result[3]:.2f}%")


if __name__ == "__main__":
    # Handle argument parsing
    parser = argparse.ArgumentParser(
        description = "Create a vocabulary deck on jpdb.io from an epub file."
    )
    
    parser.add_argument(
        "epub_path",
        help="The file path to the .epub book to parse."
    )
    parser.add_argument(
        "-d", 
        "--dir",
        action="store_true",
        help="If set, the script will attempt to parse a whole directory of epub files."
    )
    parser.add_argument(
        "--deck-name",
        help="The name of the new deck to make. If not selected the filename for the epub will be used.",
        default=None
    )
    parser.add_argument(
        "--deck-position",
        help="Which position in the user's deck list to add. A value of 0 will create the deck at the front, default is to append to the end.",
        default=None
    )

    args = parser.parse_args()
    epub_path = args.epub_path

    # First, check if we are processing a directory or not.
    if args.dir:
        print(f"Parse directory flag set, attempting to process provided folder {epub_path}.")
        if os.path.isdir(epub_path):
            process_directory_of_epubs(epub_path)
        else:
            print(f"ERROR: Provided filepath was NOT a folder.")
            print("If you are trying to parse a single file, remove the -d flag.")
            sys.exit(1)
    else: # Process the single file
        deck_name = args.deck_name
        deck_position = args.deck_position

        # If no deck name is specified, use the filename and let the user know
        if not deck_name:
            deck_name = os.path.basename(args.epub_path)
            deck_name = os.path.splitext(deck_name)[0]
            print(f"No name argument provided, defaulting to filename.")

        # If no deck position specified, default to end
        if not deck_position:
            decks = jpdb_list_user_decks(JPDB_API_KEY)
            deck_position = len(decks)

            print("---- SCRIPT START ----")
            print(f"Epub file: {epub_path}")
            print(f"Deck name: {deck_name}")
            print("----------------------")

            try:
                new_deck_data = create_new_deck_from_epub(deck_name, epub_path, deck_position)
                if new_deck_data:
                    print(f"Successfully created new deck: {deck_name} with ID: {new_deck_data[0]}")
                    print(f"Total unique words added: {new_deck_data[2]}")
                    print(f"Current user coverage of words: {new_deck_data[3]:.2f}%")
                else:
                    print("ERROR: Script failed to create new deck successfully!")

            except FileNotFoundError: 
                print(f"Error: File not found at {epub_path}")
            except zipfile.BadZipFile:
                print(f"Error: ZipFile could not read {epub_path}")
            except RuntimeError as e:
                print(f"A C++ runtime error ocurred: {e}")
    
    print("================ END OF SCRIPT ================")

