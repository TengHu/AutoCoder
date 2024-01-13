class LFUCache:
    def __init__(self, capacity: int):
        # Initialize the LFU cache with a given capacity
        self.capacity = capacity
        self.frequency = {}
        self.cache = {}
        self.min_freq = 0

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        # Update the frequency of access
        self.frequency[key] += 1
        self.min_freq = min(self.frequency.values())
        return self.cache[key]
        pass

    def put(self, key: int, value: int) -> None:
        if len(self.cache) >= self.capacity:
            # Find the least frequently accessed item and remove it
            lfu_key = min(self.frequency, key=lambda k: self.frequency[k])
            self.cache.pop(lfu_key)
            self.frequency.pop(lfu_key)
        # Add the new item to the cache and update the frequency
        self.cache[key] = value
        self.frequency[key] = self.frequency.get(key, 0) + 1
        self.min_freq = min(self.frequency.values())
        pass
