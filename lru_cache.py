class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.frequency = {}

    def get(self, key: int) -> int:
        if key in self.cache:
            self.frequency[key] += 1
            return self.cache[key]
        return -1

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.cache:
            self.cache[key] = value
            self.frequency[key] += 1
        else:
            if len(self.cache) >= self.capacity:
                min_freq = min(self.frequency.values())
                least_freq_keys = [k for k, v in self.frequency.items() if v == min_freq]
                least_freq_key = least_freq_keys[0]
                del self.cache[least_freq_key]
                del self.frequency[least_freq_key]
            self.cache[key] = value
            self.frequency[key] = 1
