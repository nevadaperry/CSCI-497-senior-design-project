from ctypes import Array
from queue import Queue
from tkinter import Tk
from tkinter.ttk import Button, Entry, Label, Radiobutton, Widget
from typing import Callable, Dict, Literal, TypedDict, Union
from pins import read_pin, setup_pins, write_pin

class CommandRotate(TypedDict):
	type: Literal['Rotate']
	direction: Literal['Counterclockwise', 'Clockwise']
	steps_remaining: int
class Command(TypedDict):
	timestamp: int
	command: Union[CommandRotate]

class GlobalState(TypedDict):
	command_queue: Queue[Command]
	selected_syringe: int

class GuiElement(TypedDict):
	element: Widget
	update: Callable[[Widget, GlobalState], None]

def build_gui_layout(gui_root: Tk) -> Dict[str, GuiElement]:
	#gui_root.state('zoomed')
	gui_root.geometry('640x480')
	
	return {
		'title': {
			'element': (lambda: (
				element := Label(gui_root, text = 'ABC'),
				element.pack(),
				element,
			))()[-1],
			'update': lambda element, global_state: None,
		},
		'selected_syringe': {
			'element': (lambda: (
				element := Label(gui_root),
				element.pack(),
				element,
			))()[-1],
			'update': (lambda element, global_state: (
				element.config(text = f'Selected syringe: {global_state['selected_syringe']}'),
			)),
		},
	}

def update_gui(
	gui_root: Tk,
	gui_elements: Dict[str, GuiElement],
	global_state: GlobalState
):
	'''
	if global_state['rotation_steps_remaining'] > 0:
		write_pin('rotator_direction', 0)
		write_pin('rotator_step', +(not read_pin('rotator_step')))
		global_state['rotation_steps_remaining'] -= 0.5
	'''
	for name, gui_element in gui_elements.items():
		gui_element['update'](gui_element['element'], global_state)
	
	# Schedule another update to run after 8 milliseconds
	gui_root.after(8, update_gui, gui_root, gui_elements, global_state)

def setup_gui():
	gui_root = Tk()
	gui_elements = build_gui_layout(gui_root)
	global_state: GlobalState = {
		'command_queue': Queue(),
		'selected_syringe': 1,
	}
	gui_root.after(0, update_gui, gui_root, gui_elements, global_state)
	gui_root.mainloop()

setup_pins()
setup_gui()
