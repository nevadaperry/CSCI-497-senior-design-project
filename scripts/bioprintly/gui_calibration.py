from threading import Timer
from time import sleep
from typing import Dict, List, TypedDict, cast, get_args
from pins import write_pin, zero_out_pins
from util import set_value, signum, stringify_primitive, this_action_would_put_it_further_away_from_target_than_it_is_now, unix_time_ms
from state import GlobalState, Redrawable, SyringeNumber, calibration_is_complete
from tkinter import Toplevel, messagebox, ttk

class ScaledConstants(TypedDict):
	main_cell_pad_x: float
	main_cell_pad_y: float

ACTUATOR_HANDCRANK_OPTIONS_MM = [1, 10]

def build_calibration_gui(
	state: GlobalState,
):
	nonpersistent = state['nonpersistent']
	
	modal = nonpersistent['modal'] = Toplevel()
	modal.title('Bioprintly - Calibration')
	modal.protocol(
		'WM_DELETE_WINDOW',
		lambda: close_calibration_gui(state),
	)
	
	outermost = ttk.Frame(modal)
	outermost.pack(
		fill = 'both',
		expand = True,
		padx = 8 * state['ui_scale'],
		pady = 8 * state['ui_scale'],
	)
	
	main_grid = ttk.Frame(outermost)
	main_grid.columnconfigure(0, weight = 1, uniform = 'main_grid')
	main_grid.columnconfigure(1, weight = 1, uniform = 'main_grid')
	main_grid.pack()
	
	scaled_constants: ScaledConstants = {
		'main_cell_pad_x': 2 * state['ui_scale'],
		'main_cell_pad_y': 2 * state['ui_scale'],
	}
	
	starting_row = 0
	
	nonpersistent['modal_redrawables'] += build_actuator_status_row(
		state,
		main_grid,
		scaled_constants,
		starting_row,
	)
	starting_row += 1
	
	nonpersistent['modal_redrawables'] += build_handcrank_rows(
		state,
		main_grid,
		scaled_constants,
		starting_row,
	)
	starting_row += len(ACTUATOR_HANDCRANK_OPTIONS_MM)
	
	# Blank row
	ttk.Label(main_grid).grid(row = starting_row)
	starting_row += 1
	
	nonpersistent['modal_redrawables'] += build_plunger_rows(
		state,
		main_grid,
		scaled_constants,
		starting_row,
	)
	starting_row += len(get_args(SyringeNumber))
	
	# Blank row
	ttk.Label(main_grid).grid(row = starting_row)
	starting_row += 1
	
	nonpersistent['modal_redrawables'] += build_current_syringe_rows(
		state,
		main_grid,
		scaled_constants,
		starting_row,
	)
	starting_row += len(get_args(SyringeNumber))

def build_actuator_status_row(
	state: GlobalState,
	parent: ttk.Frame,
	scaled_constants: ScaledConstants,
	starting_row: int,
):
	redrawables = []
	nonpersistent = state['nonpersistent']
	
	left_side_container = ttk.Frame(parent)
	left_side_container.grid(
		row = starting_row,
		column = 0,
		sticky = 'e',
		padx = scaled_constants['main_cell_pad_x'],
		pady = scaled_constants['main_cell_pad_x'],
	)
	ttk.Label(
		left_side_container,
		text = f'Actuator tip position:'
	).pack(side = 'left')
	actuator_position_label = ttk.Label(
		left_side_container,
		font = 'TkFixedFont'
	)
	actuator_position_label.pack(side = 'left')
	redrawables.append({
		'dependencies': [
			lambda: get_actuator_position_text(state),
		],
		'redraw': lambda: actuator_position_label.config(
			text = get_actuator_position_text(state),
		),
	})
	
	actuator_home_button = ttk.Button(
		parent,
		text = f"""Home the actuator (takes {round(
			nonpersistent['actuator_max_possible_extension_mm']
			/ nonpersistent['actuator_travel_mm_per_ms']
			/ 1000
		)} seconds)""",
		command = lambda: Timer(0, home_the_actuator, [state]).start(),
	)
	actuator_home_button.grid(
		row = starting_row,
		column = 1,
		sticky = 'w',
		padx = scaled_constants['main_cell_pad_x'],
		pady = scaled_constants['main_cell_pad_y'],
	)
	redrawables.append({
		'dependencies': [
			lambda: nonpersistent['actuator_has_calibration_lock'],
			# Workaround for lock change not triggering redraw
			lambda: round(unix_time_ms() / 1e3) % 2,
		],
		'redraw': lambda: actuator_home_button.config(
			state = (
				'disabled'
				if nonpersistent['actuator_has_calibration_lock']
				else 'normal'
			),
		),
	})
	
	return redrawables

def build_handcrank_rows(
	state: GlobalState,
	parent: ttk.Frame,
	scaled_constants: ScaledConstants,
	starting_row: int,
):
	nonpersistent = state['nonpersistent']
	redrawables = []
	
	for i, distance in enumerate(ACTUATOR_HANDCRANK_OPTIONS_MM):
		retract_button = ttk.Button(
			parent,
			state = 'disabled',
			text = f'Retract actuator {distance} mm',
			command = lambda distance=distance: (
				Timer(0, handcrank_the_actuator, [state, -distance]).start(),
			)
		)
		retract_button.grid(
			row = starting_row + i,
			column = 0,
			sticky = 'e',
			padx = scaled_constants['main_cell_pad_x'],
			pady = scaled_constants['main_cell_pad_y'],
		)
		extend_button = ttk.Button(
			parent,
			state = 'disabled',
			text = f'Extend actuator {distance} mm',
			command = lambda distance=distance: (
				Timer(0, handcrank_the_actuator, [state, distance]).start(),
			),
		)
		extend_button.grid(
			row = starting_row + i,
			column = 1,
			sticky = 'w',
			padx = scaled_constants['main_cell_pad_x'],
			pady = scaled_constants['main_cell_pad_y'],
		)
		
		for handcrank_button in [retract_button, extend_button]:
			redrawables.append({
				'dependencies': [
					lambda: state['actuator_position_mm'],
					lambda: nonpersistent['actuator_has_calibration_lock'],
					# Workaround for lock change not triggering redraw
					lambda: round(unix_time_ms() / 1e3) % 2,
				],
				'redraw': lambda handcrank_button=handcrank_button: (
					handcrank_button.config(state = (
						'disabled'
						if (
							state['actuator_position_mm'] == None
							or nonpersistent['actuator_has_calibration_lock']
						)
						else 'normal'
					)),
				),
			})
	
	return redrawables

def build_plunger_rows(
	state: GlobalState,
	parent: ttk.Frame,
	scaled_constants: ScaledConstants,
	starting_row: int,
):
	nonpersistent = state['nonpersistent']
	redrawables = []
	
	for syringe_number in get_args(SyringeNumber):
		left_side_container = ttk.Frame(parent)
		left_side_container.grid(
			row = starting_row + (syringe_number - 1),
			column = 0,
			sticky = 'e',
			padx = scaled_constants['main_cell_pad_x'],
			pady = scaled_constants['main_cell_pad_y'],
		)
		ttk.Label(
			left_side_container,
			text = f'Syringe {syringe_number}\'s plunger position:'
		).pack(side = 'left')
		plunger_position_label = ttk.Label(
			left_side_container,
			font = 'TkFixedFont'
		)
		plunger_position_label.pack(side = 'left')
		redrawables.append({
			'dependencies': [
				lambda syringe_number=syringe_number: (
					get_plunger_position_text(state, syringe_number)
				),
			],
			'redraw': lambda
				plunger_position_label=plunger_position_label,
				syringe_number=syringe_number,
			: (
				plunger_position_label.config(
					text = get_plunger_position_text(state, syringe_number)
				),
			),
		})
		
		record_button = ttk.Button(
			parent,
			text = f'Record actuator tip as plunger {syringe_number}\'s position',
			state = 'disabled',
			command = lambda syringe_number=syringe_number: (
				set_value(
					state['plunger_positions_mm'],
					str(syringe_number),
					state['actuator_position_mm'],
				),
				set_value(
					state,
					'current_syringe',
					syringe_number,
				),
			),
		)
		record_button.grid(
			row = starting_row + (syringe_number - 1),
			column = 1,
			sticky = 'w',
			padx = scaled_constants['main_cell_pad_x'],
			pady = scaled_constants['main_cell_pad_y'],
		)
		redrawables.append({
			'dependencies': [
				lambda: state['actuator_position_mm'],
				lambda: nonpersistent['actuator_has_calibration_lock'],
				# Workaround for lock change not triggering redraw
				lambda: round(unix_time_ms() / 1e3) % 2,
			],
			'redraw': lambda record_button=record_button: (
				record_button.config(state = (
					'disabled'
					if (
						state['actuator_position_mm'] == None
						or nonpersistent['actuator_has_calibration_lock']
					)
					else 'normal'
				)),
			),
		})
	
	return redrawables

def build_current_syringe_rows(
	state: GlobalState,
	parent: ttk.Frame,
	scaled_constants: ScaledConstants,
	starting_row: int,
):
	nonpersistent = state['nonpersistent']
	redrawables = []
	
	left_side_container = ttk.Frame(parent)
	left_side_container.grid(
		row = starting_row,
		column = 0,
		sticky = 'e',
		padx = scaled_constants['main_cell_pad_x'],
		pady = scaled_constants['main_cell_pad_y'],
	)
	ttk.Label(
		left_side_container,
		text = f'(Believed) current syringe:'
	).pack(side = 'left')
	current_syringe_label = ttk.Label(
		left_side_container,
		font = 'TkFixedFont'
	)
	current_syringe_label.pack(side = 'left')
	redrawables.append({
		'dependencies': [
			lambda: state['current_syringe']
		],
		'redraw': lambda: (
			current_syringe_label.config(text = str(state['current_syringe']))
		),
	})
	
	for syringe_number in get_args(SyringeNumber):
		set_syringe_button = ttk.Button(
			parent,
			state = 'disabled',
			text = f'Record {syringe_number} as the current syringe and close',
			command = lambda syringe_number=syringe_number: (
				set_value(
					state,
					'current_syringe',
					syringe_number,
				),
				close_calibration_gui(state),
			),
		)
		set_syringe_button.grid(
			row = starting_row + (syringe_number - 1),
			column = 1,
			sticky = 'w',
			padx = scaled_constants['main_cell_pad_x'],
			pady = scaled_constants['main_cell_pad_y'],
		)
		redrawables.append({
			'dependencies': [
				lambda: state['actuator_position_mm'],
				lambda: state['plunger_positions_mm'],
				lambda: nonpersistent['actuator_has_calibration_lock'],
				# Workaround for lock change not triggering redraw
				lambda: round(unix_time_ms() / 1e3) % 2,
			],
			'redraw': lambda set_syringe_button=set_syringe_button: (
				set_syringe_button.config(state = (
					'disabled'
					if (
						state['actuator_position_mm'] == None
						or not all(
							str(syringe_number) in state['plunger_positions_mm']
							for syringe_number in get_args(SyringeNumber)
						)
						or nonpersistent['actuator_has_calibration_lock']
					)
					else 'normal'
				)),
			),
		})
	
	return redrawables

def get_actuator_position_text(state: GlobalState) -> str:
	default = '(Unknown)'
	return (
		default
		if state['actuator_position_mm'] == None
		else f"{stringify_primitive(state['actuator_position_mm'])} mm"
	).rjust(len(default))

def get_plunger_position_text(
	state: GlobalState,
	syringe_number: SyringeNumber
) -> str:
	default = '(Unknown)'
	return (
		default
		if str(syringe_number) not in state['plunger_positions_mm']
		else f"""{stringify_primitive(
			state['plunger_positions_mm'][str(syringe_number)]
		)} mm"""
	).rjust(len(default))

def home_the_actuator(state: GlobalState):
	'''Only for use in calibration logic; not a substitute for CommandActuate'''
	nonpersistent = state['nonpersistent']
	
	if nonpersistent['actuator_has_calibration_lock'] == True:
		return
	nonpersistent['actuator_has_calibration_lock'] = True
	state['actuator_position_mm'] = None
	write_pin(state, 'actuator_retract', 1)
	sleep(
		nonpersistent['actuator_max_possible_extension_mm']
		/ nonpersistent['actuator_travel_mm_per_ms']
		/ 1000
		* (1 + nonpersistent['safety_margin'])
	)
	write_pin(state, 'actuator_retract', 0)
	state['actuator_position_mm'] = 0
	nonpersistent['actuator_has_calibration_lock'] = False

def handcrank_the_actuator(state: GlobalState, relative_mm_required: float):
	'''Only for use in calibration logic; not a substitute for CommandActuate'''
	nonpersistent = state['nonpersistent']
	
	if nonpersistent['actuator_has_calibration_lock'] == True:
		return
	nonpersistent['actuator_has_calibration_lock'] = True
	
	handcrank_loop_interval_ms = 8
	handcrank_loop_last_start = unix_time_ms()
	relative_mm_traveled = 0
	while True:
		handcrank_loop_measured_delta = (
			unix_time_ms() - handcrank_loop_last_start
		)
		handcrank_loop_last_start = unix_time_ms()
		expected_travel_mm = (
			signum(relative_mm_required)
			* nonpersistent['actuator_travel_mm_per_ms']
			* handcrank_loop_measured_delta
		)
		
		if cast(float, state['actuator_position_mm']) < 0:
			state['actuator_position_mm'] = 0
			break
		
		if this_action_would_put_it_further_away_from_target_than_it_is_now(
			relative_mm_traveled,
			expected_travel_mm,
			relative_mm_required,
		):
			break
		
		if (
			cast(float, state['actuator_position_mm'])
			+ expected_travel_mm
		) > (
			nonpersistent['actuator_max_possible_extension_mm']
			* (1 - nonpersistent['safety_margin'])
		):
			break
		
		if relative_mm_required > 0:
			write_pin(state, 'actuator_extend', 1)
		else:
			write_pin(state, 'actuator_retract', 1)
		
		relative_mm_traveled += expected_travel_mm
		state['actuator_position_mm'] = (
			cast(float, state['actuator_position_mm'])
			+ expected_travel_mm
		)
		
		sleep(max(0,
			handcrank_loop_interval_ms
			- (unix_time_ms() - handcrank_loop_last_start)
		) / 1e3)
	
	write_pin(state, 'actuator_extend', 0)
	write_pin(state, 'actuator_retract', 0)
	nonpersistent['actuator_has_calibration_lock'] = False

def close_calibration_gui(state: GlobalState):
	modal = state['nonpersistent']['modal']
	if modal == None:
		raise Exception('close_calibration_gui: modal == None')
	if not calibration_is_complete(state) and messagebox.askokcancel(
		message = 'Calibration incomplete',
		detail = 'Close anyway?',
	) == False:
		return
	
	state['nonpersistent']['modal_redrawables'] = []
	state['nonpersistent']['modal_dependency_cache'] = {}
	state['nonpersistent']['modal'] = None
	modal.destroy()

def toggle_processing_with_warning(state: GlobalState):
	if state['nonpersistent']['processing_enabled'] == True:
		state['nonpersistent']['processing_enabled'] = False
		zero_out_pins(state)
	elif messagebox.askokcancel(
		message = 'Careful!',
		detail = f"""Are these calibration values correct? If they're wrong, the bioprint hardware will likely crash and damage itself.

Current syringe: {state['current_syringe']}
Actuator tip position: {stringify_primitive(state['actuator_position_mm'])} mm extended

""" + ''.join(f"""Plunger {i} position: {
	stringify_primitive(state['plunger_positions_mm'][str(i)])
} mm\n"""
for i in get_args(SyringeNumber)
) + '(all measured from actuator tip home)'
	):
		state['nonpersistent']['processing_enabled'] = True
