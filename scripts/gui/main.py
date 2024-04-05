from typing import TypedDict
from pins import read_pin, setup_pins, write_pin
from tkinter import StringVar, Tk

class GuiState(TypedDict):
	root: Tk
	steps_remaining: int
def update_gui(state: GuiState):
	if state['steps_remaining'] > 0:
		write_pin('rotator_direction', 0)
		write_pin('rotator_step', +(not read_pin('rotator_step')))
		state['steps_remaining'] -= 0.5
	
	# Schedule another update to run after 8 milliseconds
	state['root'].after(8, update_gui, state)

def setup_gui():
	root = Tk()
	root.state('zoomed')
	abc = StringVar()
	root.after(0, update_gui, {
		'root': root,
		# 90 degrees
		'steps_remaining': 235,
	})
	root.mainloop()

setup_pins()
setup_gui()
