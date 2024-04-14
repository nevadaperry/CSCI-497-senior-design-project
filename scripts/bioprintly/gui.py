from gui_layout import GuiElement, build_gui_layout
import json
from math import floor
from pins import zero_out_pins_and_exit
from state import GlobalState, save_state_to_disk
from tkinter import Tk, ttk, messagebox
from typing import Dict
from util import time_ms

def setup_gui(state: GlobalState):
	gui_root = Tk()
	# ttkthemes themes: 'yaru', 'radiance', 'arc'
	# vanilla ttk themes: 'aqua', 'clam', 'alt', 'default', 'classic'
	ttk.Style().theme_use('aqua')
	gui_root.title('Bioprintly')
	
	gui_root.protocol(
		"WM_DELETE_WINDOW",
		lambda: confirm_close_gui(state)
	)
	
	gui_elements = build_gui_layout(gui_root, state)
	
	gui_root.after(
		0,
		update_gui_repeatedly,
		gui_root,
		gui_elements,
		state,
	)
	gui_root.mainloop()

def update_gui_repeatedly(
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
			state['gui_loop_interval'] - (time_ms() - gui_update_start_time),
		),
		update_gui_repeatedly,
		gui_root,
		gui_elements,
		state,
	)

def confirm_close_gui(state):
	if messagebox.askokcancel(
		'Are you sure?',
		'Are you sure you want to close? This will save the current state and stop command processing.',
	):
		save_state_to_disk(state)
		state['gui_on'] = False
		zero_out_pins_and_exit(state)
