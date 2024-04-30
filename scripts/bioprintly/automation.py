from state import establish_savefolder_path
import sys

savefolder_path = establish_savefolder_path()
logfile = open(f'{savefolder_path}/automation_log.txt', 'a')
logfile.write('Invoked with argv: ' + str(sys.argv) + '\n')
