#include <pybind11/pybind11.h>
#include <string>
#include <mecab.h>
#include <stdexcept>

std::string tokenize_text(const std::string& text) {
    // Create MeCab tagger object
    // Owakati --> only output wakati-gaki (space separated)
    mecab_t* mecab = mecab_new2("-Owakati");

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

long long count_utf8_chars(const std::string& text) {
    long long count = 0;
    size_t i =0;
    const size_t len = text.length();

    while (i < len)
    {
        count++;

        unsigned char c = text[i];

        if (c < 0x80) { //0xxxxxxx
            i += 1;
        } else if ((c & 0xE0) == 0xC0) { //110xxxxx
            i += 2;
        } else if ((c & 0xF0) == 0xE0) { //1110xxxx
            i += 3;
        } else if ((c & 0xF8) == 0xF0) { //11110xxx
            i += 4;
        } else {
            i += 1;
        }
    }

    return count;
}

PYBIND11_MODULE(my_cpp_module, m)
{
    m.doc() = "A text analysis tool for Japanese ebooks";

    m.def(
        "tokenize_text",
        &tokenize_text,
        "Tokenizes our Japanese text into space separated words using MeCab"
    );
}