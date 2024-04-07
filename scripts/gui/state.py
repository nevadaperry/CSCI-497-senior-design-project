from collections import deque
import json
from os import environ
from pathlib import Path
from queue import Queue
from time import time_ns
from typing import Deque, Literal, TypedDict
from scripts.gui.pins import flip_binary, read_pin, write_pin

class CommandRotate(TypedDict):
	verb: Literal['Rotate']
	direction: Literal['Counterclockwise', 'Clockwise']
	steps_needed_total: int
	steps_remaining: int
class Command(TypedDict):
	submitted_at: int
	'''Unix epoch milliseconds'''
	started_at: int | None
	finished_at: int | None
	specifics: CommandRotate

class GlobalState(TypedDict):
	savefile_path: str
	command_queue: Deque[Command]
	command_history: list[Command]
	selected_syringe: Literal[0, 1, 2, 3]
	rotator_steps_equivalent_to_90_degrees: int

def establish_savefile_path() -> str:
	env_homes_to_try = ['XDG_DATA_DIR', 'HOME', 'USERPROFILE']
	home_path = ''
	for env_home in env_homes_to_try:
		try:
			home_path = environ.get(env_home)
			break
		except:
			pass
	else:
		raise Exception(f'''User directory not found as any of these env vars: {
			', '.join(env_homes_to_try)
		}''')
	savefolder_path = f'{home_path}/.bioprintly-gui'
	Path(savefolder_path).mkdir(parents=True, exist_ok=True)
	return f'{savefolder_path}/state.json'

def get_default_global_state() -> GlobalState:
	return {
		'savefile_path': establish_savefile_path(),
		'command_queue': deque(),
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
	active_command = state['command_queue'][0]
	if active_command['started_at'] == None:
		active_command['started_at'] = time_ns()
	specifics = active_command['specifics']
	match specifics['verb']:
		case 'Rotate':
			if specifics['steps_remaining'] == 0:
				finish_active_task(state)
				return
			write_pin('rotator_direction', 0)
			write_pin('rotator_step', flip_binary(read_pin('rotator_step')))
			state['rotation_steps_remaining'] -= 0.5
