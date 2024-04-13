from pins import setup_pins
from state import GlobalState, get_default_global_state, process_commands
from time import time_ns
from tkinter import Tk, ttk
from tkinter.ttk import Button, Label
from typing import Any, Callable, Dict, Generic, TypedDict

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
	global_state: GlobalState
) -> Dict[str, GuiElement]:
	#gui_root.state('zoomed')
	gui_root.geometry('1280x720')
	
	return {
		'selected_syringe': {
			'element': (lambda: (
				element := Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element: (
				element.config(text = f'''Selected syringe: {
					global_state['selected_syringe']
				}'''),
			)),
		},
		'enqueue_button': {
			'element': (lambda: (
				element := Button(
					gui_root,
					text = 'Rotate 90º clockwise',
					command = lambda: (
						global_state['command_queue'].append({
							'submitted_at': time_ns(),
							'started_at': None,
							'finished_at': None,
							'specifics': {
								'verb': 'Rotate',
								'direction': 'Clockwise',
								'steps_needed_total': global_state[
									'rotator_steps_equivalent_to_90_degrees'
								],
								'half_steps_remaining': 2 * global_state[
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
				element.config(text = '\n'.join(list(map(
					lambda command: str(command),
					global_state['command_queue'],
				)))),
			)),
		},
	}

def update_gui(
	gui_root: Tk,
	gui_elements: Dict[str, GuiElement],
	global_state: GlobalState
):
	update_start_time = time_ns()
	
	process_commands(global_state)
	
	for name, gui_element in gui_elements.items():
		gui_element['update'](gui_element['element'])
	
	# Schedule another GUI update to run after 0-8 milliseconds
	gui_root.after(
		max(0, 8 - int((time_ns() - update_start_time) / 1e6)),
		update_gui,
		gui_root,
		gui_elements,
		global_state
	)

def setup_gui():
	gui_root = Tk()
	# ttkthemes: 'yaru', 'radiance', 'arc'
	# ttk Style: 'aqua', 'clam', 'alt', 'default', 'classic'
	ttk.Style().theme_use('aqua')
	gui_root.title('Bioprintly')
	global_state = get_default_global_state()
	gui_elements = build_gui_layout(gui_root, global_state)
	gui_root.after(0, update_gui, gui_root, gui_elements, global_state)
	gui_root.mainloop()

setup_pins()
setup_gui()
