from pins import setup_pins, zero_out_pins_and_exit
from process import process_commands
from state import GlobalState, build_default_global_state, load_state_from_disk, save_state_to_disk, time_ms
from tkinter import Tk, ttk, messagebox
from tkinter.ttk import Button, Label
from typing import Any, Callable, Dict, TypedDict

Widget = Button | Label
'''
Although Python 3.11 supports using Generic[T] with TypedDict, Pylance (for type
checking in VSCode) does not support it yet. Instead, we replace Widget with a
union of the Widget types that we use as a faux-generic.
'''
class GuiElement(TypedDict):
	element: Widget
	update: Callable[[Widget], Any]

def build_gui_layout(
	gui_root: Tk,
	state: GlobalState
) -> Dict[str, GuiElement]:
	#gui_root.state('zoomed')
	gui_root.geometry('1280x720')
	
	return {
		'update_delta': {
			'element': (lambda: (
				element := Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element.config(text = f'''Update delta in ms: {
					state['update_delta_ms']
				}'''),
			)),
		},
		'selected_syringe': {
			'element': (lambda: (
				element := Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element.config(text = f'''Selected syringe: {
					state['selected_syringe']
				}'''),
			)),
		},
		'button_to_enqueue_rotate': {
			'element': (lambda: (
				element := Button(
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
					)
				),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element: None,
		},
		'command_queue': {
			'element': (lambda: (
				element := Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element.config(text = f'Command queue:\n{'\n'.join(list(map(
					lambda command: str(command),
					state['command_queue'],
				)))}'),
			)),
		},
		'command_history': {
			'element': (lambda: (
				element := Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
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
	update_start_time = time_ms()
	state['update_delta_ms'] = update_start_time - state['last_update_start_time']
	
	process_commands(state)
	
	for name, gui_element in gui_elements.items():
		gui_element['update'](gui_element['element'])
	
	# Schedule another GUI update to run after up to gui_update_interval_ms
	state['last_update_start_time'] = time_ms()
	gui_root.after(
		max(
			0,
			state['gui_update_interval_ms']
				- (time_ms() - update_start_time),
		),
		update_gui,
		gui_root,
		gui_elements,
		state,
	)

def confirm_close_gui(gui_root, state):
	if messagebox.askokcancel(
		'Are you sure?',
		'Are you sure you want to close? This will save the current state and stop command processing.',
	):
		save_state_to_disk(state)
		zero_out_pins_and_exit(state)

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
	
	gui_root.protocol(
		"WM_DELETE_WINDOW",
		lambda gui_root = gui_root: confirm_close_gui(gui_root, state)
	)
	gui_elements = build_gui_layout(gui_root, state)
	gui_root.after(0, update_gui, gui_root, gui_elements, state)
	gui_root.mainloop()

setup_gui()
