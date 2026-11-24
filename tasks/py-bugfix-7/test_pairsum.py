from pairsum import count_pairs

class MeteredList:
    """Only len() and indexing; every element read is counted."""
    def __init__(self, items):
        self._items = list(items)
        self.reads = 0
    def __len__(self):
        return len(self._items)
    def __getitem__(self, i):
        self.reads += 1
        return self._items[i]

# correctness
assert count_pairs([], 10) == 0
assert count_pairs([1, 2, 3, 4], 5) == 2        # (1,4) and (2,3)
assert count_pairs([5, 5, 5], 10) == 3          # all three pairs
assert count_pairs([-1, 1, 0], 0) == 1          # (-1, 1)
assert count_pairs([-2, -3, 5], 3) == 1         # (-2, 5)
assert count_pairs([0, 0], 0) == 1

# input must not be mutated
data = [3, 1, 2]
count_pairs(data, 3)
assert data == [3, 1, 2]

# performance: average linear time, metered on element reads
values = [1] * 1000 + [2] * 1000 + [3] * 1000 + [4] * 1000
metered = MeteredList(values)
got = count_pairs(metered, 5)
assert got == 2_000_000, got                    # 1000x1000 of (1,4) plus 1000x1000 of (2,3)
assert metered.reads <= 3 * len(values), f"{metered.reads} reads on {len(values)} elements: not linear"

print("ok")
