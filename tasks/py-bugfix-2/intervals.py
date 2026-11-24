def merge_intervals(intervals):
    # intervals: list of [start, end] with start <= end
    merged = []
    for iv in intervals:
        if merged and iv[0] < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], iv[1])
        else:
            merged.append(iv)
    return merged
