import json

import ahocorasick
from collections import defaultdict


def create_trie(phrases):
    """
    Build a Trie (Aho-Corasick Automaton) from the list of phrases.
    """
    automaton = ahocorasick.Automaton()
    for i, phrase in enumerate(phrases.keys()):
        automaton.add_word(phrase, phrase)
    automaton.make_automaton()
    return automaton


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


# Generate phrases for all blanks
def create_all_phrases(candidates, context):
    all_phrases = defaultdict(list)
    for i, (start_segment, end_segment) in enumerate(context):

        for candidate in candidates:
            phrase = f"{start_segment or ''} {candidate} {end_segment or ''}".strip().lower()
            all_phrases[phrase].append((i, candidate))

    return all_phrases


def create_phrases(candidates, input) -> tuple[dict[str, int], dict[int, dict[str, defaultdict[str, str]]]]:
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


def calculate_probability(blank_X_candidate, phrases):
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
    sorted_candidates = {}
    for idx, c in candidate_scores.items():
        sorted_candidates[idx] = sorted(c.items(), key=lambda x: x[1], reverse=True)

    output = [None]*len(candidates_list)

    # list of top words - select the one with most confidence:
    # if unassigned apply to blank, otherwise find next word for this blank with most confidence
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

    # TODO: delete, for testing
    for x in range(len(output)):
        print(f"#{x+1} {output[x]}")

    return output


def solve_cloze(input, candidates, corpus):
    print(f'starting to solve the cloze {input} with {candidates} using {corpus}')

    candidates_list = read_file(candidates)

    all_phrases, blank_X_candidate = create_phrases(candidates_list, input)

    automaton = create_trie(all_phrases)

    # Count occurrences in corpus
    with open(corpus, 'r', encoding='utf-8') as corpus_text:
        for i, corpus_line in enumerate(corpus_text):
            if i % 100000 == 0:  # TODO: delete, for testing
                print(i)
            corpus_line = corpus_line.strip().lower()
            # for phrase in all_phrases.keys():
            #     if phrase in corpus_line:
            #         all_phrases[phrase] += 1

            for idx, phrase in automaton.iter(corpus_line):
                all_phrases[phrase] += 1

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
