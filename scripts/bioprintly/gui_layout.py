import json
from state import GlobalState, PinNumber, SyringeNumber
import tkinter
from tkinter import Tk, ttk
from typing import Any, Callable, Dict, List, Mapping, TypedDict, cast, get_args
from util import set_value, time_ms

class GuiElement(TypedDict):
	widgets: Mapping[str, tkinter.Widget | ttk.Widget]
	update: Callable[[Mapping[str, tkinter.Widget | ttk.Widget]], Any]

def build_gui_layout(
	gui_root: Tk,
	state: GlobalState
) -> Dict[str, GuiElement]:
	gui_root.grid_rowconfigure(0, weight = 1)
	map(lambda i: gui_root.grid_columnconfigure(i, weight = 1), [0, 1, 2])
	
	left_column = ttk.Frame(gui_root)
	left_column.grid(row = 0, column = 0)
	middle_column = ttk.Frame(gui_root)
	middle_column.grid(row = 0, column = 1)
	right_column = ttk.Frame(gui_root)
	right_column.grid(row = 0, column = 2)
	
	return {
		'service_on_off_switch': {
			'widgets': (lambda: (
				switch := tkinter.Checkbutton(
					left_column,
					text = 'Enable processing',
					command = lambda: (
						set_value(state, 'service_on', not state['service_on']),
					),
				),
				switch.pack(),
				{ 'switch': switch },
			))()[-1],
			'update': lambda widgets: (
				switch := cast(tkinter.Checkbutton, widgets['switch']),
				switch.select() if state['service_on'] else switch.deselect(),
			),
		},
		'service_loop_interval': {
			'widgets': (lambda: (
				label := ttk.Label(left_column),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': (lambda widgets: (
				label := cast(ttk.Label, widgets['label']),
				label.config(text = f'''Processing interval in ms: {
					state['service_loop_interval']
				}'''),
			)),
		},
		'service_loop_measured_delta': {
			'widgets': (lambda: (
				label := ttk.Label(left_column),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': (lambda widgets: (
				label := cast(ttk.Label, widgets['label']),
				label.config(text = f'''Measured delta in ms: {
					str(state['service_loop_measured_delta']).zfill(2)
				}'''),
			)),
		},
		'selected_syringe': {
			'widgets': (lambda: (
				label := ttk.Label(left_column),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': (lambda widgets: (
				label := cast(ttk.Label, widgets['label']),
				label.config(text = f'''Selected syringe: {
					state['selected_syringe']
				}'''),
			)),
		},
		'switch_to_syringe_buttons': {
			'widgets': (lambda: (
				buttons := dict(map(
					lambda i: (f'button{i}', ttk.Button(
						left_column,
						text = f'Switch to syringe {i}',
						command = lambda: (
							state['command_queue'].append({
								'enqueued_at': time_ms(),
								'specifics': {
									'verb': 'Rotate',
									'target_syringe': i,
								},
							}),
						),
					)),
					cast(List[SyringeNumber], [1, 2, 3, 4]),
				)),
				[button.pack() for button in buttons.values()],
				buttons,
			))()[-1],
			'update': lambda widgets: None,
		},
		'pin_mappings': {
			'widgets': (lambda: (
				combobox := ttk.Combobox(
					left_column,
					state = 'readonly',
					values = sorted(get_args(PinNumber)),
				),
				combobox.pack(),
				{ 'combobox': combobox },
			))()[-1],
			'update': (lambda widgets: (
				combobox := cast(ttk.Combobox, widgets['combobox']),
			)),
		},
		'command_queue': {
			'widgets': (lambda: (
				frame := ttk.Frame(middle_column),
				frame.pack(fill = 'both', expand = True),
				text := tkinter.Text(frame),
				text.config(state = tkinter.NORMAL),
				text.pack(),
				{ 'frame': frame, 'text': text },
			))()[-1],
			'update': (lambda widgets: (
				text := cast(tkinter.Text, widgets['text']),
				text.delete('1.0', tkinter.END),
				text.insert(tkinter.END, f'Command queue:\n{'\n'.join(list(map(
					lambda command: json.dumps(
						command['specifics'],
						indent = 4,
					),
					state['command_queue'],
				)))}'),
			)),
		},
		'clear_history_button': {
			'widgets': (lambda: (
				button := ttk.Button(
					right_column,
					text = 'Clear history',
					command = lambda: state['command_history'].clear(),
				),
				button.pack(),
				{ 'button': button },
			))()[-1],
			'update': lambda widgets: None,
		},
		'command_history': {
			'widgets': (lambda: (
				frame := ttk.Frame(right_column),
				frame.pack(fill = 'both', expand = True),
				text := tkinter.Text(frame),
				text.config(state = tkinter.NORMAL),
				text.pack(),
				{ 'frame': frame, 'text': text },
			))()[-1],
			'update': (lambda widgets: (
				text := cast(tkinter.Text, widgets['text']),
				text.delete('1.0', tkinter.END),
				text.insert(
					tkinter.END,
					f'Command history:\n{'\n'.join(list(map(
						lambda command: json.dumps(
							command['specifics'],
							indent = 4,
						),
						state['command_history'],
					)))}'
				),
			)),
		},
	}
