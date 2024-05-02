from threading import Timer
from pins import InputOutput, PinMappings, PinNumber, setup_pins
from gui_calibration import ACTUATOR_HANDCRANK_OPTIONS_MM, build_calibration_gui, toggle_processing_with_warning
from state import CommandSpecifics, GlobalState, SyringeNumber, enqueue_command, processing_is_allowed_to_be_started, save_state_to_disk, Redrawable, calibration_is_complete
from tkinter import StringVar, messagebox
import tkinter
import tkinter as ttk
from typing import Any, Callable, List, Sequence, Tuple, TypedDict, get_args
from util import friendly_timestamp, hsv_to_hex, intersperse, set_value, stringify_primitive

class ScaledConstants(TypedDict):
	control_frames_pad_x: float
	control_frames_pad_y: float
	scrollable_text_pad_left: str

def build_gui_layout(state: GlobalState) -> List[Redrawable]:
	redrawables: List[Redrawable] = []
	
	left_column, middle_column, right_column = build_three_columns(state)
	
	scaled_constants: ScaledConstants = {
		'control_frames_pad_x': 4 * state['ui_scale'],
		'control_frames_pad_y': 8 * state['ui_scale'],
		'scrollable_text_pad_left': ' ' * round(5 * state['ui_scale']),
	}
	
	redrawables += build_ui_scale_control(state, left_column, scaled_constants)
	redrawables += build_rotator_controls(state, left_column, scaled_constants)
	redrawables += build_actuator_controls(state, left_column, scaled_constants)
	redrawables += build_pin_io_controls(state, left_column, scaled_constants)
	redrawables += build_processing_controls(
		state,
		middle_column,
		scaled_constants,
	)
	redrawables += build_command_queue(state, middle_column, scaled_constants)
	redrawables += build_delete_last_enqueued_command_button(
		state,
		middle_column,
		scaled_constants,
	)
	redrawables += build_command_history(state, right_column, scaled_constants)
	redrawables += build_clear_history_button(
		state,
		right_column,
		scaled_constants,
	)

	return redrawables

def build_three_columns(state: GlobalState):
	outermost = ttk.Frame(state['nonpersistent']['gui_root'])
	outermost.pack(
		fill = 'both',
		expand = True,
		padx = 4 * state['ui_scale'],
		pady = 4 * state['ui_scale'],
	)
	outermost.grid_rowconfigure(0, weight = 1)
	for i in [0, 1, 2]:
		outermost.grid_columnconfigure(
			i,
			weight = 1,
			uniform = 'outermost'
		)
	
	main_columns_pad_x = 3 * state['ui_scale']
	main_columns_pad_y = 3 * state['ui_scale']
	left_column = ttk.LabelFrame(outermost, text = 'Controls')
	left_column.grid(
		row = 0, column = 0, sticky = 'nsew',
		padx = main_columns_pad_x, pady = main_columns_pad_y,
	)
	middle_column = ttk.LabelFrame(outermost, text = 'Command queue')
	middle_column.grid(
		row = 0, column = 1, sticky = 'nsew',
		padx = main_columns_pad_x, pady = main_columns_pad_y,
	)
	right_column = ttk.LabelFrame(outermost, text = 'Command history')
	right_column.grid(
		row = 0, column = 2, sticky = 'nsew',
		padx = main_columns_pad_x, pady = main_columns_pad_y,
	)
	
	for frame in [left_column, middle_column, right_column]:
		frame.grid_propagate(False)
		frame.grid_rowconfigure(0, weight = 1)
		frame.grid_columnconfigure(0, weight = 1)
	
	return left_column, middle_column, right_column

def build_ui_scale_control(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	frame = ttk.LabelFrame(
		parent,
		text = 'UI scale',
		labelanchor = 'n'
	)
	frame.pack(
		fill = 'x',
		padx = scaled_constants['control_frames_pad_x'],
		pady = scaled_constants['control_frames_pad_y'],
	)
	ui_scale_options = ['50%', '65%', '80%', '100%', '125%', '150%', '200%']
	option_menu_variable = StringVar(
		value = f'{round(100 * state["ui_scale"])}%'
	)
	option_menu_variable.trace_add(
		'write',
		lambda a, b, c, option_menu_variable=option_menu_variable: (
			set_value(
				state,
				'ui_scale',
				float(option_menu_variable.get().split('%')[0]) / 100,
			),
			set_value(
				state['nonpersistent'],
				'reopening_gui',
				True,
			),
		),
	)
	option_menu = ttk.OptionMenu(
		frame,
		option_menu_variable,
		'',
		*ui_scale_options,
	)
	option_menu.pack()

	return [
		{
			'dependencies': [
				lambda: state['nonpersistent']['modal'] == None
			],
			'redraw': lambda: (
				option_menu.config(
					state = 'disabled'
					if state['nonpersistent']['modal'] != None
					else 'normal'
				),
			)
		},
	]

def build_rotator_controls(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	redrawables: List[Redrawable] = []
	frame = ttk.LabelFrame(
		parent,
		text = 'Rotator',
		labelanchor = 'n',
	)
	frame.pack(
		fill = 'x',
		padx = scaled_constants['control_frames_pad_x'],
		pady = scaled_constants['control_frames_pad_y'],
	)
	
	current_syringe_row = ttk.Frame(frame)
	current_syringe_row.pack()
	ttk.Label(
		current_syringe_row,
		text = 'Current syringe:',
	).pack(side = 'left')
	current_syringe_label = ttk.Label(
		current_syringe_row,
		font = 'TkFixedFont',
	)
	current_syringe_label.pack(side = 'left')
	redrawables.append({
		'dependencies': [
			lambda: state['current_syringe']
		],
		'redraw': lambda: (
			current_syringe_label.config(text = (
				state['current_syringe']
				if state['current_syringe'] != None
				else '⚠️ Unknown; awaiting calibration'
			)),
		)
	})
	
	switch_to_syringe_row = ttk.Frame(frame)
	switch_to_syringe_row.pack()
	ttk.Label(
		switch_to_syringe_row,
		text = 'Switch to syringe:',
	).pack(side = 'left')
	for syringe_number in get_args(SyringeNumber):
		switch_to_syringe_button = ttk.Button(
			switch_to_syringe_row,
			text = f'#{syringe_number}',
			command = lambda syringe_number=syringe_number: enqueue_command(
				state,
				'Operator',
				{
					'verb': 'Rotate',
					'target_syringe': syringe_number,
				},
			),
		)
		switch_to_syringe_button.pack(side = 'left')
		redrawables.append({
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled']
			],
			'redraw': lambda
				switch_to_syringe_button=switch_to_syringe_button
			: (
				switch_to_syringe_button.config(
					state = 'disabled'
					if state['nonpersistent']['processing_enabled'] == True
					else 'normal'
				),
			)
		})

	return redrawables

def build_actuator_controls(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	nonpersistent = state['nonpersistent']
	redrawables: List[Redrawable] = []
	
	frame = ttk.LabelFrame(
		parent,
		text = 'Actuator',
		labelanchor = 'n',
	)
	frame.pack(
		fill = 'x',
		padx = scaled_constants['control_frames_pad_x'],
		pady = scaled_constants['control_frames_pad_y'],
	)
	
	actuator_position_row = ttk.Frame(frame)
	actuator_position_row.pack()
	ttk.Label(
		actuator_position_row,
		text = 'Actuator position:'
	).pack(side = 'left')
	actuator_position_label = ttk.Label(
		actuator_position_row,
		font = 'TkFixedFont',
	)
	actuator_position_label.pack(side = 'left')
	redrawables.append({
		'dependencies': [
			lambda: state['actuator_position_mm']
		],
		'redraw': lambda: (
			actuator_position_label.config(text = (
				f'''{
					stringify_primitive(state['actuator_position_mm'])
				} mm extended'''
				if state['actuator_position_mm'] != None
				else '(Unknown; awaiting calibration)'
			)),
		)
	})
	
	for i, distance in enumerate(ACTUATOR_HANDCRANK_OPTIONS_MM):
		row = ttk.Frame(frame)
		row.pack()
		
		retract_button = ttk.Button(
			row,
			text = f'Retract actuator {distance} mm',
			command = lambda distance=distance: enqueue_command(
				state,
				'Operator',
				{
					'verb': 'Actuate',
					'duration_ms_required': 0.0,
					'relative_mm_required': -distance,
				},
			),
		)
		retract_button.grid(row = i, column = 0)
		redrawables.append({
			'dependencies': [
				lambda: nonpersistent['processing_enabled']
			],
			'redraw': lambda retract_button=retract_button: (
				retract_button.config(
					state = 'disabled'
					if nonpersistent['processing_enabled'] == True
					else 'normal'
				),
			)
		})
		
		extend_button = ttk.Button(
			row,
			text = f'Extend actuator {distance} mm',
			command = lambda distance=distance: enqueue_command(
				state,
				'Operator',
				{
					'verb': 'Actuate',
					'duration_ms_required': 0.0,
					'relative_mm_required': distance,
				},
			),
		)
		extend_button.grid(row = i, column = 1)
		redrawables.append({
			'dependencies': [
				lambda: nonpersistent['processing_enabled']
			],
			'redraw': lambda extend_button=extend_button: (
				extend_button.config(
					state = 'disabled'
					if nonpersistent['processing_enabled'] == True
					else 'normal'
				),
			)
		})

	return redrawables

def build_pin_io_controls(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	frame = ttk.LabelFrame(
		parent,
		text = 'Pin I/O',
		labelanchor = 'n',
	)
	frame.pack(
		fill = 'both',
		padx = scaled_constants['control_frames_pad_x'],
		pady = scaled_constants['control_frames_pad_y'],
	)
	frame.grid_columnconfigure(0, weight = 8, uniform = 'pin_io')
	frame.grid_columnconfigure(1, weight = 5, uniform = 'pin_io')
	frame.grid_columnconfigure(2, weight = 5, uniform = 'pin_io')
	frame.grid_columnconfigure(3, weight = 5, uniform = 'pin_io')
	frame.pack_propagate(False)
	ttk.Label(frame, text = 'Name').grid(row = 0, column = 0)
	ttk.Label(frame, text = 'Pin number').grid(row = 0, column = 1)
	ttk.Label(frame, text = 'Type').grid(row = 0, column = 2)
	ttk.Label(frame, text = 'Live value').grid(row = 0, column = 3)
	
	redrawables = []
	for i, name in enumerate(PinMappings.__annotations__.keys()):
		grid_row = i + 1
		name_label = ttk.Label(
			frame,
			text = name,
		)
		name_label.grid(row = grid_row, column = 0)
		pin_number_variable = StringVar()
		pin_number_initial = state['pins'][name]['number']
		if pin_number_initial != None:
			pin_number_variable.set(pin_number_initial)
		pin_number_variable.trace_add(
			'write',
			lambda a, b, c, name=name, pin_number_variable=pin_number_variable: (
				set_value(
					state['pins'][name],
					'number',
					int(pin_number_variable.get()),
				),
				setup_pins(state),
			),
		)
		pin_number_dropdown = ttk.OptionMenu(
			frame,
			pin_number_variable,
			state['pins'][name]['number'],
			*sorted(get_args(PinNumber)),
		)
		pin_number_dropdown.grid(row = grid_row, column = 1)
		io_type_variable = StringVar()
		io_type_initial = state['pins'][name]['io_type']
		if io_type_initial != None:
			io_type_variable.set(io_type_initial)
		io_type_variable.trace_add(
			'write',
			lambda a, b, c, io_type_variable=io_type_variable: (
				set_value(
					state['pins'][name],
					'io_type',
					io_type_variable.get(),
				),
				setup_pins(state),
			),
		)
		io_type_dropdown = ttk.OptionMenu(
			frame,
			io_type_variable,
			state['pins'][name]['io_type'],
			*sorted(get_args(InputOutput)),
		)
		io_type_dropdown.grid(row = grid_row, column = 2)
		live_value = ttk.Label(
			frame,
			text = '-',
		)
		live_value.grid(row = grid_row, column = 3)
		
		redrawables.append({
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled'],
			],
			'redraw': lambda pin_number_dropdown=pin_number_dropdown: (
				pin_number_dropdown.config(
					state = 'disabled'
					if state['nonpersistent']['processing_enabled']
					else 'normal',
				),
			),
		})
		redrawables.append({
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled'],
			],
			'redraw': lambda io_type_dropdown=io_type_dropdown: (
				io_type_dropdown.config(
					state = 'disabled'
					if state['nonpersistent']['processing_enabled']
					else 'normal',
				),
			),
		})
		redrawables.append({
			'dependencies': [
				lambda name=name: state['pins'][name]['value'],
			],
			'redraw': lambda name=name, live_value=live_value: (
				live_value.config(
					text = state['pins'][name]['value'],
				),
			),
		})
	
	return redrawables

def build_processing_controls(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	do_this_before_each_run = ttk.LabelFrame(
		parent,
		labelanchor = 'n',
		text = 'Do this before each run!',
	)
	do_this_before_each_run.pack(
		fill = 'x',
		padx = scaled_constants['control_frames_pad_x'],
		pady = scaled_constants['control_frames_pad_y'],
	)
	start_calibration = ttk.Button(
		do_this_before_each_run,
		command = lambda: (
			build_calibration_gui(state)
			if state['nonpersistent']['modal'] == None
			else state['nonpersistent']['modal'].focus_force()
		),
	)
	start_calibration.pack()
	controls = ttk.LabelFrame(
		parent,
		text = 'Processing',
		labelanchor = 'n',
	)
	controls.pack(
		fill = 'x',
		padx = scaled_constants['control_frames_pad_x'],
		pady = scaled_constants['control_frames_pad_y'],
	)
	# Workaround to support button colors on Mac
	try:
		tkmacosx = __import__('tkmacosx')
	except:
		tkmacosx = tkinter
	processing_switch = tkmacosx.Button(
		controls,
		command = lambda: toggle_processing_with_warning(state),
	)
	processing_switch.pack()
	stats_table = ttk.Frame(controls)
	stats_table.pack()
	ttk.Label(
		stats_table,
		text = 'Processing interval setting:',
	).grid(row = 0, column = 0, sticky = 'e')
	interval_setting = ttk.Label(stats_table, font = 'TkFixedFont')
	interval_setting.grid(row = 0, column = 1, sticky = 'e')
	ttk.Label(
		stats_table,
		text = 'Measured processing interval:',
	).grid(row = 1, column = 0, sticky = 'e')
	measured_delta = ttk.Label(stats_table, font = 'TkFixedFont')
	measured_delta.grid(row = 1, column = 1, sticky = 'e')
	
	return [
		{
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled'],
				lambda: state['current_syringe'],
				lambda: state['actuator_position_mm'],
			],
			'redraw': lambda: (
				start_calibration.config(
					state = 'disabled'
					if state['nonpersistent']['processing_enabled'] == True
					else 'normal',
					
					text = '✒ Calibrate the barrel and syringes'
					if (
						state['current_syringe'] == None
						or state['actuator_position_mm'] == None
					)
					else '(Re)-calibrate the barrel and syringes',
				),
			)
		},
		{
			'dependencies': [
				lambda: calibration_is_complete(state),
				lambda: state['nonpersistent']['modal'] != None,
				lambda: state['nonpersistent']['processing_enabled'],
			],
			'redraw': lambda: (
				processing_switch.config(
					state = 'disabled'
					if not processing_is_allowed_to_be_started(state)
					else 'normal',
					
					text = '(Calibration required)'
					if not calibration_is_complete(state)
					else
						'\nPause processing\n'
						if state['nonpersistent']['processing_enabled'] == True
						else '\nStart processing\n',
					
					background = '#555'
					if not processing_is_allowed_to_be_started(state)
					else
						'#933'
						if state['nonpersistent']['processing_enabled'] == True
						else '#393',
					
					foreground = 'white',
				)
			)
		},
		{
			'dependencies': [
				lambda: state['nonpersistent']['processing_loop_interval_ms']
			],
			'redraw': lambda: (
				interval_setting.config(text = f'''{
					str(state['nonpersistent']['processing_loop_interval_ms'])
				} ms''')
			)
		},
		{
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled'],
				lambda: state['nonpersistent']['processing_loop_measured_delta']
			],
			'redraw': lambda: (
				measured_delta.config(text = f'''{
					str(
						state['nonpersistent']['processing_loop_measured_delta']
					).rjust(8)
					if state['nonpersistent']['processing_enabled']
					else '(Paused)'
				} ms''')
			)
		},
	]

def build_scrollable_text(
	parent: tkinter.Widget | ttk.Widget,
	get_text_content: Callable[[], Sequence[
		# (text_segment, color_tag_name)
		Tuple[str, str]
	]],
	empty_text: str,
) -> List[Redrawable]:
	frame = ttk.Frame(parent)
	frame.pack(fill = 'both', expand = True)
	frame.pack_propagate(False)
	text_restrictor = ttk.Frame(frame)
	text_restrictor.pack(
		side = tkinter.LEFT,
		fill = 'both',
		expand = True
	)
	text_restrictor.pack_propagate(False)
	text = tkinter.Text(
		text_restrictor,
		state = 'disabled',
		wrap = 'none',
		highlightthickness = 0,
	)
	text.pack(fill = 'both', expand = True)
	text.config(
		selectbackground = text.cget('bg'),
		inactiveselectbackground = text.cget('bg'),
		font = 'TkTextFont',
	)
	for (i, bg_color) in enumerate(COMMAND_COLORS):
		text.tag_config(
			f'{i}',
			background = bg_color,
			foreground = 'white',
		)
	
	scrollbar = ttk.Scrollbar(
		frame,
		command = text.yview
	)
	scrollbar.pack(side = tkinter.RIGHT, fill = 'y')
	text.configure(yscrollcommand = scrollbar.set)
	
	return [
		{
			'dependencies': [get_text_content],
			'redraw': lambda: (
				text_height_before := text.count('1.0', 'end', 'ypixels')[0],
				scroll_fraction_start := text.yview()[0],
				text.configure(state = 'normal'),
				text.delete('1.0', 'end'),
				text_content := get_text_content(),
				[
					[
						text.insert(
							'end',
							text_segment,
							color_tag,
						) for (text_segment, color_tag) in text_content
					] if len(text_content) > 0
					else text.insert('end', empty_text)
				],
				text.configure(state = 'disabled'),
				text_height_after := text.count('1.0', 'end', 'ypixels')[0],
				text.yview('moveto', (
					scroll_fraction_start * text_height_before
					+ (text_height_after - text_height_before)
				) / text_height_after if scroll_fraction_start != 0 else 0),
			),
		}
	]

def build_command_queue(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	scrollable_text_pad_left = scaled_constants['scrollable_text_pad_left']
	return build_scrollable_text(
		parent,
		lambda: list(map(
			lambda command: (f'''
{scrollable_text_pad_left}[{command['specifics']['verb']}]
{scrollable_text_pad_left}Enqueued by {command['enqueued_by']}
{scrollable_text_pad_left}Enqueued at {
	friendly_timestamp(command['enqueued_at'])
}{f"""
{scrollable_text_pad_left}Started at {
	friendly_timestamp(command['started_at'])
}""" if 'started_at' in command else ''}
{friendly_specifics(command['specifics'], scrollable_text_pad_left + ' ✒ ')}
\n''',
				color_tag_from_ordinal(command['ordinal']),
			),
			state['command_queue'],
		)),
		f'\n{scrollable_text_pad_left}(Empty)',
	)
def build_delete_last_enqueued_command_button(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	button = ttk.Button(
		parent,
		text = 'Delete last enqueued command (from the bottom)',
		command = lambda: (
			set_value(state, 'command_queue', state['command_queue'][:-1]),
		),
	)
	button.pack()

	return [
		{
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled'],
			],
			'redraw': lambda: (
				button.config(state = (
					'disabled'
					if state['nonpersistent']['processing_enabled']
					else 'normal'
				)),
			),
		},
	]

def build_command_history(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	scrollable_text_pad_left = scaled_constants['scrollable_text_pad_left']
	return build_scrollable_text(
		parent,
		lambda: list(map(
			lambda command: (f'''
{scrollable_text_pad_left}[{command['specifics']['verb']}]
{scrollable_text_pad_left}Enqueued by {command['enqueued_by']}
{scrollable_text_pad_left}Enqueued at {
	friendly_timestamp(command['enqueued_at'])
}
{scrollable_text_pad_left}Started at {
	friendly_timestamp(command['started_at'])
}
{scrollable_text_pad_left}Finished at {
	friendly_timestamp(command['finished_at'], False)
} (took {(command['finished_at'] - command['started_at']):,} ms)
{friendly_specifics(command['specifics'], scrollable_text_pad_left + ' ✒ ')}
\n''',
				color_tag_from_ordinal(command['ordinal']),
			),
			reversed(state['command_history']),
		)),
		f'\n{scrollable_text_pad_left}(Empty)',
	)

def build_clear_history_button(
	state: GlobalState,
	parent: tkinter.Widget,
	scaled_constants: ScaledConstants,
) -> List[Redrawable]:
	button = ttk.Button(
		parent,
		text = 'Clear command history',
		command = lambda: [
			state['command_history'].clear()
			if messagebox.askokcancel(
				message = 'Are you sure you want to clear the command history?',
			)
			else None
		],
	)
	button.pack()

	return [
		{
			'dependencies': [
				lambda: state['nonpersistent']['processing_enabled'],
			],
			'redraw': lambda: (
				button.config(
					state = 'disabled'
					if state['nonpersistent']['processing_enabled']
					else 'normal'
				),
			),
		},
	]

def friendly_specifics(specifics: CommandSpecifics, pad_left = '') -> str:
	return '\n'.join(map(
		lambda item: f'{pad_left}{item[0]}: {stringify_primitive(item[1])}',
		filter(
			lambda item: item[0] != 'verb',
			specifics.items(),
		),
	))

GREY_BANDING = hsv_to_hex(0, 0, 0.20)
COMMAND_COLORS = intersperse(list(map(
	lambda hue: hsv_to_hex(hue, 0.50, 0.20),
	reversed([0.95 - x / 5 * 0.65 for x in range(5)]),
)), GREY_BANDING) + [GREY_BANDING]

def color_tag_from_ordinal(ordinal: int) -> str:
	return str(ordinal % len(COMMAND_COLORS))
