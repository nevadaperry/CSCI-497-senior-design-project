from state import GlobalState, PinNumber
from types import SimpleNamespace
from typing import cast, get_args
from util import Bit

try:
	GPIO = __import__('RPi').GPIO
except:
	gpio_stub = ({
		'setmode': lambda mode: None,
		'BOARD': 0,
		'setup': lambda pin, type: None,
		'IN': 0,
		'OUT': 1,
		'input': lambda pin: 0,
		'output': lambda pin, value: None,
	})
	GPIO = SimpleNamespace(**gpio_stub)

def setup_pins(state: GlobalState):
	'''Can be rerun idempotently'''
	GPIO.setmode(GPIO.BOARD)
	# Turn off all pins in case any were unmapped, or left turned on externally
	for pin_number in get_args(PinNumber):
		GPIO.setup(pin_number, GPIO.OUT)
		GPIO.output(pin_number, 0)
	
	for pin_label, pin in state['pins'].items():
		if not pin['number'] in get_args(PinNumber):
			raise Exception(f'Unknown pin number {pin['number']} in setup_pins')
		if pin['type'] == 'input':
			GPIO.setup(pin['number'], GPIO.IN)
		elif pin['type'] == 'output':
			GPIO.setup(pin['number'], GPIO.OUT)
			pin['value'] = 0
		else:
			raise Exception(f'Unknown pin type {pin['type']} in setup_pins')

def read_pin(state: GlobalState, pin_label: str) -> Bit:
	if not pin_label in state['pins']:
		raise Exception(f'Tried to read from unknown pin {pin_label}')
	pin = state['pins'][pin_label]
	
	if pin['type'] == 'input':
		return cast(Bit, +GPIO.input(pin['number']))
	elif pin['type'] == 'output':
		if not 'value' in pin:
			raise Exception(f'No value found for output pin {pin_label}')
		return pin['value']
	else:
		raise

def write_pin(state: GlobalState, pin_label: str, value: Bit):
	if not pin_label in state['pins']:
		raise Exception(f'Tried to read from unknown pin {pin_label}')
	pin = state['pins'][pin_label]
	if pin['type'] != 'output':
		raise Exception(f'Tried to write to non-output pin {pin_label}')
	
	pin['value'] = value
	GPIO.output(pin['number'], value)

def zero_out_pins_and_exit(state: GlobalState):
	for pin_label, pin in state['pins'].items():
		write_pin(state, pin_label, 0)
	exit()
