"""Count unordered index pairs (i, j), i < j, whose values sum to target."""

def count_pairs(values, target):
    n = len(values)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if values[i] + values[j] == target:
                count += 1
    return count
