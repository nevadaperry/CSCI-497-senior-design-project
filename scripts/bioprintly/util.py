from colorsys import hsv_to_rgb
from datetime import datetime
import json
from math import floor
from threading import Timer
from time import time_ns
from tkinter import Tk, Toplevel
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

def set_value(dict: Any, key: str, value: Any):
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

def deep_equals(a: Any, b: Any):
	return json.dumps(a, sort_keys = True) == json.dumps(b, sort_keys = True)

def flatten(two_level_list: List[List[Any]]) -> List[Any]:
	result = []
	for inner_list in two_level_list:
		for value in inner_list:
			result.append(value)
	return result

def maximize_tk_window(root: Tk | Toplevel):
	try:
		root.state('zoomed')
		# Workaround for zoom not working after re-opening the root window
		if root.state() != 'zoomed':
			Timer(0, lambda: root.state('zoomed')).start()
	except:
		pass

def stringify_primitive(value: Any) -> str:
	if type(value) is float:
		# 2 digits after the dot
		return str(round(value, 2))
	else:
		return str(value)

def this_action_would_put_it_further_away_from_target_than_it_is_now(
	current_position: int | float,
	change: int | float,
	target_position: int | float,
) -> bool:
	'''Useful for processing to decide when to stop driving a motor.'''
	resulting_position = current_position + change
	
	return abs(
		resulting_position - target_position
	) > abs(
		current_position - target_position
	)

def signum(n: int | float):
	return (
		0 if n == 0
		else
			1 if n > 0
			else -1
	)
