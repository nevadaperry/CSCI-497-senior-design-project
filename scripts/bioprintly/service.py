from tkinter import messagebox
from typing import cast
from pins import direction, flip_bit, read_pin, write_pin, zero_out_pins
from state import FinishedCommand, GlobalState, save_state_to_disk
from time import sleep
from util import unix_time_ms

def run_service(state: GlobalState):
	while state['nonpersistent']['shutting_down'] == False:
		state['processing_loop_measured_delta'] = (
			unix_time_ms() - state['processing_loop_last_start']
		)
		state['processing_loop_last_start'] = unix_time_ms()
		
		if state['nonpersistent']['processing_enabled'] == True:
			process_commands(state)
		
		sleep(max(0,
			state['processing_loop_interval']
				- (unix_time_ms() - state['processing_loop_last_start'])
		) / 1e3)
	
	save_state_to_disk(state)
	zero_out_pins(state)

def process_commands(state: GlobalState):
	if state['nonpersistent']['selected_syringe'] == None:
		state['nonpersistent']['processing_enabled'] = False
		messagebox.showwarning(
			message = 'Barrel has not been aligned yet for this run.',
			detail = 'Please rotate it by hand to the syringe marked #1, then click the certify alignment button.',
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
					- state['nonpersistent']['selected_syringe']
				) * state['rotator_steps_equivalent_to_90_degrees']
				
				specifics['direction'] = direction(raw_steps_required)
				specifics['half_steps_remaining'] = 2 * abs(raw_steps_required)
			
			if specifics['half_steps_remaining'] == 0:
				state['nonpersistent']['selected_syringe'] = (
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
			if not 'half_steps_remaining' in specifics:
				specifics['half_steps_remaining'] = (
					2 * specifics['steps_needed_total']
				)
			
			if specifics['half_steps_remaining'] == 0:
				finish_active_task(state)
				return
			
			write_pin(state, 'actuator_direction', specifics['direction'])
			write_pin(state, 'actuator_step', flip_bit(
				read_pin(state, 'actuator_step')
			))
			specifics['half_steps_remaining'] -= 1

def finish_active_task(state: GlobalState):
	state['command_queue'][0]['finished_at'] = unix_time_ms()
	state['command_history'].append(
		cast(FinishedCommand, state['command_queue'][0])
	)
	state['command_queue'] = state['command_queue'][1:]
	save_state_to_disk(state)
