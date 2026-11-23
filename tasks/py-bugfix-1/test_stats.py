from stats import mean_of_positive
assert mean_of_positive([1, 3, -5]) == 2.0
assert mean_of_positive([]) == 0.0
assert mean_of_positive([-1, -2]) == 0.0
print("ok")
