import json
import pickle
import os.path
from collections import defaultdict

import numpy as np
from matplotlib import pyplot as plt
from math import log
import seaborn as sn
from scipy.optimize import curve_fit

sn.set()


def read_data(filename):
    word2freq = defaultdict(int)
    unique_words_per_vocabulary_size = defaultdict(int)

    i = 0
    with open(filename, 'r', encoding='utf-8') as fin:
        print('reading the text file...')
        for i, line in enumerate(fin):
            for word in line.split():
                word2freq[word] += 1
            if i % 100000 == 0:
                print(i)
                unique_words_per_vocabulary_size[i] = len(word2freq)

    total_words = sum(word2freq.values())
    word2nfreq = {w: word2freq[w]/total_words for w in word2freq}

    return word2nfreq, unique_words_per_vocabulary_size


def plot_zipf_law(word2nfreq):
    y = sorted(word2nfreq.values(), reverse=True)
    x = list(range(1, len(y)+1))

    product = [a * b for a, b in zip(x, y)]
    print(product[:1000])

    y = [log(e, 2) for e in y]
    x = [log(e, 2) for e in x]

    plt.plot(x, y)
    plt.xlabel('log(rank)')
    plt.ylabel('log(frequency)')
    plt.title("Zipf's law")
    plt.show()


def heaps_function(N, k, beta):
    return k * N**beta

def plot_heap_law(tokens_per_types : defaultdict[int]):
    total_words = np.array(list(tokens_per_types.keys()))
    unique_words = np.array(list(tokens_per_types.values()))

    popt, _ = curve_fit(heaps_function, total_words, unique_words)
    k, beta = tuple(popt)

    plt.plot(total_words, unique_words, label='Empirical Data', color='blue', alpha=0.7)
    plt.plot(total_words, k * np.power(total_words, beta), '--',
             label=f"Heaps' Law Fit: K={k:.2f}, β={beta:.3f}", color='red', linewidth=2)

    plt.legend()

    plt.xlabel('vocabulary size')
    plt.ylabel('unique words')
    plt.title("Heap's law")
    plt.show()


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as json_file:
        config = json.load(json_file)

    if not os.path.isfile('word2nfreq.pkl'):
        data, tokens_per_types = read_data(config['corpus'])
        pickle.dump(data, open('word2nfreq.pkl', 'wb'))
        pickle.dump(tokens_per_types, open('tokens_per_types.pkl', 'wb'))

    # plot_zipf_law(pickle.load(open('word2nfreq.pkl', 'rb')))


    plot_heap_law(pickle.load(open('tokens_per_types.pkl', 'rb')))
