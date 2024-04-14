from types import SimpleNamespace
from state import GlobalState, Binary
from typing import cast

VALID_IO_PINS = {
	         8, 10, 12,     16, 18,     22, 24, 26,         32,     36, 38, 40,
	 3,  5,  7,     11, 13, 15,     19, 21, 23,         29, 31, 33, 35, 37,
}

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

def flip_binary(value: Binary) -> Binary:
	return cast(Binary, +(not value))

def read_pin(state: GlobalState, pin_label: str) -> Binary:
	if not pin_label in state['pins']:
		raise Exception(f'Tried to read from unknown pin {pin_label}')
	pin = state['pins'][pin_label]
	
	if pin['type'] == 'input':
		return cast(Binary, +GPIO.input(pin['number']))
	elif pin['type'] == 'output':
		if pin['value'] == None:
			raise Exception(f'No value found for output pin {pin_label}')
		return pin['value']
	else:
		raise

def write_pin(state: GlobalState, pin_label: str, value: Binary):
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

def setup_pins(state: GlobalState):
	GPIO.setmode(GPIO.BOARD)
	for pin_label, pin in state['pins'].items():
		if not pin['number'] in VALID_IO_PINS:
			raise Exception(f'Unknown pin number {pin['number']} in setup_pins')
		if pin['type'] == 'input':
			GPIO.setup(pin['number'], GPIO.IN)
		elif pin['type'] == 'output':
			GPIO.setup(pin['number'], GPIO.OUT)
			pin['value'] = 0
			GPIO.output(pin['number'], pin['value'])
		else:
			raise Exception(f'Unknown pin type {pin['type']} in setup_pins')
