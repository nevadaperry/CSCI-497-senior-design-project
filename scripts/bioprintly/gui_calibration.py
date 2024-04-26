from typing import get_args
from pins import retract_actuator_fully
from util import set_value, maximize_tk_window
from state import GlobalState, SyringeNumber
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
	
	actuator_row = ttk.Frame(outermost)
	actuator_row.pack()
	ttk.Label(
		actuator_row,
		text = f'Actuator position:'
	).pack(side = 'left')
	actuator_position_label = ttk.Label(
		actuator_row,
		text = get_actuator_position_text(state),
		font = 'TkFixedFont'
	)
	actuator_position_label.pack(side = 'left')
	ttk.Button(
		actuator_row,
		text = 'Home the actuator',
		command = lambda: retract_actuator_fully(state),
	).pack(side = 'left')
	redrawables.append({
		'dependencies': [
			lambda: state['actuator_position_mm']
		],
		'redraw': lambda: plunger_position_label.config(
			text = get_actuator_position_text(state)
		),
	})
	
	# todo: handwheel buttons
	
	for syringe_number in get_args(SyringeNumber):
		syringe_row = ttk.Frame(outermost)
		syringe_row.pack()
		ttk.Label(
			syringe_row,
			text = f'Syringe {syringe_number}\'s plunger position:'
		).pack(side = 'left')
		plunger_position_label = ttk.Label(
			syringe_row,
			text = get_plunger_position_text(state, syringe_number),
			font = 'TkFixedFont'
		)
		plunger_position_label.pack(side = 'left')
		
		record_button = ttk.Button(
			syringe_row,
			text = f'Record actuator tip position as plunger position',
			state = 'disabled',
			command = lambda syringe_number=syringe_number: set_value(
				state['plunger_positions_mm'],
				syringe_number,
				state['actuator_position_mm'],
			),
		)
		record_button.pack(side = 'left')
		
		redrawables.append({
			'dependencies': [
				lambda: state['plunger_positions_mm']
			],
			'redraw': lambda syringe_number=syringe_number: (
				plunger_position_label.config(
					text = get_plunger_position_text(state, syringe_number)
				),
			),
		})
		redrawables.append({
			'dependencies': [
				lambda: state['actuator_position_mm']
			],
			'redraw': lambda record_button=record_button: (
				record_button.config(state = (
					'disabled'
					if state['actuator_position_mm'] == None
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
		'⚠️ Unknown'
		if state['actuator_position_mm'] == None
		else f'{state['actuator_position_mm']} mm'
	)

def get_plunger_position_text(state: GlobalState, number: SyringeNumber) -> str:
	return (
		'⚠️ Unknown'
		if number not in state['plunger_positions_mm']
		else f'{state['plunger_positions_mm'][number]} mm'
	)

def calibration_is_complete(state: GlobalState) -> bool:
	return state['selected_syringe'] != None and all(
		(number in state['plunger_positions_mm'])
		for number in get_args(SyringeNumber)
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
