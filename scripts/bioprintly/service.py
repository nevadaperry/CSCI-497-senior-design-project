from pins import read_pin, write_pin
from state import GlobalState, save_state_to_disk
from time import sleep
from util import flip_bit, direction, time_ms

def run_service(state: GlobalState):
	while state['gui_on'] == True:
		state['service_loop_measured_delta'] = \
			time_ms() - state['service_loop_last_start']
		state['service_loop_last_start'] = time_ms()
		
		if state['service_on'] == True:
			process_commands(state)
		
		sleep(max(0,
			state['service_loop_interval'] - \
				(time_ms() - state['service_loop_last_start'])
		) / 1e3)

def process_commands(state: GlobalState):
	if len(state['command_queue']) == 0:
		return
	
	active_command = state['command_queue'][0]
	if not 'started_at' in active_command:
		active_command['started_at'] = time_ms()
	
	specifics = active_command['specifics']
	match specifics['verb']:
		case 'Rotate':
			if \
				not 'direction' in specifics or \
				not 'half_steps_remaining' in specifics \
			:
				raw_steps_required = \
					(specifics['target_syringe'] - state['selected_syringe']) \
					* state['rotator_steps_equivalent_to_90_degrees']
				specifics['direction'] = direction(raw_steps_required)
				specifics['half_steps_remaining'] = 2 * abs(raw_steps_required)
			
			if specifics['half_steps_remaining'] == 0:
				state['selected_syringe'] = specifics['target_syringe']
				finish_active_task(state)
				return
			write_pin(state, 'rotator_direction', specifics['direction'])
			write_pin(state, 'rotator_step', flip_bit(
				read_pin(state, 'rotator_step')
			))
			specifics['half_steps_remaining'] -= 1
		
		case 'Actuate':
			if not 'half_steps_remaining' in specifics:
				specifics['half_steps_remaining'] = \
					2 * specifics['steps needed total']
			
			if specifics['half_steps_remaining'] == 0:
				finish_active_task(state)
				return
			write_pin(state, 'actuator_direction', specifics['direction'])
			write_pin(state, 'actuator_step', flip_bit(
				read_pin(state, 'actuator_step')
			))
			specifics['half_steps_remaining'] -= 1

def finish_active_task(state: GlobalState):
	state['command_queue'][0]['finished_at'] = time_ms()
	state['command_history'].append(state['command_queue'][0])
	state['command_queue'] = state['command_queue'][1:]
	save_state_to_disk(state)
