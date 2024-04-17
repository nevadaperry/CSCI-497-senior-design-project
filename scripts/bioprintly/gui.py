from math import floor
from gui_layout import GuiElement, build_gui_layout, update_ui_scale
from state import GlobalState
from tkinter import Tk, ttk, messagebox
from typing import Dict
from util import unix_time_ms

def setup_gui(state: GlobalState):
	gui_root = Tk()
	# ttkthemes themes: 'yaru', 'radiance', 'arc'
	# vanilla ttk themes: 'aqua', 'clam', 'alt', 'default', 'classic'
	ttk.Style().theme_use('aqua')
	gui_root.title('Bioprintly')
	gui_root.state('zoomed')
	update_ui_scale(state)
	
	gui_root.protocol(
		'WM_DELETE_WINDOW',
		lambda: confirm_close_gui(gui_root, state)
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
	gui_update_start_time = unix_time_ms()
	
	for name, gui_element in gui_elements.items():
		gui_element['update'](gui_element['widgets'])
	
	gui_root.after(
		max(
			0,
			floor(1000 / 5) - (unix_time_ms() - gui_update_start_time),
		),
		update_gui_repeatedly,
		gui_root,
		gui_elements,
		state,
	)

def confirm_close_gui(gui_root: Tk, state: GlobalState):
	if messagebox.askokcancel(
		'Are you sure?',
		'Are you sure you want to close? This will stop command processing.',
	):
		state['nonpersistent']['shutting_down'] = True
		gui_root.destroy()
