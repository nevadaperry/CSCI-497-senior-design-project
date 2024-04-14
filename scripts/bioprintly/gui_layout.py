from state import GlobalState
import tkinter
from tkinter import Tk, ttk
from typing import Any, Callable, Dict, List, NotRequired, Tuple, TypedDict, cast
from util import set_value, time_ms

class GuiElement(TypedDict):
	element: tkinter.Widget | ttk.Widget
	update: Callable[[tkinter.Widget | ttk.Widget], Any]
	'''
	Update function. Will be run at least once.
	'''

def build_gui_layout(
	gui_root: Tk,
	state: GlobalState
) -> Dict[str, GuiElement]:
	gui_root.state('zoomed')
	
	return {
		'service_on_off_switch': {
			'element': (lambda: (
				element := tkinter.Checkbutton(
					gui_root,
					text = 'Enable processing',
					command = lambda: (
						set_value(state, 'service_on', not state['service_on']),
					),
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: (
				element := cast(tkinter.Checkbutton, element),
				element.select() if state['service_on'] else element.deselect(),
			),
		},
		'service_loop_interval': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'''Processing interval in ms: {
					state['service_loop_interval']
				}'''),
			)),
		},
		'service_loop_measured_delta': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'''Measured delta in ms: {
					str(state['service_loop_measured_delta']).zfill(2)
				}'''),
			)),
		},
		'selected_syringe': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'''Selected syringe: {
					state['selected_syringe']
				}'''),
			)),
		},
		'switch_to_syringe_1_button': {
			'element': (lambda: (
				element := ttk.Button(
					gui_root,
					text = 'Switch to syringe 1',
					command = lambda: (
						state['command_queue'].append({
							'enqueued_at': time_ms(),
							'specifics': {
								'verb': 'Rotate',
								'target_syringe': 1,
							},
						}),
					),
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: None,
		},
		'switch_to_syringe_2_button': {
			'element': (lambda: (
				element := ttk.Button(
					gui_root,
					text = 'Switch to syringe 2',
					command = lambda: (
						state['command_queue'].append({
							'enqueued_at': time_ms(),
							'specifics': {
								'verb': 'Rotate',
								'target_syringe': 2,
							},
						}),
					),
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: None,
		},
		'switch_to_syringe_3_button': {
			'element': (lambda: (
				element := ttk.Button(
					gui_root,
					text = 'Switch to syringe 3',
					command = lambda: (
						state['command_queue'].append({
							'enqueued_at': time_ms(),
							'specifics': {
								'verb': 'Rotate',
								'target_syringe': 3,
							},
						}),
					),
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: None,
		},
		'switch_to_syringe_4_button': {
			'element': (lambda: (
				element := ttk.Button(
					gui_root,
					text = 'Switch to syringe 4',
					command = lambda: (
						state['command_queue'].append({
							'enqueued_at': time_ms(),
							'specifics': {
								'verb': 'Rotate',
								'target_syringe': 4,
							},
						}),
					),
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: None,
		},
		'command_queue': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'Command queue:\n{'\n'.join(list(map(
					lambda command: str(command),
					state['command_queue'],
				)))}'),
			)),
		},
		'clear_history_button': {
			'element': (lambda: (
				element := ttk.Button(
					gui_root,
					text = 'Clear history',
					command = lambda: state['command_history'].clear(),
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: None,
		},
		'command_history': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'Command history:\n{'\n'.join(list(map(
					lambda command: str(command),
					state['command_history'],
				)))}'),
			)),
		},
	}
