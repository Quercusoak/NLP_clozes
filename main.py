import random
import json
from collections import defaultdict


def generate_100_random_solutions(candidates):
    """Generates 100 random solutions for the given cloze and calculates mean accuracy"""
    candidates_list = read_file(candidates)
    random_solutions = [random.sample(candidates_list, len(candidates_list)) for _ in range(100)]
    accuracy = [0.0 for _ in range(100)]
    size = len(candidates_list)

    for i, solutions in enumerate(random_solutions):
        for blank, word in enumerate(solutions):
            if candidates_list[blank] == word:
                accuracy[i] += 1
        accuracy[i] /= size

    final_accuracy = sum(accuracy) / 100
    return final_accuracy


class TrieNode:
    """ Tree for the phrases created from N-grams"""
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.is_end_of_phrase = False
        self.count = 0


def build_trie(all_phrases):
    """ A tree of trigrams phrases words
    First word in phrase is a node whose children are the next word in phrase.
    That way phrases that begin similarly are checked once,
    and we look for the first word in the sentence before checking the others.
    """
    root = TrieNode()
    for phrase in all_phrases:
        node = root
        for word in phrase.split():
            node = node.children[word]
        node.is_end_of_phrase = True
    return root


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def create_phrases(candidates, input) -> tuple[dict[str, int], dict[int, dict[str, defaultdict[str, str]]]]:
    """
    Creates trigrams from sentence with a blank.
    Takes two words before and two after the blank and using all candidate words.
    If blank doesn't have two words before/after it, create bigrams.
    Returns all created phrases and a dictionary that contains the connection of trigram w1 w2 w3 to the bigram w1 w2
    and which blank and which candidate created this trigram.
    """
    input_text = read_file(input)
    phrases = {}
    idx = -1
    blank_str = "__________"
    blank_X_candidate = {blank: {word: defaultdict(str) for word in candidates} for blank in range(len(candidates))}

    for line in input_text:
        words = line.lower().split()
        for i, word in enumerate(words):
            if word == blank_str:
                idx = idx + 1

                # w1 w2 c
                if i > 1 and words[i - 2] != blank_str:
                    phrases[f"{words[i - 2]} {words[i - 1]}"] = 0
                    for c in candidates:
                        blank_X_candidate[idx][c][
                            f"{words[i - 2]} {words[i - 1]} {c}"] = f"{words[i - 2]} {words[i - 1]}"
                        phrases[f"{words[i - 2]} {words[i - 1]} {c}"] = 0

                # w1 c w2
                if 0 < i < len(words) - 1:
                    for c in candidates:
                        blank_X_candidate[idx][c][f"{words[i - 1]} {c} {words[i + 1]}"] = f"{words[i - 1]} {c}"
                        phrases[f"{words[i - 1]} {c} {words[i + 1]}"] = 0
                        phrases[f"{words[i - 1]} {c}"] = 0

                # <s> w1 c </s>
                if i == len(words) - 1 and i == 1:
                    phrases[words[i - 1]] = 0
                    for c in candidates:
                        blank_X_candidate[idx][c][f"{words[i - 1]} {c}"] = words[i - 1]
                        phrases[f"{words[i - 1]} {c}"] = 0

                # <s> c w1 </s>
                if i == 0 and (i + 1 < len(words) <= i + 2):
                    for c in candidates:
                        blank_X_candidate[idx][c][f"{c} {words[i + 1]}"] = c
                        phrases[c] = 0
                        phrases[f"{c} {words[i + 1]}"] = 0

                # c w1 w2
                if i + 2 < len(words) and words[i + 2] != blank_str:
                    for c in candidates:
                        blank_X_candidate[idx][c][f"{c} {words[i + 1]} {words[i + 2]}"] = f"{c} {words[i + 1]}"
                        phrases[f"{c} {words[i + 1]} {words[i + 2]}"] = 0
                        phrases[f"{c} {words[i + 1]}"] = 0

    return phrases, blank_X_candidate


def count_occurrences(corpus, all_phrases):
    """ Count occurrences in corpus using trie tree of all phrases created from trigrams"""
    root = build_trie(all_phrases)

    with open(corpus, 'r', encoding='utf-8') as corpus_text:
        for idx, corpus_line in enumerate(corpus_text):
            corpus_line = corpus_line.strip().lower().split()
            for i in range(len(corpus_line)):
                node = root
                for j in range(i, len(corpus_line)):
                    word = corpus_line[j]
                    if word not in node.children:
                        break
                    node = node.children[word]
                    if node.is_end_of_phrase:
                        phrase = ' '.join(corpus_line[i:j + 1])
                        all_phrases[phrase] += 1


def calculate_probability(blank_X_candidate, phrases):
    """
    For each blank-candidate pair, calculates probability of all trigrams of the pair.
    """
    num_blanks = len(blank_X_candidate.keys())
    candidate_scores = {blank: {} for blank in range(num_blanks)}
    k = 0.5
    vocab_size = pow(10, 7)
    for idx, candidate_phrases_dict in blank_X_candidate.items():
        for c, candidate_phrases in candidate_phrases_dict.items():
            score = None
            for trigram, pair in candidate_phrases.items():
                probability = ((phrases[trigram] + k) / (phrases[pair] + vocab_size))
                score = score * probability if score is not None else probability
            candidate_scores[idx][c] = score

    return candidate_scores


def assign_candidate_to_blank(candidate_scores, candidates_list):
    """
    Calculate for each blank the most probable solution - with the highest probability.
    Then from all those choose highest probability and assign to the blank.
    If that solution is already assigned to another blank, find the next highest unassigned solution.
    """
    sorted_candidates = {}
    for idx, c in candidate_scores.items():
        sorted_candidates[idx] = sorted(c.items(), key=lambda x: x[1], reverse=True)

    output = [None]*len(candidates_list)

    """ List of top words - select the one with most confidence:
        If unassigned apply to blank, otherwise find next word for this blank with most confidence"""
    max_list = {idx: sorted_candidates[idx][0] for idx in sorted_candidates.keys()}

    while len(candidates_list) > 0:
        max_idx, max_candidate = max(max_list.items(), key=lambda x: x[1][1])
        if max_candidate[0] in candidates_list:
            output[max_idx] = max_candidate[0]
            candidates_list.remove(max_candidate[0])
            max_list.pop(max_idx)
        else:
            while max_candidate[0] not in candidates_list:
                sorted_candidates[max_idx].remove(max_candidate)
                max_candidate = sorted_candidates[max_idx][0]
            max_list[max_idx] = max_candidate

    return output


def solve_cloze(input, candidates, corpus):
    """
    Build trie tree of all phrases (trigrams for each candidate for each blank, and the corresponding preceding bigram).
    For each corpus line if the first word of the phrase appears - check children, and this way look for whole phrase
    (is_end_of_phrase = True).
    Each occurrence is counted and then probability is calculated per blank per candidate.
    Last we assign candidate to blank by highest probability (if other blank has same candidate but lower probability,
    it'll get next probable candidate).
    """
    print(f'starting to solve the cloze {input} with {candidates} using {corpus}')
    # print(generate_100_random_solutions(candidates))
    candidates_list = read_file(candidates)
    all_phrases, blank_X_candidate = create_phrases(candidates_list, input)

    count_occurrences(corpus, all_phrases)

    candidate_scores = calculate_probability(blank_X_candidate, all_phrases)
    output = assign_candidate_to_blank(candidate_scores, candidates_list)

    return output


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as json_file:
        config = json.load(json_file)

    solution = solve_cloze(config['input_filename'],
                           config['candidates_filename'],
                           config['corpus'])

    print('cloze solution:', solution)
