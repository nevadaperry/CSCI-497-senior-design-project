import json
from state import GlobalState, Request, Response, CommandSpecifics, enqueue_command
from time import sleep
from typing import List
from util import unix_time_ms

def sleep_briefly():
	sleep(0.2)

def handle_requests_repeatedly(state: GlobalState):
	savefolder_path = state['nonpersistent']['savefolder_path']
	while state['nonpersistent']['shutting_down'] == False:
		try:
			request: Request = json.load(open(
				f"{savefolder_path}/request.json",
				'r',
			))
			if request['timestamp'] > state['request_handling_watermark']:
				print(f'Received request from Klipper: {json.dumps(request)}')

				caboose_ordinal = None
				for command in commands:
					caboose_ordinal = enqueue_command(state, 'Klipper', command)
				state['request_handling_caboose_ordinal'] = caboose_ordinal
				state['request_handling_watermark'] = request['timestamp']
		except:
			pass

		if command_with_caboose_ordinal_is_complete(state):
			response: Response = {
				'completed_request_timestamp': request['timestamp'],
			}
			json.dump(
				response,
				open(f'{savefolder_path}/response.json', 'w'),
				indent = '\t',
			)
			state['request_handling_caboose_ordinal'] = None
			break
		
		sleep_briefly()

def await_completion(state, commands: List[CommandSpecifics]):

def command_with_caboose_ordinal_is_complete(state) -> bool:
	caboose_ordinal = state['request_handling_caboose_ordinal']
	if caboose_ordinal == None:
		return False
	for finished_command in reversed(state['command_history']):
		if finished_command['ordinal'] < caboose_ordinal:
			return False
		elif finished_command['ordinal'] == caboose_ordinal:
			return True
	return False
