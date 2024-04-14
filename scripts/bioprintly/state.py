import json
from os import environ
from pathlib import Path
from typing import Dict, Literal, NotRequired, TypedDict
from util import Bit

class Pin(TypedDict):
	number: int
	type: Literal['input', 'output']
	value: NotRequired[Bit]

SyringeNumber = Literal[0, 1, 2, 3]

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

class GlobalState(TypedDict):
	savefile_path: str
	gui_on: bool
	service_on: bool
	service_loop_interval: int
	service_loop_last_start: int
	service_loop_measured_delta: int
	pins: Dict[str, Pin]
	command_queue: list[Command]
	command_history: list[Command]
	selected_syringe: SyringeNumber
	'''
	Also decides command processing interval, until we have a separate service
	or thread for command processing.
	'''
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
		state['gui_on'] = True
	except:
		pass
	
	return state
