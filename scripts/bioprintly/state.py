from copy import copy
import json
from os import environ
from pathlib import Path
from tkinter import Tk
from typing import Any, Callable, Dict, Literal, Mapping, NotRequired, TypedDict, cast, get_args, TYPE_CHECKING
from util import unix_time_ms
from pins import Bit, PinMappings

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

class GuiElement(TypedDict):
	widgets: Mapping[str, Any]
	update: Callable[[Mapping[str, Any]], Any]

class NonPersistentState(TypedDict):
	savefile_path: str
	gui_root: Tk | None
	gui_elements: Dict[str, GuiElement] | None
	default_font_sizes: Dict[str, int]
	reopening_gui: bool
	shutting_down: bool
	selected_syringe: SyringeNumber | None
	processing_enabled: bool
class GlobalState(TypedDict):
	nonpersistent: NonPersistentState
	ui_scale: float
	processing_loop_interval: int
	processing_loop_last_start: int
	processing_loop_measured_delta: int
	pins: PinMappings
	command_queue: list[Command]
	command_history: list[FinishedCommand]
	next_command_ordinal: int
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
			'gui_root': None,
			'gui_elements': None,
			'default_font_sizes': {},
			'reopening_gui': False,
			'shutting_down': False,
			'selected_syringe': None,
			'processing_enabled': False,
		},
		'ui_scale': 1,
		'processing_loop_interval': 8,
		'processing_loop_last_start': 0,
		'processing_loop_measured_delta': 0,
		'pins': cast(PinMappings, dict(map(
			lambda name: (name, {
				'number': None,
				'io_type': None,
				'value': None,
			}),
			PinMappings.__annotations__.keys(),
		))),
		'command_queue': [],
		'command_history': [],
		'next_command_ordinal': 0,
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
