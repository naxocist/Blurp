from dataclasses import dataclass
from random import randint
from math import log2, floor


@dataclass(init=False)
class BinarySearch:
    """
    Expected Behavior:
        at any possible range [l, r]
        let n = r - l + 1 = number of elements
            let k = least possible integer, where 2^k >= n
            n = 2^k: worst case = log2(n) + 1 = k + 1
            n != 2^k: worse case = floor(log2(n)) + 1 = k + 1
    """

    def __init__(self, low, high):
        self.low, self.high = low, high
        self.target = randint(low, high)
        self.expected_guess_cnt = floor(log2(high - low + 1)) + 1
        self.guess_cnt = 0

        self.success = 0

    def terminate(self, success: bool):
        self.success = 2 if success else 1
