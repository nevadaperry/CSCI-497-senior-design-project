import curses
import signal
from types import SimpleNamespace

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

GPIO.setmode(GPIO.BOARD)
valid_io_pins = {3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40}
pins = {
	'm1_step': 3,
	'm1_direction': 5,
	'uv1': 8,
	'uv2': 10,
	'uv3': 12,
	'uv4': 16
}
input_pins = set()
output_pins = {
	pins['m1_step'],
	pins['m1_direction'],
	pins['uv1'],
	pins['uv2'],
	pins['uv3'],
	pins['uv4']
}
output_values = {}

def setup_pins():
	for pin in input_pins:
		if not pin in valid_io_pins:
			raise Exception("Invalid I/O pin {pin}")
		GPIO.setup(pin, GPIO.IN)
	for pin in output_pins:
		if not pin in valid_io_pins:
			raise Exception("Invalid I/O pin {pin}")
		GPIO.setup(pin, GPIO.OUT)
		output_values[pin] = 0
	for pin in valid_io_pins:
		if not pin in output_pins:
			input_pins.add(pin)
			GPIO.setup(pin, GPIO.IN)

def read_pin(pin):
	if pin in input_pins:
		return GPIO.input(pin)
	elif pin in output_pins:
		return output_values[pin]
	else:
		raise Exception(f"Tried to read from unfound pin {pin}")

def write_pin(pin, value):
	if not pin in output_pins:
		raise Exception(f"Tried to write to non-output pin {pin}")
	output_values[pin] = value
	GPIO.output(pin, value)

def setup_curses():
	curses.curs_set(False)
	curses.start_color()
	curses.use_default_colors()
	for i in range(0, curses.COLORS):
		curses.init_pair(i + 1, i, -1)

def pretty_print(stdscr):
	col_width = 16
	screen_rows, screen_cols = stdscr.getmaxyx()
	base_x = screen_cols // 2 - col_width
	base_y = screen_rows // 2 - 20 // 2
	for pin in input_pins:
		stdscr.addstr(
			base_y + (pin + 1) // 2,
			base_x + ((pin + 1) % 2) * col_width,
			f"[Pin #{pin:02}]: {read_pin(pin)}",
			curses.color_pair(8)
		)
	for pin in output_pins:
		stdscr.addstr(
			base_y + (pin + 1) // 2,
			base_x + ((pin + 1) % 2) * col_width,
			f"(Pin #{pin:02}): {read_pin(pin)}",
			curses.color_pair(4)
		)
	stdscr.addstr(base_y - 1, base_x, f"Key: [Input pin] ", curses.color_pair(8))
	stdscr.addstr(f"(Output pin)", curses.color_pair(4))
	stdscr.refresh()

def cleanup(a, b):
	for pin in output_pins:
		write_pin(pin, 0)
	exit()

signal.signal(signal.SIGINT, cleanup)

steps_remaining = 100

def main(stdscr):
	global steps_remaining
	setup_pins()
	setup_curses()
	while True:
		if True or steps_remaining > 0:
			write_pin(pins['m1_direction'], 0)
			write_pin(pins['m1_step'], +(not read_pin(pins['m1_step'])))
			steps_remaining -= 0.5
		write_pin(pins['uv1'], 1)#+(not read_pin(pins['uv1'])))
		write_pin(pins['uv2'], 1)#+(not read_pin(pins['uv2'])))
		write_pin(pins['uv3'], 1)#+(not read_pin(pins['uv3'])))
		write_pin(pins['uv4'], 1)#+(not read_pin(pins['uv4'])))
		pretty_print(stdscr)
		curses.napms(100)

curses.wrapper(main)