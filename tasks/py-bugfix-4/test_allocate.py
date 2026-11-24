from allocate import allocate

assert allocate(100, [1, 1, 1]) == [34, 33, 33]   # exact thirds, earliest weight wins the tie
assert allocate(101, [1, 1]) == [51, 50]
assert allocate(3, [1, 1, 1, 1]) == [1, 1, 1, 0]
assert allocate(0, [3, 5]) == [0, 0]
assert allocate(50, [0, 0]) == [0, 0]             # zero total weight: no crash
assert allocate(7, [2, 3]) == [3, 4]

sh = allocate(1234567, list(range(1, 20)))        # conservation at scale
assert sum(sh) == 1234567
assert all(isinstance(x, int) for x in sh)
print("ok")
