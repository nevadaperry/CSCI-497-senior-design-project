from tkinter import BooleanVar, StringVar, messagebox
from pins import InputOutput, PinMappings, PinNumber, setup_pins
from state import CommandSpecifics, GlobalState, GuiElement, SyringeNumber, enqueue_command, save_state_to_disk
import tkinter
from tkinter import ttk
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple, cast, get_args
from util import friendly_timestamp, hsv_to_hex, intersperse, set_value

def build_gui_layout(state: GlobalState) -> Dict[str, GuiElement]:
	gui_root = state['nonpersistent']['gui_root']
	
	outermost_pad_x = 4 * state['ui_scale']
	outermost_pad_y = 4 * state['ui_scale']
	outermost = ttk.Frame(gui_root)
	outermost.pack(
		fill = 'both',
		expand = True,
		padx = outermost_pad_x,
		pady = outermost_pad_y,
	)
	outermost.grid_rowconfigure(0, weight = 1)
	[outermost.grid_columnconfigure(
		i,
		weight = 1,
		uniform = 'outermost'
	) for i in [0, 1, 2]]
	
	main_columns_pad_x = 3 * state['ui_scale']
	main_columns_pad_y = 3 * state['ui_scale']
	left_column = ttk.LabelFrame(outermost, text = 'Controls')
	left_column.grid(
		row = 0, column = 0, sticky = 'nsew',
		padx = main_columns_pad_x, pady = main_columns_pad_y,
	)
	left_column_canvas = left_column
	#left_column_canvas = tkinter.Canvas(left_column)
	#left_column_canvas.pack(fill = 'both', expand = True)
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
	
	[(
		frame.grid_propagate(False),
		frame.grid_rowconfigure(0, weight = 1),
		frame.grid_columnconfigure(0, weight = 1),
	) for frame in [left_column, middle_column, right_column]]
	
	control_frames_pad_x = 4 * state['ui_scale']
	control_frames_pad_y = 8 * state['ui_scale']
	control_frames_ipad_x = 0 * state['ui_scale']
	control_frames_ipad_y = 0 * state['ui_scale']
	
	scrollable_text_pad_left = ' ' * round(5 * state['ui_scale'])

	return {
		'ui_scale': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column_canvas,
					text = 'UI scale',
					labelanchor = 'n'
				),
				frame.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
				),
				option_menu_variable := StringVar(),
				option_menu_variable.trace_add(
					'write',
					lambda a, b, c, variable = option_menu_variable: (
						set_value(
							state,
							'ui_scale',
							float(variable.get().split('%')[0]) / 100,
						),
						save_state_to_disk(state),
						set_value(
							state['nonpersistent'],
							'reopening_gui',
							True,
						),
					),
				),
				option_menu := ttk.OptionMenu(
					frame,
					option_menu_variable,
					'',
					*['50%', '65%', '80%', '100%', '125%', '150%', '200%'],
				),
				option_menu.pack(),
				{},
			))()[-1],
			'update': lambda widgets: None,
		},
		'processing': {
			'widgets': (lambda: (
				do_this_first := ttk.LabelFrame(
					middle_column,
					labelanchor = 'n'
				),
				do_this_first.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
				),
				certify := ttk.Button(
					do_this_first,
					command = lambda: [
						set_value(
							state['nonpersistent'],
							'selected_syringe',
							1,
						)
						if messagebox.askokcancel(
							message = 'By clicking OK, you certify that you\'ve lined up the barrel with the actuator over the syringe marked #1.',
							detail = 'This is the only way this program can know the starting angle of the barrel.'
						)
						else None
					],
				),
				certify.pack(),
				processing := ttk.LabelFrame(
					middle_column,
					text = 'Processing',
					labelanchor = 'n',
				),
				processing.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
				),
				stats_table := ttk.Frame(processing),
				stats_table.pack(
					padx = control_frames_ipad_x,
					pady = control_frames_ipad_y,
				),
				switch_variable := BooleanVar(value = False),
				switch := ttk.Checkbutton(
					stats_table,
					text = 'Enable processing ',
					variable = switch_variable,
					command = lambda: (
						new_value := not (
							state['nonpersistent']['processing_enabled']
						),
						set_value(
							state['nonpersistent'],
							'processing_enabled',
							new_value,
						),
						switch_variable.set(new_value),
					),
				),
				switch.grid(row = 0, column = 0, sticky = 'e'),
				ttk.Label(
					stats_table,
					text = 'Processing interval setting:',
				).grid(row = 1, column = 0, sticky = 'e'),
				interval_setting := ttk.Label(stats_table),
				interval_setting.grid(row = 1, column = 1, sticky = 'e'),
				ttk.Label(
					stats_table,
					text = 'Measured processing interval:',
				).grid(row = 2, column = 0, sticky = 'e'),
				measured_delta := ttk.Label(stats_table),
				measured_delta.grid(row = 2, column = 1, sticky = 'e'),
				{
					'do_this_first': do_this_first,
					'certify': certify,
					'switch_variable': switch_variable,
					'switch': switch,
					'interval_setting': interval_setting,
					'measured_delta': measured_delta,
				},
			))()[-1],
			'update': lambda widgets: (
				do_this_first := cast(ttk.LabelFrame, widgets['do_this_first']),
				do_this_first.config(text = (
					'Do this first!'
					if state['nonpersistent']['selected_syringe'] == None
					else 'Alignment complete ✅'
				)),
				certify := cast(ttk.Button, widgets['certify']),
				certify.config(text = (
					'✒ Certify that the barrel is aligned'
					if state['nonpersistent']['selected_syringe'] == None
					else '(Re)-certify that the barrel is aligned'
				)),
				switch_variable := cast(BooleanVar, widgets['switch_variable']),
				switch_variable.set(
					state['nonpersistent']['processing_enabled']
				),
				interval_setting := cast(
					ttk.Label,
					widgets['interval_setting']
				),
				interval_setting.config(text = f'''{
					str(state['processing_loop_interval'])
				} ms'''),
				measured_delta := cast(ttk.Label, widgets['measured_delta']),
				measured_delta.config(text = f'''{
					str(state['processing_loop_measured_delta'])
					if state['nonpersistent']['processing_enabled']
					else '(Paused)'
				} ms'''),
			),
		},
		'rotator': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column_canvas,
					text = 'Rotator',
					labelanchor = 'n',
				),
				frame.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
				),
				selected := ttk.Label(frame),
				selected.pack(),
				buttons := dict(map(
					lambda i: (f'button{i}', ttk.Button(
						frame,
						text = f'Switch to syringe {i}',
						command = lambda: enqueue_command(state, {
							'verb': 'Rotate',
							'target_syringe': i,
						}),
					)),
					cast(List[SyringeNumber], [1, 2, 3, 4]),
				)),
				[button.pack() for button in buttons.values()],
				{ 'selected': selected, 'buttons': buttons },
			))()[-1],
			'update': lambda widgets: (
				selected := cast(ttk.Label, widgets['selected']),
				selected.config(text = f'''Selected syringe: {
					state['nonpersistent']['selected_syringe']
				}'''),
			),
		},
		'pin_io': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column_canvas,
					text = 'Pin I/O',
					labelanchor = 'n',
				),
				frame.pack(
					fill = 'both',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
				),
				frame.grid_columnconfigure(0, weight = 8, uniform = 'pin_io'),
				frame.grid_columnconfigure(1, weight = 5, uniform = 'pin_io'),
				frame.grid_columnconfigure(2, weight = 5, uniform = 'pin_io'),
				frame.grid_columnconfigure(3, weight = 5, uniform = 'pin_io'),
				frame.pack_propagate(False),
				ttk.Label(frame, text = 'Name').grid(row = 0, column = 0),
				ttk.Label(frame, text = 'Pin number').grid(row = 0, column = 1),
				ttk.Label(frame, text = 'Type').grid(row = 0, column = 2),
				ttk.Label(frame, text = 'Live value').grid(row = 0, column = 3),
				pin_rows := list(map(
					lambda i_value: (lambda: (
						row := 1 + i_value[0],
						name := i_value[1],
						name_label := ttk.Label(
							frame,
							text = name,
						),
						name_label.grid(row = row, column = 0),
						pin_number_variable := StringVar(),
						pin_number_variable.trace_add(
							'write',
							lambda a, b, c, variable = pin_number_variable: (
								set_value(
									state['pins'][name],
									'number',
									int(variable.get()),
								),
								setup_pins(state),
							),
						),
						pin_number := ttk.OptionMenu(
							frame,
							pin_number_variable,
							state['pins'][name]['number'],
							*sorted(get_args(PinNumber)),
						),
						pin_number.grid(row = row, column = 1),
						io_type_variable := StringVar(),
						io_type_variable.trace_add(
							'write',
							lambda a, b, c, variable = io_type_variable: (
								set_value(
									state['pins'][name],
									'io_type',
									variable.get(),
								),
								setup_pins(state),
							),
						),
						io_type := ttk.OptionMenu(
							frame,
							io_type_variable,
							state['pins'][name]['io_type'],
							*sorted(get_args(InputOutput)),
						),
						io_type.grid(row = row, column = 2),
						value_label := ttk.Label(
							frame,
							text = '-',
						),
						value_label.grid(row = row, column = 3),
						{
							'name': name,
							'value_label': value_label,
						},
					))()[-1],
					enumerate(PinMappings.__annotations__.keys()),
				)),
				{ 'pin_rows': pin_rows },
			))()[-1],
			'update': lambda widgets: (
				pin_rows := cast(
					List[Mapping],
					widgets['pin_rows'],
				),
				[(
					name := pin_row['name'],
					value_label := pin_row['value_label'],
					value_label.config(text = str(
						state['pins'][name]['value']
					)),
				) for pin_row in pin_rows],
			),
		},
		'command_queue': build_scrollable_text(
			middle_column,
			lambda: list(map(
				lambda command: (f'''
{scrollable_text_pad_left}[{command['specifics']['verb']}]
{scrollable_text_pad_left}Enqueued at {
	friendly_timestamp(command['enqueued_at'])
}{f'\n{scrollable_text_pad_left}Started at {
	friendly_timestamp(command['started_at'])
}' if 'started_at' in command else ''}
{friendly_specifics(command['specifics'], scrollable_text_pad_left + ' ✒ ')}
\n''',
					color_tag_from_ordinal(command['ordinal']),
				),
				state['command_queue'],
			)),
			f'\n{scrollable_text_pad_left}(Empty)',
		),
		'command_history': build_scrollable_text(
			right_column,
			lambda: list(map(
				lambda command: (f'''
{scrollable_text_pad_left}[{command['specifics']['verb']}]
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
		),
		'clear_history_button': {
			'widgets': (lambda: (
				button := ttk.Button(
					right_column,
					text = 'Clear history',
					command = lambda: [
						state['command_history'].clear()
						if messagebox.askokcancel(
							'Are you sure?',
							'Are you confident that this is the right decision',
						)
						else None
					],
				),
				button.pack(),
				{ 'button': button },
			))()[-1],
			'update': lambda widgets: None,
		},
	}

def build_scrollable_text(
	parent: tkinter.Widget | ttk.Widget,
	get_text_content: Callable[[], Sequence[
		# (text_segment, color_tag_name)
		Tuple[str, str]
	]],
	empty_text,
) -> GuiElement:
	return {
		'widgets': (lambda: (
			frame := ttk.Frame(parent),
			frame.pack(fill = 'both', expand = True),
			frame.pack_propagate(False),
			text_restrictor := ttk.Frame(frame),
			text_restrictor.pack(
				side = tkinter.LEFT,
				fill = 'both',
				expand = True
			),
			text_restrictor.pack_propagate(False),
			text := tkinter.Text(
				text_restrictor,
				state = 'disabled',
				wrap = 'none',
				highlightthickness = 0,
			),
			text.pack(fill = 'both', expand = True),
			text.config(
				selectbackground = text.cget('bg'),
				inactiveselectbackground = text.cget('bg'),
				font = 'TkTextFont',
			),
			[
				text.tag_config(f'{i}', background = bg_color)
				for (i, bg_color) in enumerate(COMMAND_COLORS)
			],
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
		)),
	}

def friendly_specifics(specifics: CommandSpecifics, pad_left = '') -> str:
	return '\n'.join(map(
		lambda item: f'{pad_left}{item[0]}: {item[1]}',
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
