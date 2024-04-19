from gui import run_gui
from pins import setup_pins
from service import run_service
import signal
from state import get_initial_global_state, load_state_from_disk, save_state_to_disk
from threading import Timer
from util import set_value

def setup_everything():
	state = get_initial_global_state()
	
	setup_pins(state)
	
	# Launch the service (command processing) as a secondary thread
	Timer(0, run_service, [state]).start()
	
	signal.signal(signal.SIGINT, lambda a, b: (
		save_state_to_disk(state),
		set_value(state['nonpersistent'], 'shutting_down', True),
		state['nonpersistent']['gui_root'].quit(),
	))
	
	# Run the GUI as the main thread
	while True:
		run_gui(state)
		if state['nonpersistent']['reopening_gui'] == True:
			state['nonpersistent']['reopening_gui'] = False
			continue
		break

setup_everything()
