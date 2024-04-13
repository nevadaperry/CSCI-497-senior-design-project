from pins import flip_binary, read_pin, write_pin
from state import GlobalState, save_state_to_disk, time_ms

def finish_active_task(state: GlobalState):
	state['command_queue'][0]['finished_at'] = time_ms()
	state['command_history'].append(state['command_queue'][0])
	state['command_queue'] = state['command_queue'][1:]
	save_state_to_disk(state)

def process_commands(state: GlobalState):
	if len(state['command_queue']) == 0:
		return
	
	active_command = state['command_queue'][0]
	if active_command['started_at'] == None:
		active_command['started_at'] = time_ms()
	save_state_to_disk(state)
	
	specifics = active_command['specifics']
	match specifics['verb']:
		case 'Rotate':
			if specifics['half_steps_remaining'] == 0:
				finish_active_task(state)
				return
			write_pin(state, 'rotator_direction', 0)
			write_pin(state, 'rotator_step', flip_binary(
				read_pin(state, 'rotator_step')
			))
			specifics['half_steps_remaining'] -= 1
		case 'Actuate':
			if specifics['half_steps_remaining'] == 0:
				finish_active_task(state)
				return
			write_pin(state, 'actuator_direction', 0)
			write_pin(state, 'actuator_step', flip_binary(
				read_pin(state, 'actuator_step')
			))
			specifics['half_steps_remaining'] -= 1
