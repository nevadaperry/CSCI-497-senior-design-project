from tkinter import messagebox
from typing import Any, Callable, Dict, cast
from pins import flip_bit, read_pin, write_pin, zero_out_pins
from state import CommandActuate, CommandRotate, CommandSpecifics, CommandTurnHeatingPad, CommandTurnUvLight, EnqueuedCommand, FinishedCommand, GlobalState, NonPersistentState, SyringeNumber, on_off_string_to_bit, save_state_to_disk, calibration_is_complete
from time import sleep
from util import signum, this_action_would_put_it_further_away_from_target_than_it_is_now, unix_time_ms

def run_service(state: GlobalState):
	nonpersistent = state['nonpersistent']
	while nonpersistent['shutting_down'] == False:
		nonpersistent['processing_loop_measured_delta'] = (
			unix_time_ms() - nonpersistent['processing_loop_last_start']
		)
		nonpersistent['processing_loop_last_start'] = unix_time_ms()
		
		if nonpersistent['processing_enabled'] == True:
			process_commands(state)
		
		if unix_time_ms() >= nonpersistent['savefile_last_write'] + 2000:
			save_state_to_disk(state)
		
		sleep(max(0,
			nonpersistent['processing_loop_interval_ms']
			- (unix_time_ms() - nonpersistent['processing_loop_last_start'])
		) / 1e3)
	
	zero_out_pins(state)
	save_state_to_disk(state)

def process_commands(state: GlobalState):
	if not calibration_is_complete(state):
		state['nonpersistent']['processing_enabled'] = False
		messagebox.showwarning(
			message = 'Calibration is missing one or more values',
			detail = 'Please click the calibrate button at the top of the UI.',
		)
		return
	
	if len(state['command_queue']) == 0:
		return
	
	active_command = state['command_queue'][0]
	if not 'started_at' in active_command:
		active_command['started_at'] = unix_time_ms()
	
	specifics = active_command['specifics']
	processing_functions: Dict[
		str,
		Callable[[GlobalState, NonPersistentState, EnqueuedCommand, Any], None]
	] = {
		'Rotate': rotate_one_interval,
		'Actuate': actuate_one_interval,
		'Turn heating pad': turn_heating_pad,
		'Turn UV light': turn_uv_light,
	}
	if not specifics['verb'] in processing_functions:
		raise Exception(f"Tried to process unknown command {specifics['verb']}")
	
	processing_functions[specifics['verb']](
		state,
		state['nonpersistent'],
		active_command,
		specifics
	)

def finish_active_task(state: GlobalState):
	state['command_queue'][0]['finished_at'] = unix_time_ms()
	state['command_history'].append(
		cast(FinishedCommand, state['command_queue'][0])
	)
	state['command_history'] = state['command_history'][:50]
	state['command_queue'] = state['command_queue'][1:]
	save_state_to_disk(state)

def rotate_one_interval(
	state: GlobalState,
	nonpersistent: NonPersistentState,
	active_command: EnqueuedCommand,
	specifics: CommandRotate,
):
	if not 'relative_degrees_required' in specifics:
		specifics['relative_degrees_required'] = (
			specifics['target_syringe']
			- cast(SyringeNumber, state['current_syringe'])
		) * -90.0
	
	if not 'relative_degrees_traveled' in specifics:
		specifics['relative_degrees_traveled'] = 0.0
	
	expected_travel_degrees = (
		signum(specifics['relative_degrees_required'])
		# Stepper motor steps only count the rising edge
		* 0.5 * nonpersistent['rotator_degrees_per_step']
	)
	
	if (
		specifics['relative_degrees_required'] == 0.0
		or this_action_would_put_it_further_away_from_target_than_it_is_now(
			specifics['relative_degrees_traveled'],
			expected_travel_degrees,
			specifics['relative_degrees_required'],
		)
	):
		state['current_syringe'] = specifics['target_syringe']
		finish_active_task(state)
		return
	
	write_pin(state, 'rotator_direction', (
		0
		if specifics['relative_degrees_required'] >= 0
		else 1
	))
	write_pin(state, 'rotator_step', flip_bit(
		read_pin(state, 'rotator_step')
	))
	
	specifics['relative_degrees_traveled'] += expected_travel_degrees

def actuate_one_interval(
	state: GlobalState,
	nonpersistent: NonPersistentState,
	active_command: EnqueuedCommand,
	specifics: CommandActuate
):
	if not 'scaled_mm_required' in specifics:
		if specifics['unscaled_mm_required'] == 'Go home':
			specifics['scaled_mm_required'] = (
				cast(float, state['actuator_position_mm'])
				* (1 + nonpersistent['safety_margin'])
				* -1
			)
		else:
			specifics['scaled_mm_required'] = (
				cast(float, specifics['unscaled_mm_required'])
				* (
					nonpersistent['actuator_klipper_scaling_factor']
					if active_command['enqueued_by'] == 'Klipper'
					else 1.0
				)
			)
	if not 'scaled_mm_traveled' in specifics:
		specifics['scaled_mm_traveled'] = 0
	
	expected_travel_mm = (
		signum(specifics['scaled_mm_required'])
		* nonpersistent['actuator_travel_mm_per_ms']
		* nonpersistent['processing_loop_measured_delta']
	)
	
	if (
		specifics['scaled_mm_required'] == 0.0
		or this_action_would_put_it_further_away_from_target_than_it_is_now(
			specifics['scaled_mm_traveled'],
			expected_travel_mm,
			specifics['scaled_mm_required'],
		)
	):
		write_pin(state, 'actuator_retract', 0)
		write_pin(state, 'actuator_extend', 0)
		state['plunger_positions_mm'][str(state['current_syringe'])] = (
			cast(float, state['actuator_position_mm'])
		)
		finish_active_task(state)
		return
	
	if (
		cast(float, state['actuator_position_mm'])
		+ expected_travel_mm
	) > (
		nonpersistent['actuator_max_possible_extension_mm']
		* (1 - nonpersistent['safety_margin'])
	):
		nonpersistent['processing_enabled'] = False
		messagebox.showerror(
			message = 'Actuator has reached the maximum safe distance programmed. You may have run out of material in the current syringe.',
			detail = 'To continue, open the calibration window, home the actuator, and re-calibrate the current syringe to a position where it has more material.',
		)
		return
	
	if expected_travel_mm > 0:
		write_pin(state, 'actuator_extend', 1)
	else:
		write_pin(state, 'actuator_retract', 1)
	
	specifics['scaled_mm_traveled'] += expected_travel_mm
	state['actuator_position_mm'] = (
		cast(float, state['actuator_position_mm'])
		+ expected_travel_mm
	)

	if cast(float, state['actuator_position_mm']) < 0:
		state['actuator_position_mm'] = 0
		write_pin(state, 'actuator_retract', 0)
		write_pin(state, 'actuator_extend', 0)
		finish_active_task(state)
		return

def turn_heating_pad(
	state: GlobalState,
	nonpersistent: NonPersistentState,
	active_command: EnqueuedCommand,
	specifics: CommandTurnHeatingPad,
):
	target_heating_pad = (
		state['current_syringe']
		if specifics['target_heating_pad'] == 'Current one'
		else specifics['target_heating_pad']
	)
	write_pin(
		state,
		f'heating_pad_{target_heating_pad}',
		on_off_string_to_bit(specifics['on_or_off']),
	)
	finish_active_task(state)

def turn_uv_light(
	state: GlobalState,
	nonpersistent: NonPersistentState,
	active_command: EnqueuedCommand,
	specifics: CommandTurnUvLight
):
	target_uv_light = (
		state['current_syringe']
		if specifics['target_uv_light'] == 'Current one'
		else specifics['target_uv_light']
	)
	write_pin(
		state,
		f'uv_light_{target_uv_light}',
		on_off_string_to_bit(specifics['on_or_off']),
	)
	return
