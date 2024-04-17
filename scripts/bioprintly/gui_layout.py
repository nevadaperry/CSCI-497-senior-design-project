from colorsys import hsv_to_rgb
from tkinter.font import nametofont
from state import CommandSpecifics, GlobalState, PinNumber, SyringeNumber, enqueue_command
import tkinter
from tkinter import Tk, ttk
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple, TypedDict, cast, get_args
from util import friendly_timestamp, intersperse, set_value

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
	
	main_column_pad_x = 2
	main_column_pad_y = 2
	left_column = ttk.LabelFrame(gui_root, text = 'Controls')
	left_column.grid(
		row = 0, column = 0, sticky = 'nsew',
		padx = main_column_pad_x, pady = main_column_pad_y,
	)
	middle_column = ttk.LabelFrame(gui_root, text = 'Command queue')
	middle_column.grid(
		row = 0, column = 1, sticky = 'nsew',
		padx = main_column_pad_x, pady = main_column_pad_y,
	)
	right_column = ttk.LabelFrame(gui_root, text = 'Command history')
	right_column.grid(
		row = 0, column = 2, sticky = 'nsew',
		padx = main_column_pad_x, pady = main_column_pad_y,
	)
	right_column.grid_rowconfigure(0, weight = 1, uniform = 'right_column')
	right_column.grid_rowconfigure(1, weight = 29, uniform = 'right_column')
	right_column.grid_columnconfigure(0, weight = 1)
	
	[(
		frame.grid_propagate(False),
		frame.grid_rowconfigure(0, weight = 1),
		frame.grid_columnconfigure(0, weight = 1),
	) for frame in [left_column, middle_column, right_column]]
	
	control_frames_pad_x = 4
	control_frames_pad_y = 8
	control_frames_ipad_x = 0
	control_frames_ipad_y = 0
	
	return {
		'ui_scale': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column,
					text = 'UI scale',
					labelanchor = 'n'
				),
				frame.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
					ipadx = control_frames_ipad_x,
					ipady = control_frames_ipad_y,
				),
				combobox := ttk.Combobox(
					frame,
					state = 'readonly',
					values = [
						'50%', '65%', '80%', '100%', '125%', '150%', '200%'
					],
				),
				combobox.bind(
					'<<ComboboxSelected>>',
					lambda event, combobox = combobox: update_ui_scale(
						state,
						float(combobox.get().split('%')[0]),
					),
				),
				combobox.pack(),
				{},
			))()[-1],
			'update': lambda widgets: None,
		},
		'processing': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column,
					text = 'Processing',
					labelanchor = 'n'
				),
				frame.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
					ipadx = control_frames_ipad_x,
					ipady = control_frames_ipad_y,
				),
				switch := tkinter.Checkbutton(
					frame,
					text = 'Enable processing',
					command = lambda: (
						set_value(
							state,
							'processing_enabled',
							not state['processing_enabled']
						),
					),
				),
				switch.pack(),
				interval_setting := ttk.Label(frame),
				interval_setting.pack(),
				measured_delta := ttk.Label(frame),
				measured_delta.pack(),
				{
					'switch': switch,
					'interval_setting': interval_setting,
					'measured_delta': measured_delta,
				},
			))()[-1],
			'update': lambda widgets: (
				switch := cast(tkinter.Checkbutton, widgets['switch']),
				(
					switch.select()
					if state['processing_enabled']
					else switch.deselect()
				),
				interval_setting := cast(
					ttk.Label,
					widgets['interval_setting']
				),
				interval_setting.config(
					text = f'''Processing interval setting in ms: {
						state['processing_loop_interval']
					}'''
				),
				measured_delta := cast(
					ttk.Label,
					widgets['measured_delta'],
				),
				measured_delta.config(
					text = f'''Measured processing interval in ms: {
						str(state['processing_loop_measured_delta']).zfill(2)
					}'''
				),
			),
		},
		'syringe': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column,
					text = 'Syringes',
					labelanchor = 'n',
				),
				frame.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
					ipadx = control_frames_ipad_x,
					ipady = control_frames_ipad_y,
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
					state['selected_syringe']
				}'''),
			),
		},
		'pin_mappings': {
			'widgets': (lambda: (
				frame := ttk.LabelFrame(
					left_column,
					text = 'Pin mappings',
					labelanchor = 'n',
				),
				frame.pack(
					fill = 'x',
					padx = control_frames_pad_x,
					pady = control_frames_pad_y,
					ipadx = control_frames_ipad_x,
					ipady = control_frames_ipad_y,
				),
				combobox := ttk.Combobox(
					frame,
					state = 'readonly',
					values = sorted(get_args(PinNumber)),
				),
				combobox.pack(),
				{ 'combobox': combobox },
			))()[-1],
			'update': lambda widgets: None,
		},
		'command_queue': build_scrollable_text(
			middle_column,
			lambda: intersperse(list(map(
				lambda command: (
f'''{command['specifics']['verb']}
Enqueued at {friendly_timestamp(command['enqueued_at'])}
{friendly_specifics(command['specifics'])}
''',
					color_tag_from_ordinal(command['ordinal']),
				),
				state['command_queue'],
			)), ('\n', '')),
		),
		'command_history': build_scrollable_text(
			right_column,
			lambda: intersperse(list(map(
				lambda command: (
f'''{command['specifics']['verb']}
Started at {friendly_timestamp(command['started_at'])}
Finished at {friendly_timestamp(command['finished_at'])}
{friendly_specifics(command['specifics'])}
''',
					color_tag_from_ordinal(command['ordinal']),
				),
				reversed(state['command_history']),
			)), ('\n', '')),
		),
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
	}

def build_scrollable_text(
	parent: tkinter.Widget | ttk.Widget,
	get_text_content: Callable[[], Sequence[
		# (text_segment, color_tag_name)
		Tuple[str, str]
	]],
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
				else text.insert('end', '(Empty)')
			],
			text.configure(state = 'disabled'),
			text_height_after := text.count('1.0', 'end', 'ypixels')[0],
			text.yview('moveto', (
				scroll_fraction_start * text_height_before
				+ (text_height_after - text_height_before)
			) / text_height_after if scroll_fraction_start != 0 else 0),
		)),
	}

def friendly_specifics(specifics: CommandSpecifics) -> str:
	return '\n'.join(map(
		lambda item: f'    {item[0]}: {item[1]}',
		filter(
			lambda item: item[0] != 'verb',
			specifics.items(),
		),
	))

NEUTRAL_COLOR = '#272727'
COMMAND_COLORS = intersperse(list(map(
	lambda hue: '#%02x%02x%02x' % tuple(map(
		lambda rgb: round(255 * rgb),
		hsv_to_rgb(hue, 0.40, 0.12)
	)),
	reversed([0.95 - x / 5 * 0.65 for x in range(5)]),
)), NEUTRAL_COLOR) + [NEUTRAL_COLOR]

def color_tag_from_ordinal(ordinal: int) -> str:
	return str(ordinal % len(COMMAND_COLORS))

TK_STANDARD_FONT_NAMES = [
	'TkDefaultFont',
	'TkTextFont',
	'TkFixedFont',
	'TkMenuFont',
	'TkHeadingFont',
	'TkCaptionFont',
	'TkSmallCaptionFont',
	'TkIconFont',
	'TkTooltipFont',
]

def update_ui_scale(state: GlobalState, percent: float | None = None):
	if percent == None:
		percent = state['ui_scale_percent']
	else:
		state['ui_scale_percent'] = percent
	
	default_font_sizes = state['nonpersistent']['default_font_sizes']
	
	for font_name in TK_STANDARD_FONT_NAMES:
		font = nametofont(font_name)
		
		if font_name not in default_font_sizes:
			current_size = font.actual()['size']
			default_font_sizes[font_name] = current_size
		
		default_size = default_font_sizes[font_name]
		font.configure(size = round(default_size * (percent / 100)))
