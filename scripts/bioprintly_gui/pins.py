from signal import SIGINT, signal
from types import SimpleNamespace
from typing import Dict, Literal, TypedDict, cast

GPIO_AVAILABLE = False
'''
Set this to False to test/debug this script on devices other than Raspberry Pi,
with all GPIO inputs reading 0 and all outputs having no effect.
'''
if (GPIO_AVAILABLE):
	import RPi.GPIO as GPIO # type: ignore
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

VALID_IO_PINS = {
	         8, 10, 12,     16, 18,     22, 24, 26,         32,     36, 38, 40,
	 3,  5,  7,     11, 13, 15,     19, 21, 23,         29, 31, 33, 35, 37,
}

Binary = Literal[0, 1]
class Pin(TypedDict):
	number: int
	type: Literal['input', 'output']
	value: Binary

def flip_binary(value: Binary) -> Binary:
	return cast(Binary, +(not value))

PINS: Dict[str, Pin] = {
	'rotator_step': { 'number': 3, 'type': 'output', 'value': 0 },
	'rotator_direction': { 'number': 5, 'type': 'output', 'value': 0 },
	'unused7': { 'number': 7, 'type': 'output', 'value': 0 },
	'unused8': { 'number': 8, 'type': 'output', 'value': 0 },
	'unused10': { 'number': 10, 'type': 'output', 'value': 0 },
	'unused11': { 'number': 11, 'type': 'output', 'value': 0 },
	'unused12': { 'number': 12, 'type': 'output', 'value': 0 },
	'unused13': { 'number': 13, 'type': 'output', 'value': 0 },
	'unused15': { 'number': 15, 'type': 'output', 'value': 0 },
	'unused16': { 'number': 16, 'type': 'output', 'value': 0 },
	'unused18': { 'number': 18, 'type': 'output', 'value': 0 },
	'unused19': { 'number': 19, 'type': 'output', 'value': 0 },
	'unused21': { 'number': 21, 'type': 'output', 'value': 0 },
	'unused22': { 'number': 22, 'type': 'output', 'value': 0 },
	'unused23': { 'number': 23, 'type': 'output', 'value': 0 },
	'unused24': { 'number': 24, 'type': 'output', 'value': 0 },
	'unused26': { 'number': 26, 'type': 'output', 'value': 0 },
	'unused29': { 'number': 29, 'type': 'output', 'value': 0 },
	'unused31': { 'number': 31, 'type': 'output', 'value': 0 },
	'unused32': { 'number': 32, 'type': 'output', 'value': 0 },
	'unused33': { 'number': 33, 'type': 'output', 'value': 0 },
	'unused35': { 'number': 35, 'type': 'output', 'value': 0 },
	'unused36': { 'number': 36, 'type': 'output', 'value': 0 },
	'unused37': { 'number': 37, 'type': 'output', 'value': 0 },
	'unused38': { 'number': 38, 'type': 'output', 'value': 0 },
	'unused40': { 'number': 40, 'type': 'output', 'value': 0 },
}

def read_pin(pin_label: str) -> Binary:
	if not pin_label in PINS:
		raise Exception(f'Tried to read from unknown pin {pin_label}')
	pin = PINS[pin_label]
	
	if pin['type'] == 'input':
		return cast(Binary, +GPIO.input(pin['number']))
	elif pin['type'] == 'output':
		if not 'value' in pin:
			raise Exception(f'No value found for output pin {pin_label}')
		return pin['value']
	else:
		raise

def write_pin(pin_label: str, value: Binary):
	if not pin_label in PINS:
		raise Exception(f'Tried to read from unknown pin {pin_label}')
	pin = PINS[pin_label]
	if pin['type'] != 'output':
		raise Exception(f'Tried to write to non-output pin {pin_label}')
	
	PINS[pin_label]['value'] = value
	GPIO.output(PINS[pin_label]['number'], value)

def cleanup(signal, frame):
	for pin_label, pin in PINS.items():
		write_pin(pin_label, 0)
	exit()

def setup_pins():
	GPIO.setmode(GPIO.BOARD)
	signal(SIGINT, cleanup)
	for pin_label, pin in PINS.items():
		if not pin['number'] in VALID_IO_PINS:
			raise Exception(f'Unknown pin number {pin['number']} in setup_pins')
		if pin['type'] == 'input':
			GPIO.setup(pin['number'], GPIO.IN)
		elif pin['type'] == 'output':
			GPIO.setup(pin['number'], GPIO.OUT)
			GPIO.output(pin['number'], pin['value'])
		else:
			raise Exception(f'Unknown pin type {pin['type']} in setup_pins')
