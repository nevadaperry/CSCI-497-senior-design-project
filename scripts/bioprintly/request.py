from state import establish_savefolder_path, Request, Response
import sys
from time import sleep
from util import unix_time_ms

savefolder_path = establish_savefolder_path()
logfile = open(f'{savefolder_path}/request.log', 'a')
logfile.write('Invoked with argv: ' + str(sys.argv) + '\n')
logfile.close()

commands: CommandSpecifics = []
match argv[1]:
	case 'M140':
	case 'T0':
	case 'T1':
	case 'T2':
	case 'T3':
	case 'G1':
	case _:
		raise Exception(f'Unknown G-code {argv[1]} in bioprintly/request.py')
request_timestamp = unix_time_ms()
request: Request = {
	'timestamp': request_timestamp,
	'commands': commands,
}
json.dump(
	request,
	f'{savefolder_path}/request.json',
	indent = '\t',
)

def sleep_briefly():
	sleep(0.1)

while True:
	try:
		response: Response = json.load(open(
			f'{savefolder_path}/response.json'),
			'r',
		))
	except:
		sleep_briefly()
		continue

	if response['finished_request_timestamp'] == request_timestamp:
		break

	sleep_briefly()
