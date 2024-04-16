from math import floor
from time import time_ns
from typing import Any, Dict, Literal, cast

Bit = Literal[0, 1]

def flip_bit(value: Bit) -> Bit:
	return cast(Bit, +(not value))

def time_ms() -> int:
	return floor(time_ns() / 1e6)

def set_value(dict: Any, key: Any, value: Any):
	'''
	Useful for modifying values from inside multi-statement lambdas, which is
	normally not allowed.
	'''
	dict[key] = value

def direction(value: int) -> Bit:
	if value > 0:
		return 1
	else:
		return 0
