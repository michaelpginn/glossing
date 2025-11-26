"""Contains the evaluation scripts for comparing predicted and gold IGT"""

from typing import List

from glossing.bleu import bleu_score

from .igt import IGT, gloss_string_to_morpheme_glosses, gloss_string_to_word_glosses


def evaluate_glosses(predicted_glosses: List[str], gold_glosses: List[str]):
    """Runs evaluation over paired lists of glosses.

    Expects all glosses to be in the string format such as

    ```text
    DET.PL cat-PL run-3PL
    ```

    where words are separated with spaces and morphemes are separated with dashes '-' or equals '='

    Returns the following metrics at both the morpheme and word level:
        - `accuracy`: the micro (over whole corpus) and macro (averaged over sentences) accuracy, skipping [SEP] tokens
        - `bleu`: the blue score (max 4-grams), where words/morphemes are atomic units for n-grams
        - `error_rate`: the error rate under levenshtein distance, computed at the word/morpheme/character level, skipping [SEP] tokens
        - `classes` (morphemes only): the precision, recall, and f1 for stem and gram morphemes
    """
    if len(predicted_glosses) != len(gold_glosses):
        raise ValueError(
            f"Length mismatch, got {len(predicted_glosses)} predicted rows and {len(gold_glosses)} gold rows."
        )

    pred_word_glosses = [gloss_string_to_word_glosses(s) for s in predicted_glosses]
    gold_word_glosses = [gloss_string_to_word_glosses(s) for s in gold_glosses]

    pred_morphemes = [gloss_string_to_morpheme_glosses(s) for s in predicted_glosses]
    gold_morphemes = [gloss_string_to_morpheme_glosses(s) for s in gold_glosses]

    return {
        "words": {
            "accuracy": _accuracy(pred_word_glosses, gold_word_glosses),
            "bleu": bleu_score(
                pred_word_glosses, [[line] for line in gold_word_glosses]
            ),
            "error_rate": _error_rate(pred_word_glosses, gold_word_glosses),
        },
        "morphemes": {
            "accuracy": _accuracy(pred_morphemes, gold_morphemes),
            "classes": _f1_stems_grams(pred_morphemes, gold_morphemes),
            "bleu": bleu_score(pred_morphemes, [[line] for line in gold_morphemes]),
            "error_rate": _error_rate(pred_morphemes, gold_morphemes),
        },
        "characters": {
            "error_rate": _error_rate(
                [list(s) for s in predicted_glosses],
                [list(s) for s in gold_glosses],
            ),
        },
    }


def _accuracy(pred: List[List[str]], gold: List[List[str]]) -> dict:
    """Computes the average and overall accuracy, where predicted labels must be in the correct position in the list."""
    total_correct_predictions = 0
    total_tokens = 0
    summed_accuracies = 0

    for entry_pred, entry_gold, i in zip(pred, gold, range(len(gold))):
        entry_correct_predictions = 0

        entry_gold_len = len([token for token in entry_gold if token != IGT.SEP_TOKEN])
        if entry_gold_len == 0:
            raise ValueError(f"Found empty gold entry at position {i}:", entry_gold)

        for token_index in range(len(entry_gold)):
            # For each token, check if it matches
            if (
                token_index < len(entry_pred)
                and entry_pred[token_index] == entry_gold[token_index]
                and entry_gold[token_index] not in [IGT.UNK_TOKEN, IGT.SEP_TOKEN]
            ):
                entry_correct_predictions += 1

        entry_accuracy = entry_correct_predictions / entry_gold_len
        summed_accuracies += entry_accuracy

        total_correct_predictions += entry_correct_predictions
        total_tokens += entry_gold_len

    total_entries = len(gold)
    average_accuracy = summed_accuracies / total_entries
    overall_accuracy = total_correct_predictions / total_tokens
    return {"macro": average_accuracy, "micro": overall_accuracy}


def _f1_stems_grams(pred: List[List[str]], gold: List[List[str]]) -> dict:
    perf = {
        "stem": {"correct": 0, "pred": 0, "gold": 0},
        "gram": {"correct": 0, "pred": 0, "gold": 0},
    }

    for entry_pred, entry_gold in zip(pred, gold):
        for token_index in range(len(entry_gold)):
            # We can determine if a token is a stem or gram by checking if it is all uppercase
            token_type = "gram" if entry_gold[token_index].isupper() else "stem"
            perf[token_type]["gold"] += 1

            if token_index < len(entry_pred):
                pred_token_type = (
                    "gram" if entry_pred[token_index].isupper() else "stem"
                )
                perf[pred_token_type]["pred"] += 1

                if entry_pred[token_index] == entry_gold[token_index]:
                    # Correct prediction
                    perf[token_type]["correct"] += 1

    stem_perf = {
        "prec": 0
        if perf["stem"]["pred"] == 0
        else perf["stem"]["correct"] / perf["stem"]["pred"],
        "rec": 0
        if perf["gram"]["gold"] == 0
        else perf["stem"]["correct"] / perf["stem"]["gold"],
    }
    if (stem_perf["prec"] + stem_perf["rec"]) == 0:
        stem_perf["f1"] = 0
    else:
        stem_perf["f1"] = (
            2
            * (stem_perf["prec"] * stem_perf["rec"])
            / (stem_perf["prec"] + stem_perf["rec"])
        )

    gram_perf = {
        "prec": 0
        if perf["gram"]["pred"] == 0
        else perf["gram"]["correct"] / perf["gram"]["pred"],
        "rec": 0
        if perf["gram"]["gold"] == 0
        else perf["gram"]["correct"] / perf["gram"]["gold"],
    }
    if (gram_perf["prec"] + gram_perf["rec"]) == 0:
        gram_perf["f1"] = 0
    else:
        gram_perf["f1"] = (
            2
            * (gram_perf["prec"] * gram_perf["rec"])
            / (gram_perf["prec"] + gram_perf["rec"])
        )
    return {"stem": stem_perf, "gram": gram_perf}


def _error_rate(preds: List[List[str]], golds: List[List[str]]) -> float:
    def _normalized_edit_dist(pred: List[str], gold: List[str]):
        """DP edit distance as in https://en.wikipedia.org/wiki/Levenshtein_distance"""
        pred = [p for p in pred if p != IGT.SEP_TOKEN]
        gold = [g for g in gold if g != IGT.SEP_TOKEN]
        if len(pred) == 0:
            return len(gold)
        if len(gold) == 0:
            return len(pred)

        dists = [[0 for _ in range(len(gold) + 1)] for _ in range(len(pred) + 1)]

        for i in range(1, len(pred) + 1):
            dists[i][0] = i
        for j in range(1, len(gold) + 1):
            dists[0][j] = j

        for j in range(1, len(gold) + 1):
            for i in range(1, len(pred) + 1):
                subst_cost = 0 if pred[i - 1] == gold[j - 1] else 1
                dists[i][j] = min(
                    dists[i - 1][j] + 1,
                    dists[i][j - 1] + 1,
                    dists[i - 1][j - 1] + subst_cost,
                )
        return dists[-1][-1] / len(gold)

    edit_dists = [_normalized_edit_dist(p, g) for p, g in zip(preds, golds)]
    return sum(edit_dists) / len(edit_dists)
