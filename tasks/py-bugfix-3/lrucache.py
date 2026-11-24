class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self._store = {}   # key -> [value, tick]
        self._tick = 0
        self._size = 0

    def get(self, key, default=None):
        if key in self._store:
            return self._store[key][0]
        return default

    def set(self, key, value):
        self._tick += 1
        self._store[key] = [value, self._tick]
        self._size += 1
        while self._size > self.capacity:
            victim = max(self._store, key=lambda k: self._store[k][1])
            del self._store[victim]
            self._size -= 1

    def __len__(self):
        return self._size
