from lrucache import LRUCache

c = LRUCache(2)
c.set("a", 1); c.set("b", 2)
assert c.get("a") == 1
c.set("c", 3)                      # must evict b, since a was just read
assert c.get("b") is None and c.get("a") == 1 and c.get("c") == 3
assert len(c) == 2

c2 = LRUCache(2)
c2.set("x", 1); c2.set("x", 2)     # update in place, not a new entry
assert len(c2) == 1 and c2.get("x") == 2
c2.set("y", 3); c2.set("z", 4)     # only x is evicted
assert c2.get("x") is None and c2.get("y") == 3 and c2.get("z") == 4
assert len(c2) == 2

c3 = LRUCache(1)
c3.set("k", 1); c3.set("k", 2); c3.set("j", 3)
assert c3.get("k") is None and c3.get("j") == 3 and len(c3) == 1
print("ok")
