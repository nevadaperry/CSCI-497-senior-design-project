from pins import setup_pins, zero_out_pins_and_exit
from service import run_service
from state import GlobalState, build_default_global_state, load_state_from_disk, save_state_to_disk, time_ms
from threading import Timer
import tkinter
from tkinter import Tk, ttk, messagebox
from typing import Any, Callable, Dict, TypedDict, cast
from util import set_value

class GuiElement(TypedDict):
	element: tkinter.Widget | ttk.Widget
	update: Callable[[tkinter.Widget | ttk.Widget], Any]

def build_gui_layout(
	gui_root: Tk,
	state: GlobalState
) -> Dict[str, GuiElement]:
	#gui_root.state('zoomed')
	gui_root.geometry('1280x720')
	
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
		'service_timestep': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'''Service timestep in ms: {
					state['service_timestep_ms']
				}'''),
			)),
		},
		'service_delta': {
			'element': (lambda: (
				element := ttk.Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element := cast(ttk.Label, element),
				element.config(text = f'''Service delta in ms: {
					state['service_delta_ms']
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
		'enqueue_rotate_button': {
			'element': (lambda: (
				element := ttk.Button(
					gui_root,
					text = 'Rotate 90º clockwise',
					command = lambda: (
						state['command_queue'].append({
							'enqueued_at': time_ms(),
							'started_at': None,
							'finished_at': None,
							'specifics': {
								'verb': 'Rotate',
								'direction': 'Clockwise',
								'steps_needed_total': state[
									'rotator_steps_equivalent_to_90_degrees'
								],
								'half_steps_remaining': 2 * state[
									'rotator_steps_equivalent_to_90_degrees'
								],
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

def update_gui(
	gui_root: Tk,
	gui_elements: Dict[str, GuiElement],
	state: GlobalState,
):
	gui_update_start_time = time_ms()
	
	for name, gui_element in gui_elements.items():
		gui_element['update'](gui_element['element'])
	
	gui_root.after(
		max(
			0,
			# 62.5 fps or less
			16 - (time_ms() - gui_update_start_time),
		),
		update_gui,
		gui_root,
		gui_elements,
		state
	)

def confirm_close_gui(state):
	if messagebox.askokcancel(
		'Are you sure?',
		'Are you sure you want to close? This will save the current state and stop command processing.',
	):
		save_state_to_disk(state)
		zero_out_pins_and_exit(state)

def setup_close_handlers(gui_root: Tk, state: GlobalState):
	gui_root.protocol(
		"WM_DELETE_WINDOW",
		lambda: confirm_close_gui(state)
	)

def setup_gui():
	gui_root = Tk()
	# ttkthemes themes: 'yaru', 'radiance', 'arc'
	# vanilla ttk themes: 'aqua', 'clam', 'alt', 'default', 'classic'
	ttk.Style().theme_use('aqua')
	gui_root.title('Bioprintly')
	
	state = build_default_global_state()
	try:
		load_state_from_disk(state)
	except:
		pass
	setup_pins(state)
	setup_close_handlers(gui_root, state)
	
	gui_elements = build_gui_layout(gui_root, state)
	Timer(0, run_service, [state]).start()
	gui_root.after(0, update_gui, gui_root, gui_elements, state)
	gui_root.mainloop()

setup_gui()
