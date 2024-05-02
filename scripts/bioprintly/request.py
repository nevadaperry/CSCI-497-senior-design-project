import json
from typing import List, cast, get_args
from state import SyringeNumber, establish_savefolder_path, Request, Response, CommandSpecifics
import sys
from time import sleep
from util import unix_time_ms

def build_commands_for_g_code(g_code: str) -> List[CommandSpecifics]:
	if g_code == 'M140':
		for i in range(2, len(sys.argv)):
			if sys.argv[i][0] == 'S':
				on_or_off = 'Off' if float(sys.argv[i][1:]) == 0.0 else 'On'
				break
		else:
			return []
		commands = []
		for i in get_args(SyringeNumber):
			commands.append({
				'verb': 'Turn heating pad',
				'target_heating_pad': i,
				'on_or_off': on_or_off,
			})
		commands.append({
			'verb': 'Turn UV light',
			'target_uv_light': 'Current one',
			'on_or_off': on_or_off
		})
		return commands
	elif g_code[0] == 'T':
		target_syringe = 1 + int(g_code[1:])
		if not target_syringe in get_args(SyringeNumber):
			raise Exception(f'T-code {g_code} out of range in bioprintly/request.py')
		target_syringe = cast(SyringeNumber, target_syringe)
		return [
			{ 'verb': 'Actuate', 'unscaled_mm_required': 'Go home' },
			{
				'verb': 'Turn UV light',
				'target_uv_light': 'Current one',
				'on_or_off': 'Off'
			},
			{
				'verb': 'Rotate',
				'target_syringe': target_syringe },
			{
				'verb': 'Turn UV light',
				'target_uv_light': 'Current one',
				'on_or_off': 'On'
			},
			{
				'verb': 'Actuate',
				'unscaled_mm_required': 'Go to plunger flange'
			},
		]
	elif g_code == 'G1':
		for i in range(2, len(sys.argv)):
			if sys.argv[i][0] == 'E':
				unscaled_mm_required = float(sys.argv[i][1:])
				break
		else:
			return []
		return [{
			'verb': 'Actuate',
			'unscaled_mm_required': unscaled_mm_required,
		}]
	else:
		raise Exception(f'Unknown G-code {sys.argv[1]} in bioprintly/request.py')

def sleep_briefly():
	sleep(0.2)

def submit_request_to_bioprintly(
	savefolder_path: str,
	commands: List[CommandSpecifics],
):
	request_timestamp = unix_time_ms()
	request: Request = {
		'timestamp': request_timestamp,
		'commands': commands,
	}
	json.dump(
		request,
		open(f'{savefolder_path}/request.json', 'w'),
		indent = '\t',
	)

	while True:
		try:
			response: Response = json.load(open(
				f'{savefolder_path}/response.json',
				'r',
			))
		except:
			sleep_briefly()
			continue

		if response['completed_request_timestamp'] == request_timestamp:
			break

		sleep_briefly()

def handle_request_from_klipper():
	savefolder_path = establish_savefolder_path()
	logfile = open(f'{savefolder_path}/request.log', 'a')
	logfile.write('Invoked with argv: ' + str(sys.argv) + '\n')
	commands = build_commands_for_g_code(sys.argv[1])
	logfile.write(f'Built and submitting commands {json.dumps(commands)}')
	logfile.close()
	if len(commands) > 0:
		submit_request_to_bioprintly(savefolder_path, commands)

handle_request_from_klipper()
