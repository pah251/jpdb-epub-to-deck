import os
import sys
import zipfile
from html.parser import HTMLParser

# ---- Find required mingw binaries, load c++ module ----
#--------------------------------------------------------
MINGW_BIN_PATH = os.environ.get("MINGW_BIN_PATH")
MECAB_ROOT = os.environ.get("MECAB_ROOT")

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
    import my_cpp_module
    print("Successfully imported C++ module.")
except ImportError as e:
    print(f"Error importing C++ module: {e}")
    print("Did you forget to cmake and build in the build directory?")
    sys.exit(1)
#--------------------------------------------------------

class EpubTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return "".join(self.text_parts)



def get_text_from_epub(epub_path):
    """
    Function to open an epub file, find all .xhtml content, and return as a single string
    """

    parser = EpubTextExtractor()

    with zipfile.ZipFile(epub_path, 'r') as epub:
        for item in epub.infolist():
            if item.filename.endswith(('.html', '.xhtml')):
                with epub.open(item) as file_content:
                    html_bytes = file_content.read()
                    parser.feed(html_bytes.decode('utf-8'))

    return parser.get_text()

if __name__ == "__main__":
    #TODO: read file location from command line, input argument
    epub_file_to_test = "konbini.epub"

    print(f"\nAttempting to read epub: {epub_file_to_test}")
    try:
        book_text = get_text_from_epub(epub_file_to_test)
        print(f"successfully read {len(book_text)} characters")

        word_counts = my_cpp_module.unique_word_count(book_text)
        sorted_words = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)

        for word, count in sorted_words[:50]:
            print(f"{word.ljust(50)} : {count}")

    except FileNotFoundError: 
        print(f"Error: File not found at {epub_file_to_test}")
    except zipfile.BadZipFile:
        print(f"Error: ZipFile could not read {epub_file_to_test}")
