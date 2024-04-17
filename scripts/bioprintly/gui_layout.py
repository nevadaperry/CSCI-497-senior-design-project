import json
from state import GlobalState, PinNumber, SyringeNumber
import tkinter
from tkinter import Tk, ttk
from typing import Any, Callable, Dict, List, Mapping, TypedDict, cast, get_args
from util import friendly_timestamp, set_value, unix_time_ms

class GuiElement(TypedDict):
	widgets: Mapping[str, tkinter.Widget | ttk.Widget]
	update: Callable[[Mapping[str, tkinter.Widget | ttk.Widget]], Any]

def build_gui_layout(
	gui_root: Tk,
	state: GlobalState
) -> Dict[str, GuiElement]:
	gui_root.grid_rowconfigure(0, weight = 1)
	[gui_root.grid_columnconfigure(
		i,
		weight = 1,
		uniform='gui_root'
	) for i in [0, 1, 2]]
	
	left_column = ttk.Frame(gui_root)
	left_column.grid(row = 0, column = 0, sticky = 'nsew')
	middle_column = ttk.Frame(gui_root)
	middle_column.grid(row = 0, column = 1, sticky = 'nsew')
	right_column = ttk.Frame(gui_root)
	right_column.grid(row = 0, column = 2, sticky = 'nsew')
	right_column.grid_rowconfigure(0, weight = 1, uniform = 'right_column')
	right_column.grid_rowconfigure(1, weight = 29, uniform = 'right_column')
	right_column.grid_columnconfigure(0, weight = 1)
	
	[(
		frame.grid_propagate(False),
		frame.grid_rowconfigure(0, weight = 1),
		frame.grid_columnconfigure(0, weight = 1),
	) for frame in [left_column, middle_column, right_column]]
	
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
			'update': lambda widgets: (
				label := cast(ttk.Label, widgets['label']),
				label.config(text = f'''Processing interval setting in ms: {
					state['service_loop_interval']
				}'''),
			),
		},
		'service_loop_measured_delta': {
			'widgets': (lambda: (
				label := ttk.Label(left_column),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': lambda widgets: (
				label := cast(ttk.Label, widgets['label']),
				label.config(text = f'''Measured processing interval in ms: {
					str(state['service_loop_measured_delta']).zfill(2)
				}'''),
			),
		},
		'selected_syringe': {
			'widgets': (lambda: (
				label := ttk.Label(left_column),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': lambda widgets: (
				label := cast(ttk.Label, widgets['label']),
				label.config(text = f'''Selected syringe: {
					state['selected_syringe']
				}'''),
			),
		},
		'switch_to_syringe_buttons': {
			'widgets': (lambda: (
				buttons := dict(map(
					lambda i: (f'button{i}', ttk.Button(
						left_column,
						text = f'Switch to syringe {i}',
						command = lambda: (
							state['command_queue'].append({
								'enqueued_at': unix_time_ms(),
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
			'update': lambda widgets: (
				combobox := cast(ttk.Combobox, widgets['combobox']),
			),
		},
		'command_history_label': {
			'widgets': (lambda: (
				label := ttk.Label(middle_column, text = 'Command queue'),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': lambda widgets: None,
		},
		'command_queue': build_scrollable_text(
			middle_column,
			lambda: '\n'.join(list(map(
				lambda command:
f'''Enqueued at {friendly_timestamp(command['enqueued_at'])}
{json.dumps(command['specifics'], indent = 4)}
''',
				reversed(state['command_queue']),
			))),
		),
		'command_history_label': {
			'widgets': (lambda: (
				label := ttk.Label(right_column, text = 'Command history'),
				label.pack(),
				{ 'label': label },
			))()[-1],
			'update': lambda widgets: None,
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
		'command_history': build_scrollable_text(
			right_column,
			lambda: '\n'.join(list(map(
				lambda command:
f''' Started at {friendly_timestamp(command['started_at'])}
Finished at {friendly_timestamp(command['finished_at'])}
{json.dumps(command['specifics'], indent = 4)}
''',
				reversed(state['command_history']),
			))),
		),
	}

def build_scrollable_text(
	parent: tkinter.Widget | ttk.Widget,
	text_content: Callable[[], str],
) -> GuiElement:
	return {
		'widgets': (lambda: (
			frame := ttk.Frame(parent),
			frame.pack(fill = 'both', expand = True),
			frame.pack_propagate(False),
			text_cage := ttk.Frame(frame),
			text_cage.pack(side = tkinter.LEFT, fill = 'both', expand = True),
			text_cage.pack_propagate(False),
			text := tkinter.Text(text_cage, state = 'disabled'),
			text.config(selectbackground = text.cget('bg'), inactiveselectbackground = text.cget('bg')),
			text.pack(fill = 'both', expand = True),
			scrollbar := ttk.Scrollbar(
				frame,
				command = text.yview
			),
			scrollbar.pack(side = tkinter.RIGHT, fill = 'y'),
			text.configure(yscrollcommand = scrollbar.set),
			{ 'text': text, 'scrollbar': scrollbar },
		))()[-1],
		'update': (lambda widgets: (
			text := cast(tkinter.Text, widgets['text']),
			text_height_before := text.count('1.0', 'end', 'ypixels')[0],
			scroll_fraction_start := text.yview()[0],
			text.configure(state = 'normal'),
			text.delete('1.0', 'end'),
			text.insert(
				'end',
				text_content(),
			),
			text.configure(state = 'disabled'),
			text_height_after := text.count('1.0', 'end', 'ypixels')[0],
			text.yview('moveto', (
				scroll_fraction_start * text_height_before
				+ (text_height_after - text_height_before)
			) / text_height_after if scroll_fraction_start != 0 else 0),
		)),
	}
