def allocate(total_cents, weights):
    """Largest-remainder apportionment of total_cents across weights."""
    n = len(weights)
    total_w = sum(weights)
    if total_w <= 0:
        return [0] * n
    exact = [total_cents * w / total_w for w in weights]
    shares = [int(x) for x in exact]   # exact shares are non-negative
    remainder = total_cents - sum(shares)
    order = sorted(range(n), key=lambda i: (-(exact[i] - shares[i]), i))
    for i in order[:remainder]:
        shares[i] += 1
    return shares
