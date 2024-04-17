from gui import run_gui
from pins import setup_pins
from service import run_service
from state import get_initial_global_state, load_state_from_disk
from threading import Timer

def setup_everything():
	state = get_initial_global_state()
	
	setup_pins(state)
	
	# Launch the service (command processing) as a secondary thread
	Timer(0, run_service, [state]).start()
	
	# Run the GUI as the main thread
	while True:
		run_gui(state)
		if state['nonpersistent']['reopening_gui'] == True:
			state['nonpersistent']['reopening_gui'] = False
			continue
		break

setup_everything()
