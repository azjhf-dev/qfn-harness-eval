def mean_of_positive(xs):
    pos = [x for x in xs if x > 0]
    return sum(pos) / len(xs)
