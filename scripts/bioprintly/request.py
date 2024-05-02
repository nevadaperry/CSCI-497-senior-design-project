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
g_code = sys.argv[1]
if g_code == 'M140':
	for i in range(2, len(sys.argv)):
		if sys.argv[i][0] == 'S':
			on_or_off = 'Off' if float(sys.argv[i][1:]) == 0.0 else 'On'
			break
	else:
		return
	for i in [1, 2, 3, 4]:
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
elif g_code[0] == 'T':
	commands += [
		{ 'verb': 'Actuate', 'unscaled_mm_required': 'Go home' },
		{
			'verb': 'Turn UV light',
			'target_uv_light': 'Current one',
			'on_or_off': 'Off'
		},
		{ 'verb': 'Rotate', 'target_syringe': 1 + int(g_code[1:]) },
		{
			'verb': 'Turn UV light',
			'target_uv_light': 'Current one',
			'on_or_off': 'On'
		},
		{ 'verb': 'Actuate', 'unscaled_mm_required': 'Go to plunger flange' },
	]
elif g_code == 'G1':
	for i in range(2, len(sys.argv)):
		if sys.argv[i][0] == 'E':
			unscaled_mm_required = float(sys.argv[i][1:])
			break
	else:
		return
	commands.append({
		'verb': 'Actuate',
		'unscaled_mm_required': unscaled_mm_required,
	})
else:
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
