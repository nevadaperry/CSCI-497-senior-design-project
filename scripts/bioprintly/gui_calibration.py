from threading import Timer
from typing import get_args
from pins import home_the_actuator
from util import set_value, maximize_tk_window
from state import GlobalState, SyringeNumber, save_state_to_disk
from tkinter import Toplevel, messagebox, ttk

def build_calibration_gui(state: GlobalState):
	modal = state['nonpersistent']['modal'] = Toplevel()
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
	
	redrawables = state['nonpersistent']['modal_redrawables']
	
	status_grid = ttk.Frame(outermost)
	status_grid.pack()
	status_grid.columnconfigure(0, weight = 1, uniform = 'status_grid')
	status_grid.columnconfigure(1, weight = 1, uniform = 'status_grid')
	status_grid.columnconfigure(2, weight = 1, uniform = 'status_grid')
	
	ttk.Label(
		status_grid,
		text = f'Actuator position:'
	).grid(row = 0, column = 0, sticky = 'e')
	actuator_position_label = ttk.Label(
		status_grid,
		text = get_actuator_position_text(state),
		font = 'TkFixedFont'
	)
	actuator_position_label.grid(row = 0, column = 1)
	ttk.Button(
		status_grid,
		text = 'Home the actuator',
		command = lambda: Timer(0, home_the_actuator, [state]).start(),
	).grid(row = 0, column = 2, sticky = 'w')
	redrawables.append({
		'dependencies': [
			lambda: get_actuator_position_text(state),
		],
		'redraw': lambda: actuator_position_label.config(
			text = get_actuator_position_text(state)
		),
	})
	
	# todo: handwheel buttons
	# todo: buttons to certify the selected syringe (they only unlock after the
	# plunger positions are calibrated)
	
	for syringe_number in get_args(SyringeNumber):
		ttk.Label(
			status_grid,
			text = f'Syringe {syringe_number}\'s plunger position:'
		).grid(row = syringe_number, column = 0, sticky = 'e')
		plunger_position_label = ttk.Label(
			status_grid,
			text = get_plunger_position_text(state, syringe_number),
			font = 'TkFixedFont'
		)
		plunger_position_label.grid(row = syringe_number, column = 1)
		
		record_button = ttk.Button(
			status_grid,
			text = f'Record actuator tip position as plunger position',
			state = 'disabled',
			command = lambda syringe_number=syringe_number: set_value(
				state['plunger_positions_mm'],
				str(syringe_number),
				state['actuator_position_mm'],
			),
		)
		record_button.grid(row = syringe_number, column = 2, sticky = 'w')
		
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
		redrawables.append({
			'dependencies': [
				lambda: state['actuator_position_mm'],
				lambda: state['nonpersistent']['actuator_is_homing'],
			],
			'redraw': lambda record_button=record_button: (
				record_button.config(state = (
					'disabled'
					if (
						state['actuator_position_mm'] == None
						or state['nonpersistent']['actuator_is_homing'] == True
					)
					else 'normal'
				)),
			),
		})
	
	ttk.Button(
		outermost,
		text = 'Close',
		command = lambda: close_calibration_gui(state),
	).pack()

def get_actuator_position_text(state: GlobalState) -> str:
	return (
		'Homing...'
		if state['nonpersistent']['actuator_is_homing'] == True
		else
			'⚠️ Unknown'
			if state['actuator_position_mm'] == None
			else f'{state['actuator_position_mm']} mm'
	)

def get_plunger_position_text(
	state: GlobalState,
	syringe_number: SyringeNumber
) -> str:
	return (
		'⚠️ Unknown'
		if str(syringe_number) not in state['plunger_positions_mm']
		else f'{state['plunger_positions_mm'][str(syringe_number)]} mm'
	)

def calibration_is_complete(state: GlobalState) -> bool:
	return (
		state['selected_syringe'] != None
		and state['actuator_position_mm'] != None
		and all(
			str(syringe_number) in state['plunger_positions_mm']
			for syringe_number in get_args(SyringeNumber)
		)
	)

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
