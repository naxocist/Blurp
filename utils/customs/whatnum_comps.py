from dataclasses import dataclass
from random import randint
from math import log2, ceil


@dataclass(init=False)
class BinarySearch:
    def __init__(self, low, high):
        self.low, self.high = low, high
        self.target = randint(low, high)
        self.expected_guess_cnt = ceil(log2(high - low + 1))
        self.guess_cnt = 0
