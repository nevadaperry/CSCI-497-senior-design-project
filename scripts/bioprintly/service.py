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
		
		sleep(max(0,
			nonpersistent['processing_loop_interval']
				- (unix_time_ms() - nonpersistent['processing_loop_last_start'])
		) / 1e3)
	
	save_state_to_disk(state)
	zero_out_pins(state)

def process_commands(state: GlobalState):
	nonpersistent = state['nonpersistent']
	
	if nonpersistent['selected_syringe'] == None:
		nonpersistent['processing_enabled'] = False
		messagebox.showwarning(
			message = 'Calibration has not been completed yet for this run.',
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
					- nonpersistent['selected_syringe']
				) * nonpersistent['rotator_steps_equivalent_to_90_degrees']
				
				specifics['direction'] = direction(raw_steps_required)
				specifics['half_steps_remaining'] = 2 * abs(raw_steps_required)
			
			if specifics['half_steps_remaining'] == 0:
				nonpersistent['selected_syringe'] = (
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
			if not 'milliseconds_remaining' in specifics:
				specifics['milliseconds_remaining'] = (
					2 * specifics['milliseconds_needed_total']
				)
			
			if specifics['milliseconds_remaining'] == 0:
				finish_active_task(state)
				return
			
			write_pin(state, 'actuator_direction', specifics['direction'])
			write_pin(state, 'actuator_step', flip_bit(
				read_pin(state, 'actuator_step')
			))
			specifics['milliseconds_remaining'] -= 1

def finish_active_task(state: GlobalState):
	state['command_queue'][0]['finished_at'] = unix_time_ms()
	state['command_history'].append(
		cast(FinishedCommand, state['command_queue'][0])
	)
	state['command_queue'] = state['command_queue'][1:]
	save_state_to_disk(state)
