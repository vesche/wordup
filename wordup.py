#!/usr/bin/env python

import bs4
import json
import argparse
import requests

from collections import Counter

url = 'https://api.yourdictionary.com/wordfinder/v1/unscrambler?tiles={letters}&offset=0&limit=10&order_by=score&group_by=word_length&dictionary=WWF&bonus=true&dictionary_opt=YDR&check_exact_match=true&exclude_original=true&original_tiles={letters}'
uas = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:72.0) Gecko/20100101 Firefox/72.0'
letter_values = {
    'a':  1, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 3, 'h':  3, 'i': 1,
    'j': 10, 'k': 5, 'l': 2, 'm': 4, 'n': 2, 'o': 1, 'p': 3, 'q': 10, 'r': 1,
    's':  1, 't': 1, 'u': 2, 'v': 6, 'w': 4, 'x': 8, 'y': 4, 'z': 10
}


def get_words(letters):
    r = requests.get(url.format(letters=letters) + letters, headers={'User-Agent': uas})
    response = r.json()

    words = list()
    for group in response['data']['_groups']:
        for item in group['_items']:
            words.append(item['word'])

    return words


def score_word(word, values):
    _values = values[:]
    flat_score = 0
    total_wordscore = 1

    for letter in word:
        select_value = {}
        for v in _values:
            if v['letter'] == letter:
                # shitty priority-based python switch statement :)
                if not select_value:
                    select_value = v
                    continue
                if v['wordscore'] > select_value['wordscore']:
                    select_value = v
                    continue
                if v['wordscore'] == 1 and v['value'] > select_value['value']:
                    select_value = v
                    continue

        # pop value
        _values.remove(select_value)
        flat_score += select_value['value']
        total_wordscore *= select_value['wordscore']

    return flat_score * total_wordscore, _values


def get_parser():
    parser = argparse.ArgumentParser(description='wordup')
    parser.add_argument('-l', nargs='+', type=str)
    parser.add_argument('-w', nargs='+', type=str)
    return parser


def main():
    parser = get_parser()
    args = vars(parser.parse_args())

    values = [] # [{'letter': 'l', 'value': 1, 'wordscore': 1}, ...]
    for arg in args['l']:
        multiply, letters = int(arg[0]), arg[1:]
        for letter in letters:
            values.append({
                'letter': letter,
                'value': letter_values[letter] * multiply,
                'wordscore': 1,
            })
    if args['w']:
        for arg in args['w']:
            wordscore, letters = int(arg[0]), arg[1:]
            for letter in letters:
                values.append({
                    'letter': letter,
                    'value': letter_values[letter],
                    'wordscore': wordscore,
                })

    all_letters = ''.join([v['letter'] for v in values])
    wordscore_letters = ''.join([v['letter'] for v in values if v['wordscore'] > 1])
    wordscore_counts = Counter(wordscore_letters)

    # get all words from wordfinder website
    words = get_words(all_letters)

    top_words = []
    for word in words:
        word_counts = Counter(word)
        if all(word_counts[letter] >= count for letter, count in wordscore_counts.items()):
            top_words.append(word)
        if len(top_words) == 20: # top 20
            break

    scores = [] # [{'first': 'word1', 'second': 'word2', 'score': 0}, ...]
    for word in top_words:
        first_word_score, new_values = score_word(word, values)

        letters_leftover = str(all_letters)
        for c in word:
            letters_leftover = letters_leftover.replace(c, '', 1)

        secondary_words = get_words(letters_leftover)[:5] # top 5 (secondary)
        for word2 in secondary_words:
            second_word_score, _ = score_word(word2, new_values)
            scores.append({
                'first': word,
                'second': word2,
                'score': first_word_score + second_word_score
            })

    top_20_sorted_scores = sorted(scores, key=lambda x:x['score'], reverse=True)[:20]
    for i in top_20_sorted_scores:
        print('{0:>4} - {1}, {2}'.format(i['score'], i['first'], i['second']))


if __name__ == '__main__':
    main()
