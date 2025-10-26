Japanese EPUB to JPDB Deck Creator

C++/Python tool to extract useful Japanese vocabulary from .epub files and automatically create new decks for each parsed file.
Python: file handling, API calls
C++: high-speed text analysis using MeCab library

Requirements:
C++
Install these and add the bin folders to PATH 
- C++17 Compliler: this project was built using MinGW-w64(g++) on windows.
- CMake (v3.15+): C++ build tool
- MeCab (64-bit): https://github.com/ikegami-yukino/mecab/releases (!!select UTF-8 when installing!!)
  
Python
Required packages that can be installed via pip
- requests: for calling the jpdb.io api
- python-dotenv: loading environment variables easily
- pybind11: included as git submodule, no need for installation

Setup and installation:
1. Clone the repository
You will need to clone recursively to download the pybind11 module

git clone --recursive https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

2. Create your environment file
We use a handy-dandy .env file to handle secret keys and paths.
Create a file called ".env" in the base folder of the project, include the following:

MINGW_BIN_PATH=C:/path/to/mingw64/bin

MECAB_ROOT=C:/Program Files/MeCab

JPDB_API_KEY=YOUR_SECRET_API_KEY_GOES_HERE

3. Build c++ module
# 1. Create a build directory
mkdir build
cd build

# 2. Run CMake to generate the Makefile
# We must pass the path to MeCab directly to CMake.
# (Update this path if yours is different)
cmake -G "MinGW Makefiles" -DMECAB_ROOT="C:/Program Files/MeCab" ..

# 3. Run make to compile the C++ code
# (You may need to use 'mingw32-make' depending on your MinGW version)
mingw32-make

Usage
Arguments:
1. File/Folder path: path to the singular file or folder to parse
2. -d --dir: optional flag but must be included if you are parsing a directory
3. --deck-name: optional specific name of the deck. Defaults to the name of the epub.
4. --deck-position: optional specific position in your deck list to add the new deck to. Defaults to append to the end of your deck list.

Example usage
$ python jpdb_epub_deck.py "C:\Study\ebooks\住野よる" -d
Process every epub within the "/住野よる" folder

$ python jpdb_epub_deck.py "C:\Study\ebooks\住野よる\君の膵臓をたべたい.epub"
Process only 君の膵臓をたべたい.epub. Create a new deck called "君の膵臓をたべたい" and append it to the end of your deck list.

$ python jpdb_epub_deck.py "C:\Study\ebooks\住野よる\君の膵臓をたべたい.epub" --deck-name="I want to eat your pancreas"
Process only 君の膵臓をたべたい.epub. Create a new deck called "I want to eat your pancreas" and append it to the end of your deck list.

$ python jpdb_epub_deck.py "C:\Study\ebooks\住野よる\君の膵臓をたべたい.epub" --deck-name="I want to eat your pancreas" -0
Process only 君の膵臓をたべたい.epub. Create a new deck called "I want to eat your pancreas" and add it to the start of your deck list.
