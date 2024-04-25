from copy import deepcopy
from math import floor
from threading import Timer
from tkinter.font import nametofont
from gui_layout import build_gui_layout
from state import GlobalState, save_state_to_disk
from tkinter import Tk, ttk, messagebox
from util import deep_equals, unix_time_ms

def run_gui(state: GlobalState):
	gui_root = state['nonpersistent']['gui_root'] = Tk()
	gui_root.title('Bioprintly')
	
	scale_fonts_by_ui_scale(state)
	
	gui_root.protocol(
		'WM_DELETE_WINDOW',
		lambda: confirm_close_gui(state)
	)
	
	state['nonpersistent']['gui_redrawables'] = build_gui_layout(state)
	
	gui_root.after(0, update_gui_repeatedly, state)
	
	try:
		gui_root.state('zoomed')
		# Workaround for zoom not working after re-opening the root window
		if gui_root.state() != 'zoomed':
			Timer(0, lambda: gui_root.state('zoomed')).start()
	except:
		pass
	
	gui_root.mainloop()

def update_gui_repeatedly(state: GlobalState):
	gui_update_start_time = unix_time_ms()
	gui_root = state['nonpersistent']['gui_root']
	gui_redrawables = state['nonpersistent']['gui_redrawables']
	gui_dependency_cache = state['nonpersistent']['gui_dependency_cache']
	if gui_root == None:
		raise Exception(f'update_gui_repeatedly: gui_root == None')
	
	for i, redrawable in enumerate(gui_redrawables):
		for j, dependency in enumerate(redrawable['dependencies']):
			cache_key = f'{i},{j}'
			cur_value = dependency()
			
			if cache_key in gui_dependency_cache:
				prev_value = gui_dependency_cache[cache_key]
				if not deep_equals(cur_value, prev_value):
					redrawable['redraw']()
					gui_dependency_cache[cache_key] = deepcopy(cur_value)
					break
			else:
				redrawable['redraw']()
				gui_dependency_cache[cache_key] = deepcopy(cur_value)
				break
	
	if state['nonpersistent']['reopening_gui'] == True:
		gui_root.destroy()
		return
	else:
		gui_root.after(
			max(
				0,
				# Max 10 redraws per second, to keep the RPi responsive overall
				floor(1000 / 10) - (unix_time_ms() - gui_update_start_time),
			),
			update_gui_repeatedly,
			state,
		)

def confirm_close_gui(state: GlobalState):
	if (state['nonpersistent']['gui_root'] == None):
		raise Exception('confirm_close_gui: gui_root == None')
	if (
		state['nonpersistent']['processing_enabled'] == False
		or messagebox.askokcancel(
			'Are you sure?',
			'Are you sure you want to close? This will stop command processing.',
		)
	):
		save_state_to_disk(state)
		state['nonpersistent']['shutting_down'] = True
		state['nonpersistent']['gui_root'].destroy()

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

def scale_fonts_by_ui_scale(state: GlobalState):
	default_font_sizes = state['nonpersistent']['default_font_sizes']
	
	for font_name in TK_STANDARD_FONT_NAMES:
		font = nametofont(font_name)
		
		if font_name not in default_font_sizes:
			current_size = font.actual()['size']
			default_font_sizes[font_name] = current_size
		
		default_size = default_font_sizes[font_name]
		font.configure(size = round(default_size * state['ui_scale']))
