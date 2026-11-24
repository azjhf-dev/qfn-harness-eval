from intervals import merge_intervals

def check(got, want):
    assert got == want, f"got {got}, want {want}"

src = [[5, 7], [1, 3], [2, 4]]
check(merge_intervals(src), [[1, 4], [5, 7]])   # unsorted input
assert src == [[5, 7], [1, 3], [2, 4]], "input must not be mutated"

check(merge_intervals([[1, 3], [3, 5]]), [[1, 5]])        # touching intervals merge
check(merge_intervals([[1, 4], [2, 3]]), [[1, 4]])        # nested
check(merge_intervals([]), [])
check(merge_intervals([[2, 2]]), [[2, 2]])
check(merge_intervals([[1, 2], [4, 5], [2, 4]]), [[1, 5]])  # unsorted chain of touching
print("ok")
