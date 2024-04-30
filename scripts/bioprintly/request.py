import json
from state import establish_savefolder_path, Request, Response, CommandSpecifics
import sys
from time import sleep
from util import unix_time_ms

savefolder_path = establish_savefolder_path()
logfile = open(f'{savefolder_path}/request.log', 'a')
logfile.write('Invoked with argv: ' + str(sys.argv) + '\n')
logfile.close()

commands: CommandSpecifics = []
match sys.argv[1]:
	case 'M140':
		for i in [1, 2, 3, 4]:
			commands.append({
				'verb': 'Turn heating pad',
				'target_heating_pad': i,
				'on_or_off': 'On',
			})
	case 'T0':
		commands.append({ 'verb': 'Rotate', 'target_syringe': 1 })
	case 'T1':
		commands.append({ 'verb': 'Rotate', 'target_syringe': 2 })
	case 'T2':
		commands.append({ 'verb': 'Rotate', 'target_syringe': 3 })
	case 'T3':
		commands.append({ 'verb': 'Rotate', 'target_syringe': 4 })
	case 'G1':
		commands.append({
			'verb': 'Actuate',
			'relative_mm_required': 1,
		})
	case _:
		raise Exception(f'Unknown G-code {argv[1]} in bioprintly/request.py')

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

def sleep_briefly():
	sleep(0.1)

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
