from datetime import datetime
from math import floor
from time import time_ns
from typing import Any, List, Literal, cast

Bit = Literal[0, 1]

def flip_bit(value: Bit) -> Bit:
	return cast(Bit, +(not value))

def unix_time_ms() -> int:
	return floor(time_ns() / 1e6)

def friendly_timestamp(unix_time_ms: int) -> str:
	return datetime.fromtimestamp(unix_time_ms / 1000).strftime(
		'%I:%M:%S %p on %a, %b %d, %Y'
	)

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

def intersperse(list: List, item):
	'''
	Adds `item` between each member of `list`.
	From https://stackoverflow.com/a/5921708
	'''
	result = [item] * (len(list) * 2 - 1)
	result[0::2] = list
	return result
