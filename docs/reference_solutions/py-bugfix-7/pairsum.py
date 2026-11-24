"""Count unordered index pairs (i, j), i < j, whose values sum to target."""
from collections import Counter

def count_pairs(values, target):
    counts = Counter(values)          # one pass over the elements
    total = 0
    for v in list(counts):
        w = target - v
        if w not in counts or w < v:
            continue                  # each unordered value pair counted once
        if w == v:
            c = counts[v]
            total += c * (c - 1) // 2
        else:
            total += counts[v] * counts[w]
    return total
