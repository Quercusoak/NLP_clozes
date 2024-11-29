import json
import math

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
                # probability = math.log(probability)
                score = score * probability if score is not None else probability
            candidate_scores[idx][c] = score

    return candidate_scores


def assign_candidate_to_blank(candidate_scores, candidates_list):
    sorted_candidates = {}
    # for idx, c in candidate_scores.items():
    #     # print(f"#{idx + 1}: {c}")
    #     sorted_candidates[idx] = sorted(c.items(), key=lambda x: x[1], reverse=True)

    output = [None]*len(candidates_list)

    # if there is only one option that solves the cloze, choose it
    for blank, word_scores in candidate_scores.items():
        average = sum(word_scores.values()) / len(word_scores)
        possible_solution = list(filter(lambda x: x[1] > average, word_scores.items()))
        if len(possible_solution) == 1 and possible_solution[0][0] in candidates_list:
            only_choice = possible_solution[0][0]
            output[blank] = only_choice
            candidates_list.remove(only_choice)
        else:
            sorted_candidates[blank] = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)

    # list of top words - select max :
    # if unassigned : apply to blank; remove from list of unassigned
    # else : sorted_candidates.remove; add next max unassigned (without assigning immediately)
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

    # TODO: delete, for testing
    candidate_scores = {
        0: {'notation': 3.3749905500200813e-21, 'system': 5.3746495720041386e-21, 'remote': 1.2499997500000374e-22,
            'open': 1.2499957500140373e-22, 'technologies': 1.6249762753440237e-21, 'faster': 1.2499996250000873e-22,
            'commonly': 1.2499991250005374e-22, 'browsers': 3.7499962500034124e-22, 'displayed': 3.7499955000049876e-22,
            'people': 3.858336083282568e-20, 'half': 1.1249681633978034e-21, 'methods': 3.124830009080359e-21},
        1: {'notation': 1.2499910000622121e-22, 'system': 1.874132088822822e-21, 'remote': 1.2499955000149624e-22,
            'open': 1.2499900000771119e-22, 'technologies': 1.249943252559422e-22, 'faster': 1.2499987500009876e-22,
            'commonly': 1.2499993750002375e-22, 'browsers': 1.2499955000149624e-22, 'displayed': 1.2499972500053375e-22,
            'people': 1.2497133156794904e-22, 'half': 1.2499480021476237e-22, 'methods': 3.7497491417074996e-22},
        2: {'notation': 1.2499240046129326e-22, 'system': 1.249913380333763e-22, 'remote': 1.8109698326168567e-19,
            'open': 6.124175658484969e-21, 'technologies': 1.249923879620557e-22, 'faster': 1.249924129605333e-22,
            'commonly': 1.249924129605333e-22, 'browsers': 1.249924129605333e-22, 'displayed': 1.2499240046129326e-22,
            'people': 3.749763389383002e-22, 'half': 1.2499240046129326e-22, 'methods': 3.7497720138387974e-22},
        3: {'notation': 1.2456736504121313e-22, 'system': 1.1584526307181494e-20, 'remote': 3.8648549743003217e-19,
            'open': 1.0259646195632281e-17, 'technologies': 1.2456721556054199e-22, 'faster': 3.7370187090253916e-22,
            'commonly': 6.6000751446675815e-21, 'browsers': 1.2456736504121313e-22, 'displayed': 1.2456729030083894e-22,
            'people': 8.717956269309773e-22, 'half': 1.245670660802844e-22, 'methods': 1.245672280172623e-22},
        4: {'notation': 1.2494061572534574e-22, 'system': 1.2493966618298943e-22, 'remote': 1.2494061572534574e-22,
            'open': 1.2494057824316978e-22, 'technologies': 3.3733925765121635e-21, 'faster': 1.2494061572534574e-22,
            'commonly': 1.2494061572534574e-22, 'browsers': 1.2494061572534574e-22, 'displayed': 1.2494061572534574e-22,
            'people': 1.2494046579677305e-22, 'half': 1.2494022841063764e-22, 'methods': 1.2494057824316976e-22},
        5: {'notation': 1.249967500641551e-22, 'system': 1.2495999971411785e-22, 'remote': 6.249438793199205e-22,
            'open': 1.248285203827955e-22, 'technologies': 1.2499048810645153e-22, 'faster': 5.6245927744905695e-21,
            'commonly': 1.2499238787562124e-22, 'browsers': 1.2499782503416323e-22, 'displayed': 1.2498987569317289e-22,
            'people': 1.249246068611964e-22, 'half': 1.2495740139161796e-22, 'methods': 1.249838893569777e-22},
        6: {'notation': 1.246938751614481e-22, 'system': 1.3714535127679592e-21, 'remote': 2.1820917546080572e-20,
            'open': 1.40889820943745e-20, 'technologies': 1.2469300231293324e-22, 'faster': 1.2469434899784204e-22,
            'commonly': 2.240192570591928e-17, 'browsers': 1.2469439887556417e-22, 'displayed': 1.2469436146726945e-22,
            'people': 1.0845843245200685e-20, 'half': 1.2469403726274886e-22, 'methods': 1.2468590775856514e-22},
        7: {'notation': 6.24987562745039e-22, 'system': 2.010817546774383e-20, 'remote': 3.749848881060019e-22,
            'open': 1.1246429255860519e-21, 'technologies': 1.5622970562481015e-20, 'faster': 1.2498855104529834e-22,
            'commonly': 1.2499938750288374e-22, 'browsers': 2.418643337242258e-19, 'displayed': 1.2499830002278468e-22,
            'people': 2.5846819207383065e-20, 'half': 6.249123872658077e-22, 'methods': 3.1244732136583607e-21},
        8: {'notation': 2.8749462385053394e-21, 'system': 1.3572644700365192e-19, 'remote': 1.374976900374709e-21,
            'open': 4.735335888403443e-20, 'technologies': 1.537349954629439e-20, 'faster': 4.124914201750944e-21,
            'commonly': 1.8123294597638006e-20, 'browsers': 1.2499957500132874e-22, 'displayed': 1.1753136587631615e-18,
            'people': 1.2899261488678832e-17, 'half': 2.5621899733855888e-20, 'methods': 2.1621959951823627e-20},
        9: {'notation': 1.249748925340669e-22, 'system': 1.2497364279752021e-22, 'remote': 1.249749175290404e-22,
            'open': 6.248722756180075e-22, 'technologies': 1.2497484254414988e-22, 'faster': 1.2497493002653093e-22,
            'commonly': 1.2497474256443582e-22, 'browsers': 1.2497494252402392e-22, 'displayed': 1.2497494252402392e-22,
            'people': 4.660716332848761e-19, 'half': 1.2497478005675987e-22, 'methods': 1.2497480505173838e-22},
        10: {'notation': 6.210269491227458e-22, 'system': 5.579591901263283e-21, 'remote': 3.7262939729739805e-22,
             'open': 1.117872318157727e-21, 'technologies': 1.242067560451732e-22, 'faster': 1.1178903158750526e-21,
             'commonly': 3.7262861477946087e-22, 'browsers': 1.2421012204422282e-22,
             'displayed': 1.2421010962322677e-22, 'people': 7.37697953126831e-20, 'half': 1.714653275790984e-14,
             'methods': 6.207303137314865e-22},
        11: {'notation': 1.2499535016978007e-22, 'system': 1.2492855299200569e-22, 'remote': 1.2499888750918368e-22,
             'open': 1.2496214893865199e-22, 'technologies': 1.1249401531190686e-21, 'faster': 1.2499917500492871e-22,
             'commonly': 1.2499887500939868e-22, 'browsers': 1.2499980000024125e-22,
             'displayed': 1.2499806252873583e-22, 'people': 1.2497752902461294e-22, 'half': 1.249920754969276e-22,
             'methods': 8.748318565920058e-22}}
    output = assign_candidate_to_blank(candidate_scores, candidates_list)

    all_phrases, blank_X_candidate = create_phrases(candidates_list, input)

    automaton = create_trie(all_phrases)

    # Count occurrences in corpus
    with open(corpus, 'r', encoding='utf-8') as corpus_text:
        for i, corpus_line in enumerate(corpus_text):
            if i % 100000 == 0:  # TODO: delete, for testing
                print(i)
            corpus_line = corpus_line.strip().lower()
            # for phrase in all_phrases.items():
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
