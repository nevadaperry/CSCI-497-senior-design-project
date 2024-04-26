from tkinter import messagebox
from typing import cast
from pins import direction, flip_bit, read_pin, write_pin, zero_out_pins
from state import FinishedCommand, GlobalState, save_state_to_disk
from time import sleep
from util import unix_time_ms

def run_service(state: GlobalState):
	nonpersistent = state['nonpersistent']
	while nonpersistent['shutting_down'] == False:
		nonpersistent['processing_loop_measured_delta'] = (
			unix_time_ms() - nonpersistent['processing_loop_last_start']
		)
		nonpersistent['processing_loop_last_start'] = unix_time_ms()
		
		if nonpersistent['processing_enabled'] == True:
			process_commands(state)
		else:
			zero_out_pins(state)
		
		if unix_time_ms() >= nonpersistent['savefile_last_write'] + 2000:
			save_state_to_disk(state)
		
		sleep(max(0,
			nonpersistent['processing_loop_interval']
			- (unix_time_ms() - nonpersistent['processing_loop_last_start'])
		) / 1e3)
	
	zero_out_pins(state)
	save_state_to_disk(state)

def process_commands(state: GlobalState):
	nonpersistent = state['nonpersistent']
	
	if state['selected_syringe'] == None:
		nonpersistent['processing_enabled'] = False
		messagebox.showwarning(
			message = 'Syringe position is unknown',
			detail = 'Please click the calibrate button at the top of the UI.',
		)
		return
	if state['actuator_position_mm'] == None:
		nonpersistent['processing_enabled'] = False
		messagebox.showwarning(
			message = 'Actuator position is unknown',
			detail = 'Please click the calibrate button at the top of the UI.',
		)
		return
	
	if len(state['command_queue']) == 0:
		return
	
	active_command = state['command_queue'][0]
	if not 'started_at' in active_command:
		active_command['started_at'] = unix_time_ms()
	
	specifics = active_command['specifics']
	match specifics['verb']:
		case 'Rotate':
			if (
				not 'direction' in specifics or
				not 'half_steps_remaining' in specifics
			):
				raw_steps_required = (
					specifics['target_syringe']
					- state['selected_syringe']
				) * nonpersistent['rotator_steps_equivalent_to_90_degrees']
				
				specifics['direction'] = direction(raw_steps_required)
				specifics['half_steps_remaining'] = 2 * abs(raw_steps_required)
			
			if specifics['half_steps_remaining'] == 0:
				state['selected_syringe'] = (
					specifics['target_syringe']
				)
				finish_active_task(state)
				return
			
			write_pin(state, 'rotator_direction', specifics['direction'])
			write_pin(state, 'rotator_step', flip_bit(
				read_pin(state, 'rotator_step')
			))
			specifics['half_steps_remaining'] -= 1
		
		case 'Actuate':
			if not 'travel_mm_remaining' in specifics:
				specifics['travel_mm_remaining'] = (
					specifics['travel_mm_needed_total']
				)
			
			target_pin_name = (
				'actuator_extend'
				if specifics['direction'] == 1
				else 'actuator_retract'
			)
			
			if specifics['travel_mm_remaining'] <= 0:
				write_pin(state, 'actuator_retract', 0)
				write_pin(state, 'actuator_extend', 0)
				finish_active_task(state)
				return
			
			write_pin(state, target_pin_name, specifics['direction'])
			specifics['travel_mm_remaining'] -= (
				nonpersistent['processing_loop_measured_delta'] * \
				nonpersistent['actuator_travel_mm_per_ms']
			)

def finish_active_task(state: GlobalState):
	state['command_queue'][0]['finished_at'] = unix_time_ms()
	state['command_history'].append(
		cast(FinishedCommand, state['command_queue'][0])
	)
	state['command_queue'] = state['command_queue'][1:]
	save_state_to_disk(state)
