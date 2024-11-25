import json
import ahocorasick
from collections import defaultdict


def create_trie(phrases):
    """
    Build a Trie (Aho-Corasick Automaton) from the list of phrases.
    """
    automaton = ahocorasick.Automaton()
    for phrase, info in phrases.items():
        for (blank, candidate) in info:
            automaton.add_word(phrase, (candidate, blank))
    automaton.make_automaton()
    return automaton


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def read_input_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]


# create context for trigrams- left word and right word
def get_blank_context(input):
    input_text = read_file(input)
    context_segments = []

    for line in input_text:
        words = line.split()

        for i, word in enumerate(words):
            if word == "__________":
                word_before = words[i - 1] if i > 0 else None
                word_after = words[i + 1] if i + 1 < len(words) else None
                context_segments.append((word_before, word_after))

    return context_segments


# Generate phrases for all blanks
def create_all_phrases(candidates, context):
    all_phrases = defaultdict(list)
    for i, (start_segment, end_segment) in enumerate(context):

        for candidate in candidates:
            phrase = f"{start_segment or ''} {candidate} {end_segment or ''}".strip().lower()
            all_phrases[phrase].append((i, candidate))

    return all_phrases


def solve_cloze(input, candidates, corpus):
    print(f'starting to solve the cloze {input} with {candidates} using {corpus}')

    candidates_list = read_file(candidates)
    output = [None] * len(candidates_list)
    NO_VALUE = -1  # for blanks with no probability that should be saved for last

    context_segments = get_blank_context(input)
    all_phrases = create_all_phrases(candidates_list, context_segments)

    # automaton = create_trie(all_phrases)
    candidate_scores = {blank: {word: 0 for word in candidates_list} for blank in range(len(candidates_list))}

   # TODO: delete, for testing
    for phrase in context_segments:
        print(f"{phrase[0]} __________ {phrase[1]}")

    # Count occurrences in corpus
    with open(corpus, 'r', encoding='utf-8') as corpus_text:
        for i, corpus_line in enumerate(corpus_text):
            if i % 100000 == 0:  # TODO: delete, for testing
                print(i)
            corpus_line = corpus_line.strip().lower()
            for phrase, blanks_and_candidates in all_phrases.items():
                if phrase in corpus_line:
                    for blank_index, candidate in blanks_and_candidates:
                        candidate_scores[blank_index][candidate] += 1

            # for end_index, (candidate, blank_index) in automaton.iter(corpus_line):
            #     candidate_scores[blank_index][candidate] += 1

    # TODO: delete, for testing
    for blank, word_scores in candidate_scores.items():
        print(f"#{blank + 1}: {context_segments[blank][0]} __ {context_segments[blank][1]}: {word_scores}")

    # if there is only one option that solves the cloze, choose it
    for blank, word_scores in candidate_scores.items():
        possible_solutions = list(filter(lambda x: word_scores[x] > 0, word_scores))
        if len(possible_solutions) == 1:
            only_choice = possible_solutions[0]
            if only_choice in candidates_list:
                output[blank] = only_choice
                candidates_list.remove(only_choice)
        if len(possible_solutions) == 0:
            output[blank] = NO_VALUE

    # TODO: delete, for testing
    print(output)

    # choose rest of words now that obvious solutions selected
    for blank, word_scores in candidate_scores.items():
        if output[blank] is None:
            blank_candidates = {(word, score) for word, score in word_scores.items() if word in candidates_list}
            blank_solution = max((word for word in word_scores if word in candidates_list), key= lambda x: word_scores[x])
            output[blank] = blank_solution
            candidates_list.remove(blank_solution)

    # finally guess words that have no occurrences in corpus
    no_solution = [blank_index for blank_index, value in enumerate(output) if value == NO_VALUE]
    i=0
    for blank in no_solution:
        output[blank]=candidates_list[i]
        i=i+1

    return output


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as json_file:
        config = json.load(json_file)

    solution = solve_cloze(config['input_filename'],
                           config['candidates_filename'],
                           config['corpus'])

    print('cloze solution:', solution)
