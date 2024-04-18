from colorsys import hsv_to_rgb
from datetime import datetime
from math import floor
from time import time_ns
from typing import Any, List, Literal, cast

def unix_time_ms() -> int:
	return floor(time_ns() / 1e6)

def friendly_timestamp(
	unix_time_ms: int,
	include_date = True,
) -> str:
	return datetime.fromtimestamp(unix_time_ms / 1000).strftime(
		'%I:%M:%S %p on %a, %b %d, %Y' if include_date else '%I:%M:%S %p'
	)

def set_value(dict: Any, key: Any, value: Any):
	'''
	Useful for modifying values from inside multi-statement lambdas, which is
	normally not allowed.
	'''
	dict[key] = value

def intersperse(list: List, item):
	'''
	Adds `item` between each member of `list`.
	From https://stackoverflow.com/a/5921708
	'''
	result = [item] * (len(list) * 2 - 1)
	result[0::2] = list
	return result

def hsv_to_hex(hue: float, saturation: float, value: float):
	return '#%02x%02x%02x' % tuple(map(
		lambda rgb: round(255 * rgb),
		hsv_to_rgb(hue, saturation, value)
	))

def throw(exception: Exception):
	'''Allows raising exceptions inside lambdas'''
	raise exception
