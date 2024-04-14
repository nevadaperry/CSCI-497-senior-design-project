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
	
	cached_trigger_values = {}
	gui_root.after(
		0,
		update_gui_repeatedly,
		gui_root,
		gui_elements,
		state,
		cached_trigger_values
	)
	gui_root.mainloop()

def update_gui_repeatedly(
	gui_root: Tk,
	gui_elements: Dict[str, GuiElement],
	state: GlobalState,
	cached_trigger_values: Dict[str, str],
):
	'''
	Update GUI elements based on triggers, where each element's update function
	will be run if its trigger value has changed. Similar to useEffect/useMemo
	from React if you're familiar with that.
	'''
	gui_update_start_time = time_ms()
	
	for name, gui_element in gui_elements.items():
		if not 'update_trigger' in gui_element:
			continue
		
		trigger_dict = gui_element['update_trigger'][0]
		trigger_key = gui_element['update_trigger'][1]
		new_cached_value = json.dumps(
			trigger_dict[trigger_key],
			sort_keys = True
		)
		
		if \
			name not in cached_trigger_values or \
			new_cached_value != cached_trigger_values[name] \
		:
			gui_element['update'](gui_element['element']) # type: ignore
		
		cached_trigger_values[name] = new_cached_value
	
	gui_root.after(
		max(
			0,
			# 60 fps or so
			floor(1000 / 60) - (time_ms() - gui_update_start_time),
		),
		update_gui_repeatedly,
		gui_root,
		gui_elements,
		state,
		cached_trigger_values,
	)

def confirm_close_gui(state):
	if messagebox.askokcancel(
		'Are you sure?',
		'Are you sure you want to close? This will save the current state and stop command processing.',
	):
		save_state_to_disk(state)
		state['gui_on'] = False
		zero_out_pins_and_exit(state)
