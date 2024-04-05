import signal
from types import SimpleNamespace
from typing import Dict, Literal, TypedDict

gpio_available = False
if (gpio_available):
	import RPi.GPIO as GPIO
else:
	GPIO = ({
		'setmode': lambda mode: None,
		'BOARD': 0,
		'setup': lambda pin, type: None,
		'IN': 0,
		'OUT': 1,
		'input': lambda pin: 0,
		'output': lambda pin, value: None,
	})
	GPIO = SimpleNamespace(**GPIO)

valid_io_pins = {
	         8, 10, 12,     16, 18,     22, 24, 26,         32,     36, 38, 40,
	 3,  5,  7,     11, 13, 15,     19, 21, 23,         29, 31, 33, 35, 37,
}

class Pin(TypedDict):
	number: int
	type: Literal['input', 'output']
	value: Literal[0, 1]

pins: Dict[str, Pin] = {
	'rotator_step': { 'number': 3, 'type': 'output' },
	'rotator_direction': { 'number': 5, 'type': 'output' },
	'unused7': { 'number': 7, 'type': 'output' },
	'unused8': { 'number': 8, 'type': 'output' },
	'unused10': { 'number': 10, 'type': 'output' },
	'unused11': { 'number': 11, 'type': 'output' },
	'unused12': { 'number': 12, 'type': 'output' },
	'unused13': { 'number': 13, 'type': 'output' },
	'unused15': { 'number': 15, 'type': 'output' },
	'unused16': { 'number': 16, 'type': 'output' },
	'unused18': { 'number': 18, 'type': 'output' },
	'unused19': { 'number': 19, 'type': 'output' },
	'unused21': { 'number': 21, 'type': 'output' },
	'unused22': { 'number': 22, 'type': 'output' },
	'unused23': { 'number': 23, 'type': 'output' },
	'unused24': { 'number': 24, 'type': 'output' },
	'unused26': { 'number': 26, 'type': 'output' },
	'unused29': { 'number': 29, 'type': 'output' },
	'unused31': { 'number': 31, 'type': 'output' },
	'unused32': { 'number': 32, 'type': 'output' },
	'unused33': { 'number': 33, 'type': 'output' },
	'unused35': { 'number': 35, 'type': 'output' },
	'unused36': { 'number': 36, 'type': 'output' },
	'unused37': { 'number': 37, 'type': 'output' },
	'unused38': { 'number': 38, 'type': 'output' },
	'unused40': { 'number': 40, 'type': 'output' },
}

def read_pin(pin_label):
	if not pin_label in pins:
		raise Exception(f"Tried to read from unknown pin {pin_label}")
	pin = pins[pin_label]
	
	if pin['type'] == 'input':
		return GPIO.input(pin['number'])
	elif pin['type'] == 'output':
		value = pin['value']
		if not value:
			raise Exception(f"No value found for output pin {pin_label}")
		return value

def write_pin(pin_label, value):
	if not pin_label in pins:
		raise Exception(f"Tried to read from unknown pin {pin_label}")
	pin = pins[pin_label]
	if pin['type'] != 'output':
		raise Exception(f"Tried to write to non-output pin {pin_label}")
	
	pins[pin_label]['value'] = value
	GPIO.output(pins[pin_label], value)

def cleanup(a, b):
	for pin_label, pin in pins.items():
		write_pin(pin_label, 0)
	exit()

def setup_pins():
	GPIO.setmode(GPIO.BOARD)
	signal.signal(signal.SIGINT, cleanup)
	for pin_label, pin in pins.items():
		if pin['type'] == 'input':
			GPIO.setup(pin['number'], GPIO.IN)
		elif pin['type'] == 'output':
			GPIO.setup(pin['number'], GPIO.OUT)
			starting_value = 0
			GPIO.output(pin['number'], starting_value)
			pin['value'] = starting_value
		else:
			raise Exception(f"Unknown pin type {pin['type']} in setup_pins()")
