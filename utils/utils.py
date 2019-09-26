import string
import nltk
from nltk import bigrams, trigrams, ngrams, word_tokenize, FreqDist
from nltk.tokenize import RegexpTokenizer

import pdb

stop_words = [
    ' ',
    'this address you'
]

# take second element for sort
def take_second(elem):
    return elem[1]


def get_str_top_three(ngram_list):
    res = []
    idx = 0
    for tuple_word, word_count in ngram_list:
        words = ' '.join(tuple_word)
        if idx < 3:
            for stop_word in stop_words:
                if stop_word != words and words != ' ':
                    res_text.append({
                        'text': words,
                        'count': word_count
                    })
                    idx = idx + 1
        else:
            break

    return res

def get_top_ngrams(content):
    text = content.translate(str.maketrans('', '', string.punctuation + string.digits))
    tokens = nltk.word_tokenize(text)
    tokens = [token.lower() for token in tokens if len(token) > 1] #same as unigrams
    uni_tokens = list(ngrams(text, 1))
    fdist = FreqDist(uni_tokens)
    bi_tokens = list(bigrams(tokens))
    tri_tokens = list(trigrams(tokens))

    # get counts
    uni_words = [(item, fdist[item]) for item in fdist]
    uni_words.sort(key=take_second, reverse=True)

    tri_words = [(item, tri_tokens.count(item)) for item in set(tri_tokens)]
    tri_words.sort(key=take_second, reverse=True)

    bi_words = [(item, tri_tokens.count(item)) for item in set(bi_tokens)]
    bi_words.sort(key=take_second, reverse=True)

    top_uni_words = get_str_top_three(uni_words)
    top_bi_words = get_str_top_three(bi_words)
    top_tri_words = get_str_top_three(tri_words)

    return (top_uni_words, top_bi_words, top_tri_words)

def get_word_count(text):
    if text is None:
        return 0
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(text)
    if tokens is None:
        return 0
    return len(set(tokens))