import time
_cache = {}

def get(key, loader):
    if key in _cache:
        return _cache[key][0]
    value = loader(key)
    _cache[key] = (value, time.time())
    return value
