import json
from os import environ
from pathlib import Path
from pins import flip_binary, read_pin, write_pin
from queue import Queue
from time import time_ns
from typing import Deque, Literal, TypedDict

class CommandRotate(TypedDict):
	verb: Literal['Rotate']
	direction: Literal['Counterclockwise', 'Clockwise']
	steps_needed_total: int
	half_steps_remaining: int
class Command(TypedDict):
	submitted_at: int
	'''Unix epoch milliseconds'''
	started_at: int | None
	finished_at: int | None
	specifics: CommandRotate

class GlobalState(TypedDict):
	savefile_path: str
	command_queue: list[Command]
	command_history: list[Command]
	selected_syringe: Literal[0, 1, 2, 3]
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

def get_default_global_state() -> GlobalState:
	return {
		'savefile_path': establish_savefile_path(),
		'command_queue': [],
		'command_history': [],
		'selected_syringe': 1,
		'rotator_steps_equivalent_to_90_degrees': 235,
	}

def save_global_state(state: GlobalState):
	savefile = open(state['savefile_path'], 'w')
	json.dump(state, savefile, indent = "\t")

def load_global_state(state: GlobalState):
	savefile = open(state['savefile_path'], 'r')
	json.load(savefile)

def finish_active_task(state: GlobalState):
	
	save_global_state(state)

def process_commands(state: GlobalState):
	if len(state['command_queue']) == 0:
		return
	
	active_command = state['command_queue'][0]
	if active_command['started_at'] == None:
		active_command['started_at'] = time_ns()
	save_global_state(state)
	
	specifics = active_command['specifics']
	match specifics['verb']:
		case 'Rotate':
			if specifics['half_steps_remaining'] == 0:
				finish_active_task(state)
				return
			write_pin('rotator_direction', 0)
			write_pin('rotator_step', flip_binary(read_pin('rotator_step')))
			specifics['half_steps_remaining'] -= 1
