from copy import copy
import json
from os import environ
from pathlib import Path
from typing import Dict, Literal, NotRequired, TypedDict, cast, get_args
from util import Bit, unix_time_ms

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
CommandSpecifics = CommandRotate | CommandActuate
class Command(TypedDict):
	ordinal: int
	enqueued_at: int
	'''Unix epoch milliseconds'''
	started_at: NotRequired[int]
	finished_at: NotRequired[int]
	specifics: CommandSpecifics
class FinishedCommand(TypedDict):
	ordinal: int
	enqueued_at: int
	'''Unix epoch milliseconds'''
	started_at: int
	finished_at: int
	specifics: CommandSpecifics

class NonPersistentState(TypedDict):
	savefile_path: str
	shutting_down: bool
	default_font_sizes: Dict[str, int]
class GlobalState(TypedDict):
	nonpersistent: NonPersistentState
	ui_scale_percent: float
	processing_enabled: bool
	processing_loop_interval: int
	processing_loop_last_start: int
	processing_loop_measured_delta: int
	pins: Dict[str, Pin]
	command_queue: list[Command]
	command_history: list[FinishedCommand]
	next_command_ordinal: int
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
	savefile = open(state['nonpersistent']['savefile_path'], 'w')
	persistent_state = cast(Dict, copy(state))
	persistent_state.pop('nonpersistent')
	json.dump(
		persistent_state,
		savefile,
		indent = '\t'
	)

def load_state_from_disk(state: GlobalState):
	savefile = open(state['nonpersistent']['savefile_path'], 'r')
	savedata = json.load(savefile)
	for key, value in savedata.items():
		if key == 'nonpersistent':
			continue
		if key in state:
			state[key] = value

def get_initial_global_state() -> GlobalState:
	state: GlobalState = {
		'nonpersistent': {
			'savefile_path': establish_savefile_path(),
			'shutting_down': False,
			'default_font_sizes': {},
		},
		'ui_scale_percent': 100,
		'processing_enabled': False,
		'processing_loop_interval': 8,
		'processing_loop_last_start': 0,
		'processing_loop_measured_delta': 0,
		'pins': {
			'rotator_step': { 'number': 3, 'type': 'output', 'value': 0 },
			'rotator_direction': { 'number': 5, 'type': 'output', 'value': 0 },
		},
		'command_queue': [],
		'command_history': [],
		'next_command_ordinal': 0,
		'selected_syringe': 1,
		'rotator_steps_equivalent_to_90_degrees': 235,
	}
	
	try:
		load_state_from_disk(state)
	except:
		pass
	
	return state

def enqueue_command(state: GlobalState, specifics: CommandSpecifics):
	state['command_queue'].append({
		'ordinal': state['next_command_ordinal'],
		'enqueued_at': unix_time_ms(),
		'specifics': specifics,
	})
	state['next_command_ordinal'] += 1
