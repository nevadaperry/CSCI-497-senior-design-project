from copy import copy
import json
from os import environ
import os
from pathlib import Path
import subprocess
from tkinter import Tk, Toplevel, messagebox
from typing import Any, Callable, Dict, List, Literal, NotRequired, TypedDict, cast, get_args
from util import unix_time_ms
from pins import PinMappings

SyringeNumber = Literal[1, 2, 3, 4]
OnOff = Literal['On', 'Off']

class CommandRotate(TypedDict):
	verb: Literal['Rotate']
	target_syringe: SyringeNumber
	relative_degrees_required: NotRequired[float]
	relative_degrees_traveled: NotRequired[float]
class CommandActuate(TypedDict):
	verb: Literal['Actuate']
	relative_mm_required: float | Literal["Go home"]
	relative_mm_traveled: NotRequired[float]
class CommandTurnHeatingPad(TypedDict):
	verb: Literal['Turn heating pad']
	target_heating_pad: SyringeNumber | Literal['Current one']
	on_or_off: OnOff
class CommandTurnUvLight(TypedDict):
	verb: Literal['Turn UV light']
	target_uv_light: SyringeNumber | Literal['Current one']
	on_or_off: OnOff

CommandSpecifics = (
	CommandRotate
	| CommandActuate
	| CommandTurnHeatingPad
	| CommandTurnUvLight
)

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

# Basically useEffect
class Redrawable(TypedDict):
	dependencies: List[Callable[[], Any]]
	'''List of functions whose return values will trigger a redraw if changed'''
	redraw: Callable[[], Any]

class NonPersistentState(TypedDict):
	savefile_path: str
	savefile_last_write: int
	gui_root: Tk | None
	gui_redrawables: List[Redrawable]
	gui_dependency_cache: Dict[str, Any]
	modal: Toplevel | None
	modal_redrawables: List[Redrawable]
	modal_dependency_cache: Dict[str, Any]
	default_font_sizes: Dict[str, int]
	reopening_gui: bool
	shutting_down: bool
	processing_enabled: bool
	processing_loop_last_start: int
	processing_loop_measured_delta: int
	processing_loop_interval_ms: int
	safety_margin: float
	'''
	General-purpose safety margin for any operation that would physically crash
	the hardware, or fail to clear an obstacle. This is especially important
	because we (Team 22) are using a servo actuator and driver that extends
	/retracts continuously while given a high signal. Bioprintly itself is not a
	Raspberry Pi OS driver, so there is no guarantee that a high signal will be
	turned off at an intended point in time.
	
	An improved iteration of this project might (1) use a stepper actuator
	rather than a servo one, to eliminate concerns over signal timing, or (2)
	delegate control of the servo actuator to an Arduino/microcontroller set up
	to accept commands with specific timing params.
	'''
	rotator_degrees_per_step: float
	actuator_travel_mm_per_ms: float
	actuator_max_possible_extension_mm: float
	actuator_has_calibration_lock: bool
	'''
	Actuator may be locked during certain calibration steps so that only one
	calibration related action may be taken at a time.
	'''
class ProcessInfo(TypedDict):
	pid: int
	ppid: int
class GlobalState(TypedDict):
	nonpersistent: NonPersistentState
	process_info: ProcessInfo
	ui_scale: float
	pins: PinMappings
	current_syringe: SyringeNumber | None
	actuator_position_mm: float | None
	plunger_positions_mm: Dict[str, float]
	'''Distances from fully retracted actuator tip to each plunger's tip'''
	command_queue: list[Command]
	command_history: list[FinishedCommand]
	next_command_ordinal: int

def establish_savefolder_path() -> str:
	if environ.get('XDG_DATA_DIR'):
		savefolder_base = f"{environ.get('XDG_DATA_DIR')}/"
	elif environ.get('HOME'):
		savefolder_base = f"{environ.get('HOME')}/."
	elif environ.get('APPDATA'):
		savefolder_base = f"{environ.get('APPDATA')}/"
	else:
		raise Exception(f'User directory not found as any of these env vars: XDG_DATA_DIR, HOME, APPDATA')
	savefolder_path = f'{savefolder_base}bioprintly'
	Path(savefolder_path).mkdir(parents = True, exist_ok = True)
	return savefolder_path

def establish_savefile_path() -> str:
	savefolder_path = establish_savefolder_path()
	return f'{savefolder_path}/state.json'

def save_state_to_disk(state: GlobalState):
	'''
	I believe this should only be called from the service thread to avoid race
	conditions.
	'''
	savefile_path = state['nonpersistent']['savefile_path']
	savefile = open(savefile_path, 'w')
	persistent_state = cast(Dict, copy(state))
	persistent_state.pop('nonpersistent')
	json.dump(
		persistent_state,
		savefile,
		indent = '\t'
	)
	state['nonpersistent']['savefile_last_write'] = unix_time_ms()

def load_state_from_disk(state: GlobalState):
	savefile_path = state['nonpersistent']['savefile_path']
	try:
		savefile = open(savefile_path, 'r')
	except:
		return
	savedata = json.load(savefile)
	for key, value in savedata.items():
		if key == 'nonpersistent':
			continue
		if key == 'process_info':
			dont_run_multiple_instances_at_once(value)
			continue
		if key in state:
			state[key] = value

def dont_run_multiple_instances_at_once(savefile_process_info: ProcessInfo):
	if type(savefile_process_info['pid']) is not int:
		raise Exception(f"Non-integer value for savefile_process_info['pid'] (bad savefile)")
	
	try:
		ppid_for_savefile_pid = int(subprocess.check_output(
			f'ps -o ppid= {savefile_process_info["pid"]}',
			shell = True,
			text = True
		).strip())
	except:
		return
	if ppid_for_savefile_pid == savefile_process_info['ppid']:
		messagebox.showerror(
			message = 'Another instance of Bioprintly appears to be running',
			detail = 'Not starting another instance to avoid conflicts.',
		)
		exit(1)

def get_initial_global_state() -> GlobalState:
	state: GlobalState = {
		'nonpersistent': {
			'savefile_path': establish_savefile_path(),
			'savefile_last_write': 0,
			'gui_root': None,
			'gui_redrawables': [],
			'gui_dependency_cache': {},
			'modal': None,
			'modal_redrawables': [],
			'modal_dependency_cache': {},
			'default_font_sizes': {},
			'reopening_gui': False,
			'shutting_down': False,
			'processing_enabled': False,
			'processing_loop_interval_ms': 8,
			'processing_loop_measured_delta': 8,
			'processing_loop_last_start': unix_time_ms(),
			'safety_margin': 0.05,
			'rotator_degrees_per_step': 90 / 235,
			'actuator_travel_mm_per_ms': 12e-3,
			'actuator_max_possible_extension_mm': 113.3,
			'actuator_has_calibration_lock': False,
		},
		'process_info': { 'pid': os.getpid(), 'ppid': os.getppid() },
		'ui_scale': 1.0,
		'pins': cast(PinMappings, dict(map(
			lambda name: (
				name,
				{
					'number': None,
					'io_type': None,
					'value': None,
				},
			),
			PinMappings.__annotations__.keys(),
		))),
		'current_syringe': None,
		'actuator_position_mm': None,
		'plunger_positions_mm': {},
		'command_queue': [],
		'command_history': [],
		'next_command_ordinal': 0,
	}
	
	load_state_from_disk(state)
	# Save process info to prevent multiple instances from running at once
	save_state_to_disk(state)
	
	return state

def calibration_is_complete(state: GlobalState) -> bool:
	return (
		state['current_syringe'] != None
		and state['actuator_position_mm'] != None
		and all(
			str(syringe_number) in state['plunger_positions_mm']
			for syringe_number in get_args(SyringeNumber)
		)
		and state['nonpersistent']['actuator_has_calibration_lock'] == False
	)

def processing_is_allowed_to_be_started(state: GlobalState) -> bool:
	return (
		calibration_is_complete(state)
		and state['nonpersistent']['modal'] == None
	)

def enqueue_command(state: GlobalState, specifics: CommandSpecifics):
	state['command_queue'].append({
		'ordinal': state['next_command_ordinal'],
		'enqueued_at': unix_time_ms(),
		'specifics': specifics,
	})
	state['next_command_ordinal'] += 1
