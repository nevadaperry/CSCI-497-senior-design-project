from threading import Timer
from time import sleep
from typing import cast, get_args
from pins import write_pin
from util import set_value, signum, stringify_primitive, this_action_would_put_it_further_away_from_target_than_it_is_now
from state import GlobalState, SyringeNumber, calibration_is_complete
from tkinter import Toplevel, messagebox, ttk

ACTUATOR_HANDWHEEL_OPTIONS = [0.5, 10]

def home_the_actuator(state: GlobalState):
	'''Only for use in calibration logic; not a substitute for CommandActuate'''
	nonpersistent = state['nonpersistent']
	
	if nonpersistent['actuator_has_calibration_lock'] == True:
		return
	nonpersistent['actuator_has_calibration_lock'] = True
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

def handwheel_the_actuator(state: GlobalState, relative_mm_required: float):
	'''Only for use in calibration logic; not a substitute for CommandActuate'''
	nonpersistent = state['nonpersistent']
	
	if nonpersistent['actuator_has_calibration_lock'] == True:
		return
	nonpersistent['actuator_has_calibration_lock'] = True
	
	relative_mm_traveled = 0
	expected_travel_per_step = (
		signum(relative_mm_required)
		* nonpersistent['actuator_travel_mm_per_ms']
		* nonpersistent['processing_loop_measured_delta']
	)
	while True:
		if this_action_would_put_it_further_away_from_target_than_it_is_now(
			relative_mm_traveled,
			expected_travel_per_step,
			relative_mm_required,
		):
			break
		
		if (
			cast(float, state['actuator_position_mm'])
			+ expected_travel_per_step
		) > (
			nonpersistent['actuator_max_possible_extension_mm']
			* (1 - nonpersistent['safety_margin'])
		):
			messagebox.showwarning(
				message = 'Actuator has reached the maximum safe distance programmed',
				detail = f"({nonpersistent['actuator_max_possible_extension_mm']} mm minus a {100 * nonpersistent['safety_margin']}% safety margin)",
			)
			break
		
		if signum(relative_mm_required) == 1:
			write_pin(state, 'actuator_extend', 1)
		else:
			write_pin(state, 'actuator_retract', 1)
		relative_mm_traveled += expected_travel_per_step
		
		sleep(state['nonpersistent']['processing_loop_interval_ms'])
	
	write_pin(state, 'actuator_extend', 0)
	write_pin(state, 'actuator_retract', 0)
	nonpersistent['actuator_has_calibration_lock'] = False

def build_calibration_gui(state: GlobalState):
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
	
	redrawables = nonpersistent['modal_redrawables']
	
	main_grid = ttk.Frame(outermost)
	main_grid.columnconfigure(0, weight = 1, uniform = 'main_grid')
	main_grid.columnconfigure(1, weight = 1, uniform = 'main_grid')
	main_grid.pack()
	
	main_cell_pad_x = 2 * state['ui_scale']
	main_cell_pad_y = 2 * state['ui_scale']
	
	if 'Actuator status row':
		left_side_container = ttk.Frame(main_grid)
		left_side_container.grid(
			row = 0,
			column = 0,
			sticky = 'e',
			padx = main_cell_pad_x,
			pady = main_cell_pad_y
		)
		ttk.Label(
			left_side_container,
			text = f'Actuator position:'
		).pack(side = 'left')
		actuator_position_label = ttk.Label(
			left_side_container,
			font = 'TkFixedFont'
		)
		actuator_position_label.pack(side = 'left')
		redrawables.append({
			'dependencies': [
				lambda: get_actuator_position_text(state),
				lambda: nonpersistent['actuator_has_calibration_lock'],
			],
			'redraw': lambda: actuator_position_label.config(
				text = get_actuator_position_text(state),
				state = (
					'disabled'
					if nonpersistent['actuator_has_calibration_lock']
					else 'normal'
				),
			),
		})
		
		actuator_home_button = ttk.Button(
			main_grid,
			text = 'Home the actuator',
			command = lambda: Timer(0, home_the_actuator, [state]).start(),
		)
		actuator_home_button.grid(
			row = 0,
			column = 1,
			sticky = 'w',
			padx = main_cell_pad_x,
			pady = main_cell_pad_y,
		)
		redrawables.append({
			'dependencies': [
				lambda: nonpersistent['actuator_has_calibration_lock'],
			],
			'redraw': lambda: actuator_home_button.config(
				state = (
					'disabled'
					if nonpersistent['actuator_has_calibration_lock']
					else 'normal'
				),
			),
		})
		
	
	for i, distance in enumerate(ACTUATOR_HANDWHEEL_OPTIONS):
		row = 1 + i
		
		retract_button = ttk.Button(
			main_grid,
			text = f'Retract actuator {distance} mm',
			command = lambda distance=distance: (
				
			)
		)
		retract_button.grid(
			row = row,
			column = 0,
			sticky = 'e',
			padx = main_cell_pad_x,
			pady = main_cell_pad_y,
		)
		extend_button = ttk.Button(
			main_grid,
			text = f'Extend actuator {distance} mm',
			command = lambda distance=distance: None,
		)
		extend_button.grid(
			row = row,
			column = 1,
			sticky = 'w',
			padx = main_cell_pad_x,
			pady = main_cell_pad_y,
		)
		
		for handwheel_button in [retract_button, extend_button]:
			redrawables.append({
				'dependencies': [
					lambda: state['actuator_position_mm'],
					lambda: nonpersistent['actuator_has_calibration_lock'],
				],
				'redraw': lambda handwheel_button=handwheel_button: (
					handwheel_button.config(state = (
						'disabled'
						if (
							state['actuator_position_mm'] == None
							or nonpersistent['actuator_has_calibration_lock']
						)
						else 'normal'
					)),
				),
			})
	
	ttk.Label(main_grid).grid(row = 1 + len(ACTUATOR_HANDWHEEL_OPTIONS))
	
	for syringe_number in get_args(SyringeNumber):
		row = 1 + len(ACTUATOR_HANDWHEEL_OPTIONS) + syringe_number
		
		left_side_container = ttk.Frame(main_grid)
		left_side_container.grid(
			row = row,
			column = 0,
			sticky = 'e',
			padx = main_cell_pad_x,
			pady = main_cell_pad_y,
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
			main_grid,
			text = f'Record actuator tip as plunger {syringe_number}\'s position',
			state = 'disabled',
			command = lambda syringe_number=syringe_number: set_value(
				state['plunger_positions_mm'],
				str(syringe_number),
				state['actuator_position_mm'],
			),
		)
		record_button.grid(
			row = row,
			column = 1,
			sticky = 'w',
			padx = main_cell_pad_x,
			pady = main_cell_pad_y,
		)
		redrawables.append({
			'dependencies': [
				lambda: state['actuator_position_mm'],
				lambda: nonpersistent['actuator_has_calibration_lock'],
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
	
	# todo: buttons to certify the selected syringe (they only unlock after the
	# plunger positions are calibrated)

	ttk.Label(outermost).pack()
	
	ttk.Button(
		outermost,
		text = 'Close',
		command = lambda: close_calibration_gui(state),
	).pack()

def get_actuator_position_text(state: GlobalState) -> str:
	default = '⚠️ Unknown'
	return (
		'Homing...'
		if state['nonpersistent']['actuator_has_calibration_lock'] == True
		else
			default
			if state['actuator_position_mm'] == None
			else f'{state['actuator_position_mm']} mm'
	).rjust(len(default))

def get_plunger_position_text(
	state: GlobalState,
	syringe_number: SyringeNumber
) -> str:
	default = '⚠️ Unknown'
	return (
		default
		if str(syringe_number) not in state['plunger_positions_mm']
		else f'{state['plunger_positions_mm'][str(syringe_number)]} mm'
	).rjust(len(default))

def close_calibration_gui(state: GlobalState):
	modal = state['nonpersistent']['modal']
	if modal == None:
		raise Exception('close_calibration_gui: modal == None')
	if not calibration_is_complete(state) and messagebox.askokcancel(
		message = 'Calibration incomplete',
		detail = 'Changes will not be applied.',
	) == False:
		return
	
	state['nonpersistent']['modal_redrawables'] = []
	state['nonpersistent']['modal_dependency_cache'] = {}
	state['nonpersistent']['modal'] = None
	modal.destroy()

def toggle_processing_with_warning(state: GlobalState):
	if state['nonpersistent']['processing_enabled'] == True:
		state['nonpersistent']['processing_enabled'] = False
	elif messagebox.askokcancel(
		message = 'Careful!',
		detail = f"""Are these calibration values correct? If they're wrong, the bioprint hardware will likely crash and damage itself.

Selected syringe: {state['selected_syringe']}
Actuator position: {state['actuator_position_mm']} mm extended

""" + ''.join(f"""Plunger {i} position: {
	stringify_primitive(state['plunger_positions_mm'][str(i)])
} mm\n"""
for i in get_args(SyringeNumber)
) + '(all measured from actuator home)'
	) and messagebox.askokcancel(
		message = 'Really start processing?'
	):
		state['nonpersistent']['processing_enabled'] = True
