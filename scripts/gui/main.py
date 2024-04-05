from pins import read_pin, setup_pins, write_pin
from tkinter import *

setup_pins()
tk = Tk()
# 90 degrees
steps_remaining = 235

def update():
	global steps_remaining
	if steps_remaining > 0:
		write_pin('rotator_direction', 0)
		write_pin('rotator_step', +(not read_pin('rotator_step')))
		steps_remaining -= 0.5
	tk.after(8, update)

tk.after(0, update)
tk.mainloop()
