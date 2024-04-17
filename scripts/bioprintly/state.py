import json
from math import floor
from os import environ
from pathlib import Path
from typing import Dict, Literal, NotRequired, Tuple, Type, TypedDict, Union
from util import Bit

PinNumber = Literal[
	         8, 10, 12,     16, 18,     22, 24, 26,         32,     36, 38, 40,
	 3,  5,  7,     11, 13, 15,     19, 21, 23,         29, 31, 33, 35, 37,
]
class Pin(TypedDict):
	number: PinNumber
	type: Literal['input', 'output']
	value: NotRequired[Bit]

SyringeNumber = Literal[1, 2, 3, 4]

class CommandRotate(TypedDict):
	verb: Literal['Rotate']
	target_syringe: SyringeNumber
	direction: NotRequired[Bit]
	half_steps_remaining: NotRequired[int]
class CommandActuate(TypedDict):
	verb: Literal['Actuate']
	direction: Bit
	steps_needed_total: int
	half_steps_remaining: NotRequired[int]
class Command(TypedDict):
	enqueued_at: int
	'''Unix epoch milliseconds'''
	started_at: NotRequired[int]
	finished_at: NotRequired[int]
	specifics: CommandRotate
class FinishedCommand(TypedDict):
	enqueued_at: int
	'''Unix epoch milliseconds'''
	started_at: int
	finished_at: int
	specifics: CommandRotate

class GlobalState(TypedDict):
	savefile_path: str
	gui_on: bool
	service_on: bool
	service_loop_interval: int
	service_loop_last_start: int
	service_loop_measured_delta: int
	pins: Dict[str, Pin]
	command_queue: list[Command]
	command_history: list[FinishedCommand]
	selected_syringe: SyringeNumber
	rotator_steps_equivalent_to_90_degrees: int

def establish_savefile_path() -> str:
	if environ.get('XDG_DATA_DIR'):
		savefolder_base = f'{environ.get('XDG_DATA_DIR')}/'
	elif environ.get('HOME'):
		savefolder_base = f'{environ.get('HOME')}/.'
	elif environ.get('APPDATA'):
		savefolder_base = f'{environ.get('APPDATA')}/'
	else:
		raise Exception(f'User directory not found as any of these env vars: XDG_DATA_DIR, HOME, APPDATA')
	savefolder_path = f'{savefolder_base}bioprintly-gui'
	Path(savefolder_path).mkdir(parents = True, exist_ok = True)
	return f'{savefolder_path}/state.json'

def save_state_to_disk(state: GlobalState):
	savefile = open(state['savefile_path'], 'w')
	json.dump(state, savefile, indent = "\t")

def load_state_from_disk(state: GlobalState):
	savefile = open(state['savefile_path'], 'r')
	savedata = json.load(savefile)
	for key, value in savedata.items():
		if key in ['savefile_path', 'gui_on', 'gui_loop_interval']:
			continue
		if key in state:
			state[key] = value

def get_initial_global_state() -> GlobalState:
	state: GlobalState = {
		'savefile_path': establish_savefile_path(),
		'gui_on': True,
		'service_on': False,
		'service_loop_interval': 8,
		'service_loop_last_start': 0,
		'service_loop_measured_delta': 0,
		'pins': {
			'rotator_step': { 'number': 3, 'type': 'output', 'value': 0 },
			'rotator_direction': { 'number': 5, 'type': 'output', 'value': 0 },
		},
		'command_queue': [],
		'command_history': [],
		'selected_syringe': 1,
		'rotator_steps_equivalent_to_90_degrees': 235,
	}
	
	try:
		load_state_from_disk(state)
	except:
		pass
	
	return state
