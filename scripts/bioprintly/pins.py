from __future__ import annotations
from time import sleep
from types import SimpleNamespace
from typing import Iterable, Literal, Tuple, TypedDict, cast, get_args, TYPE_CHECKING
if TYPE_CHECKING:
	from state import GlobalState

Bit = Literal[0, 1]
PinNumber = Literal[
	         8, 10, 12,     16, 18,     22, 24, 26,         32,     36, 38, 40,
	 3,  5,  7,     11, 13, 15,     19, 21, 23,         29, 31, 33, 35, 37,
]
InputOutput = Literal['Input', 'Output']

class Pin(TypedDict):
	number: PinNumber | None
	io_type: InputOutput | None
	value: Bit | None
class PinMappings(TypedDict):
	rotator_direction: Pin
	rotator_step: Pin
	actuator_retract: Pin
	actuator_extend: Pin
	heating_pad_1: Pin
	heating_pad_2: Pin
	heating_pad_3: Pin
	heating_pad_4: Pin
	uv_light_1: Pin
	uv_light_2: Pin
	uv_light_3: Pin
	uv_light_4: Pin

try:
	GPIO = __import__('RPi', fromlist = ['GPIO']).GPIO
	GPIO.setwarnings(False)
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

def flip_bit(value: Bit) -> Bit:
	return cast(Bit, +(not value))

def setup_pins(state: GlobalState):
	'''Can be rerun idempotently'''
	GPIO.setmode(GPIO.BOARD)
	# Turn off all pins in case any were unmapped, or left turned on externally
	zero_out_pins(state)
	
	for pin_name, pin in cast(
		Iterable[Tuple[str, Pin]],
		state['pins'].items()
	):
		if any(map(lambda value: value == None, pin.values())):
			continue
		if not pin['number'] in get_args(PinNumber):
			raise Exception(f"Unknown pin number {pin['number']} in setup_pins")
		if pin['io_type'] == 'Input':
			GPIO.setup(pin['number'], GPIO.IN)
		elif pin['io_type'] == 'Output':
			GPIO.setup(pin['number'], GPIO.OUT)
			pin['value'] = 0
		else:
			raise Exception(f"Unknown pin type {pin['io_type']} in setup_pins")

def read_pin(state: GlobalState, pin_name: str) -> Bit:
	if not pin_name in state['pins']:
		raise Exception(f'Tried to read from unknown pin {pin_name}')
	pin = state['pins'][pin_name]
	
	if pin['io_type'] == 'Input':
		return cast(Bit, +GPIO.input(pin['number']))
	elif pin['io_type'] == 'Output':
		if not 'value' in pin:
			raise Exception(f'No value found for output pin {pin_name}')
		return pin['value']
	else:
		raise Exception(f"Unknown pin type {pin['io_type']} in read_pin")

def write_pin(state: GlobalState, pin_name: str, value: Bit):
	if not pin_name in state['pins']:
		raise Exception(f'Tried to read from unknown pin {pin_name}')
	pin = state['pins'][pin_name]
	if pin['io_type'] != 'Output':
		raise Exception(f'Tried to write to non-output pin {pin_name}')
	
	GPIO.output(pin['number'], value)
	pin['value'] = value

def zero_out_pins(state: GlobalState):
	for pin_number in get_args(PinNumber):
		GPIO.setup(pin_number, GPIO.OUT)
		GPIO.output(pin_number, 0)
	
	for pin_name, pin in state['pins'].items():
		cast(Pin, pin)['value'] = 0
