#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <mecab.h>
#include <stdexcept>
#include <map>
#include <vector>


std::string tokenize_text(const std::string& text) {
    // Create MeCab tagger object
    // Owakati --> only output wakati-gaki (space separated)
    mecab_t* mecab = mecab_new2("");

    // check initialisation was successful
    if (!mecab) {
        throw std::runtime_error("Could not create MeCab tagger. Is MeCab installed correctly?");
    }

    // parse the text
    const char* result = mecab_sparse_tostr(mecab, text.c_str());

    // if unable to parse -> throw error
    if (!result) {
        const char* error = mecab_strerror(mecab);
        std::string error_message = "MeCab prasing failed: ";
        if (error) {
            error_message += error;
        }
        mecab_destroy(mecab);
        throw std::runtime_error(error_message);
    }

    // turn C-style string into C++
    std::string output = result;

    // clean-up
    mecab_destroy(mecab);

    return output;
}

std::vector<std::string> split_by_delimeter(const std::string& line, char delim) {
    std::stringstream string_stream(line);
    std::vector<std::string> words;
    std::string curr_word;
    while (std::getline(string_stream, curr_word, delim)) {
        words.push_back(curr_word);
    }
    return words;
}

std::map<std::string, int> unique_word_count(const std::string& text) {
    // parse the data using mecab function
    std::stringstream ss(tokenize_text(text));

    // create the map
    std::map<std::string, int> word_counts;

    std::string line;

    while (std::getline(ss, line))
    {
        // skip EOF line
        if (line == "EOF") {
            continue;
        }
        
        // output from MeCab is of format:
        // <word><tab><information>
        // we can easily grab the word by substring from start of line -> tab
        size_t tab_pos = line.find('\t');
        if (tab_pos == std::string::npos) { // skip cases when not found
            continue;
        }

        // extract the word
        std::string surface_word = line.substr(0, tab_pos);
        // extract the information into a vector
        std::string word_information = line.substr(tab_pos + 1);
        std::vector<std::string> word_information_parts = split_by_delimeter(word_information, ',');
        if (word_information_parts.size() < 7) { // the base word is held in [6] --> skip all malformed
            continue;
        }
        
        const std::string& word_classification = word_information_parts[0];
        const std::string& word_subtype = word_information_parts[1];
        // only count Nouns, Verbs, Adjectives and Adverbs!
        // (名詞、動詞、形容詞、副詞)
        // filter out suffixes, prefixes, we're only interested in useful vocab
        if (word_classification == "名詞" || 
        word_classification == "動詞" ||
        word_classification == "形容詞" ||
        word_classification == "副詞" ) {
            // filter unuseful types
            if (word_subtype == "非自立" || // "non-independent" (e.g., いる, し)
            word_subtype == "接尾" ||   // "suffix" (e.g., さん, 的)
            word_subtype == "代名詞" || // "pronoun" (e.g., 私, これ)
            word_subtype == "数") {
                continue;
            }
            const std::string& base_word = word_information_parts[6]; // already checked for array lengths
            if (base_word == "*") {
                word_counts[surface_word]++;
            } else {
                word_counts[base_word]++;
            }
        }
        
    }

    return word_counts;
}

PYBIND11_MODULE(jp_epub_parser, m)
{
    m.doc() = "A text parser tool for Japanese ebooks";

    m.def(
        "unique_word_count",
        &unique_word_count,
        "Returns a dictionary of all unique words and their count."
    );
}