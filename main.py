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
            automaton.add_word(phrase,  (candidate, blank))
    automaton.make_automaton()
    return automaton


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def read_input_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]


# Generate phrases for all blanks
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

def create_all_phrases(candidates, context):
    all_phrases = defaultdict(list)
    for i, (start_segment, end_segment) in enumerate(context):

        for candidate in candidates:
            phrase = f"{start_segment or ''} {candidate} {end_segment or ''}".strip().lower()
            all_phrases[phrase].append((i, candidate))

    return all_phrases


def solve_cloze(input, candidates, corpus):
    print(f'starting to solve the cloze {input} with {candidates} using {corpus}')

    output = list()
    candidates_list = read_file(candidates)

    # with open(input, 'r', encoding='utf-8') as corpus_text:
    # blanks = [m.start() for m in re.finditer(r"__________", input_text)]
    # score = {blank: [] for blank in blanks}

    context_segments = get_blank_context(input)
    all_phrases = create_all_phrases(candidates_list, context_segments)

    automaton = create_trie(all_phrases)

    with open(corpus, 'r', encoding='utf-8') as corpus_text:
        corpus_lines = [line.strip().lower() for line in corpus_text]

    # Count occurrences in corpus
    candidate_scores = defaultdict(lambda: defaultdict(int))
    for corpus_line in corpus_lines:
        # for phrase, blanks_and_candidates in all_phrases.items():
        #     if phrase in corpus_line:
        #         for blank_index, candidate in blanks_and_candidates:
        #             candidate_scores[blank_index][candidate] += 1

        for end_index, (candidate, blank_index) in automaton.iter(corpus_line):
            candidate_scores[blank_index][candidate] += 1

    # output = [
    #     max(scores, key=scores.get)  # Find candidate with max score for each blank
    #     for _, scores in sorted(candidate_scores.items())
    # ]

    for blank_index in sorted(candidate_scores.keys()):
        best_candidate = max(candidate_scores[blank_index], key=candidate_scores[blank_index].get)
        output.append(best_candidate)

    # # Select best candidates
    # for blank_index in range(len(context_segments)):
    #     best_candidate = max(
    #         candidate_scores[blank_index],
    #         key=lambda x: candidate_scores[blank_index][x],
    #         default=None
    #     )
    #     if best_candidate:
    #         # Extract the candidate word from the phrase
    #         candidate_word = best_candidate.split()[1]  # Assume the candidate is the middle word
    #         output.append(candidate_word)





    # with open(corpus, 'r', encoding='utf-8') as corpus_text:
    #     for start_segment, end_segment in context_segments:
    #         scores = defaultdict(int)
    #         for candidate in candidates_list:
    #             phrase = start_segment + ' ' + candidate + ' ' + end_segment  # Replace blank with candidate
    #             corpus_text.seek(0)
    #             scores[candidate] = sum(1 for line in corpus_text.readlines() if phrase.lower() in line.lower())
    #
    #         best_candidate = max(scores, key=scores.get)
    #         output.append(best_candidate)





        # blanks = [m.start() for m in re.finditer(r"__________", line)]
        # for i, blank_pos in enumerate(blanks):
        #     candidate_scores = defaultdict(int)
        #
        #     # Context before the blank (from start to the blank)
        #     start_segment = line[:blank_pos]
        #
        #     # Context after the blank (from the blank to the next blank or end of line)
        #     if i + 1 < len(blanks):
        #         end_segment = line[blank_pos + blank_len:blanks[i + 1]]
        #     else:
        #         end_segment = line[blank_pos + blank_len:]  # If it's the last blank, take the rest of the line
        #
        #     for candidate in candidates_list:
        #         phrase = start_segment + candidate + end_segment  # Replace blank with candidate
        #         candidate_scores[candidate] = sum(1 for line in corpus_text if phrase.lower() in line.lower())
        #
        #     # Sort candidates by occurrences and pick the one with the highest score
        #     best_candidate = max(candidate_scores, key=candidate_scores.get)
        #     output.append(best_candidate)

    #     for blank in blanks:
    #         candidate_scores = defaultdict(int)
    #
    #         # Replace the blank with each candidate and check corpus frequency
    #         for candidate in candidates_list:
    #             phrase = line[:blank] + candidate + line[blank + len("__________"):]  # Replace blank with candidate
    #             candidate_scores[candidate] = sum(1 for line in corpus_text if phrase.lower() in line.lower())
    #
    #         # Sort candidates by occurrences and pick the one with the highest score
    #         best_candidate = max(candidate_scores, key=candidate_scores.get)
    #         output.append(best_candidate)
    #
    # # Replace each blank with candidate and count number of occurrences in corpus
    # # for blank in blanks:
    # #     for candidate in candidates_list:
    # #         sentence = input_text[:blank] + candidate + input_text[blank + len("__________"):]
    # #         occurrences = corpus_text.lower().count(sentence.lower())
    # #         score[blank].append((candidate, occurrences))
    # #
    # # for blank_pos, scores in score.items():
    # #     # Sort the candidates for the blank by score in descending order
    # #     scores.sort(key=lambda x: x[1], reverse=True)
    # #
    # #     # Find the highest-scoring candidate that hasn't been used
    # #     for candidate, score in scores:
    # #         if candidate not in output:
    # #             output.append(candidate)
    # #             break

    return output


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as json_file:
        config = json.load(json_file)

    solution = solve_cloze(config['input_filename'],
                           config['candidates_filename'],
                           config['corpus'])

    print('cloze solution:', solution)
