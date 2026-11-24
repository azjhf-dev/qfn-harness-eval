def allocate(total_cents, weights):
    """Split total_cents into integer shares proportional to weights."""
    total_w = sum(weights)
    shares = []
    for w in weights:
        shares.append(round(total_cents * w / total_w))
    return shares
