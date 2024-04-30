import json
from state import GlobalState, Request, Response, CommandSpecifics, enqueue_command
from time import sleep
from typing import List
from util import unix_time_ms

def sleep_briefly():
	sleep(0.1)

def handle_requests_repeatedly(state: GlobalState):
	savefolder_path = state['nonpersistent']['savefolder_path']
	while state['nonpersistent']['shutting_down'] == False:
		try:
			request: Request = json.load(open(
				f"{savefolder_path}/request.json",
				'r',
			))
		except:
			sleep_briefly()
			continue

		if request['timestamp'] > state['request_handling_watermark']:
			await_completion(state, request['commands'])
			state['request_handling_watermark'] = request['timestamp']
			response: Response = {
				'completed_request_timestamp': request['timestamp'],
			}
			json.dump(
				response,
				open(f'{savefolder_path}/response.json', 'w'),
				indent = '\t',
			)
		
		sleep_briefly()

def await_completion(state, commands: List[CommandSpecifics]):
	caboose_ordinal = 0
	for command in commands:
		caboose_ordinal = enqueue_command(state, 'Klipper', command)

	while state['nonpersistent']['shutting_down'] == False:
		if command_with_ordinal_is_complete(state, caboose_ordinal):
			break
		sleep_briefly()

def command_with_ordinal_is_complete(state, target_ordinal: int) -> bool:
	for finished_command in reversed(state['command_history']):
		if finished_command['ordinal'] < target_ordinal:
			return False
		elif finished_command['ordinal'] == target_ordinal:
			return True
	return False
