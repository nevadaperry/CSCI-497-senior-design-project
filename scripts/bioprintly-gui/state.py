import json
from math import floor
from os import environ
from pathlib import Path
from time import time_ns
from typing import Dict, Literal, TypedDict

class CommandRotate(TypedDict):
	verb: Literal['Rotate']
	direction: Literal['Counterclockwise', 'Clockwise']
	steps_needed_total: int
	half_steps_remaining: int
class CommandActuate(TypedDict):
	verb: Literal['Actuate']
	direction: Literal['Out', 'In']
	steps_needed_total: int
	half_steps_remaining: int
class Command(TypedDict):
	enqueued_at: int
	'''Unix epoch milliseconds'''
	started_at: int | None
	finished_at: int | None
	specifics: CommandRotate

Binary = Literal[0, 1]
class Pin(TypedDict):
	number: int
	type: Literal['input', 'output']
	value: Binary | None

class GlobalState(TypedDict):
	savefile_path: str
	pins: Dict[str, Pin]
	service_on: bool
	service_timestep_ms: int
	last_service_loop_start: int
	service_delta_ms: int
	command_queue: list[Command]
	command_history: list[Command]
	selected_syringe: Literal[0, 1, 2, 3]
	'''
	Also decides command processing interval, until we have a separate service
	or thread for command processing.
	'''
	rotator_steps_equivalent_to_90_degrees: int

def time_ms() -> int:
	return floor(time_ns() / 1e6)

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

def build_default_global_state() -> GlobalState:
	return {
		'savefile_path': establish_savefile_path(),
		'service_on': False,
		'service_timestep_ms': 8,
		'last_service_loop_start': 0,
		'service_delta_ms': 0,
		'pins': {
			'rotator_step': { 'number': 3, 'type': 'output', 'value': 0 },
			'rotator_direction': { 'number': 5, 'type': 'output', 'value': 0 },
		},
		'command_queue': [],
		'command_history': [],
		'selected_syringe': 1,
		'rotator_steps_equivalent_to_90_degrees': 235,
	}

def save_state_to_disk(state: GlobalState):
	savefile = open(state['savefile_path'], 'w')
	json.dump(state, savefile, indent = "\t")

def load_state_from_disk(state: GlobalState):
	savefile = open(state['savefile_path'], 'r')
	savedata = json.load(savefile)
	for key, value in savedata.items():
		if key in state:
			state[key] = value
