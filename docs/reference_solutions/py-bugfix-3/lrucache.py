class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self._store = {}   # key -> [value, tick]
        self._tick = 0

    def get(self, key, default=None):
        if key in self._store:
            self._tick += 1
            self._store[key][1] = self._tick
            return self._store[key][0]
        return default

    def set(self, key, value):
        self._tick += 1
        self._store[key] = [value, self._tick]
        while len(self._store) > self.capacity:
            victim = min(self._store, key=lambda k: self._store[k][1])
            del self._store[victim]

    def __len__(self):
        return len(self._store)
