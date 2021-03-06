#!/usr/bin/env python3

import argparse
import logging
import os
import shlex
import sys
import time

import settings

from solar_car_process import SolarCarProcess

'''
Attempt to Ping the other pi, if the pi responds open primary processes, otherwise open secondary processes
'''
def ping_raspi():
    response = os.system("ping -c 3 " + settings.HOST_IP)
    pingSuccess = False
    if response == 0:
        pingSuccess = True
    print(pingSuccess)
    return pingSuccess

class Domovoi:

    '''
    Check the path of each process, throw an error if the path is invalid
    '''
    def check_paths(self, solar_car_processes):
        for solar_car_process in solar_car_processes: # For each solar_car_process 
            if not os.path.exists(solar_car_process.path[0]):
                logging.critical("No such path: %s", solar_car_process.path[0])
                exit()

    '''
    Try and start the processes, if an error occurs, kill the process
    '''
    def start_processes(self, solar_car_processes): 
        for solar_car_process in solar_car_processes:
            try:
                solar_car_process.start()
            except OSError as e: 
                logging.critical(e)
                self.kill_processes(solar_car_processes)
                raise

    '''
    Kill and remove all the processes from the list
    '''
    def kill_processes(self, solar_car_processes):
        for solar_car_process in solar_car_processes:
            # Ensures that all processes are stopped
            try:
                solar_car_process.process.kill()
            except AttributeError: # Fails to kill everything
                pass
            solar_car_processes.remove(solar_car_process)

    '''
    Opens processes_file which should contain a list of paths to each SolarCarProcess, and makes an object for each one.
    '''
    def parse_file(self, processes_file):
        with open(processes_file) as file:
            return([SolarCarProcess(shlex.split(path)) for path in file.read().splitlines()])

    def run(self, processes_file):
        solar_car_processes = self.parse_file(processes_file)
        if len(solar_car_processes) == 0:
            logging.error("There are no processes in processes_file")
            return
        self.check_paths(solar_car_processes)
        self.start_processes(solar_car_processes)
        # Watch over the processes and respond accordingly
        while (len(solar_car_processes)): # Checks to make sure that there are still processes to be watched over.
            break
            for solar_car_process in solar_car_processes:
                if solar_car_process.check_status() != None:
                    if solar_car_process.process.returncode == 0: # Good exit, removes the process from the list
                        solar_car_processes.remove(solar_car_process)
                    elif solar_car_process.timesRestarted == settings.MAX_RESTART: # If a process restarts too many times, print this and remove it.
                        logging.critical("%s reached %d restart(s) with exit code %d",
                            os.path.basename(solar_car_process.path[0]), settings.MAX_RESTART, solar_car_process.process.returncode)
                        solar_car_processes.remove(solar_car_process)
                    else:  # Log the crash 
                        logging.warning("%s crash number %d with exit code %d",
                            os.path.basename(solar_car_process.path[0]), solar_car_process.timesRestarted + 1, solar_car_process.process.returncode)
                        solar_car_process.restart()
                        startup_error = solar_car_process.process.communicate()[1]# Communicate returns a tuple (stdoutdata, stderrdata)
                        if startup_error:# If there is a value in stderrdata, notify and remove it
                            logging.error("%s unable to startup: %s",
                                os.path.basename(solar_car_process.path[0]), startup_error)
                            solar_car_processes.remove(solar_car_process)
            time.sleep(settings.SLEEP_TIME)# Wait 2 seconds before doing the for loop again
   

def main():
    parser = argparse.ArgumentParser()# Take in command line arguments
    # Add a positional for startup modes
    parser.add_argument('mode', help='Domovoi startup mode, run as ./domovoi primary or ./domovoi secondary')
    args = parser.parse_args()
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(filename='logs/%s' % time.asctime(), format='%(asctime)s - %(levelname)s - %(message)s') # Makes a log of events in this session
    file = settings.DISPLAY_FILE
    if(args.mode == "primary"):
        if(ping_raspi()):
            file = settings.DISPLAY_FILE
        else:
            file = settings.RACE_FILE;
    elif(args.mode == "secondary"):
        file = settings.DISPLAY_FILE;

    domovoi = Domovoi()
    domovoi.run(file)# Uses the arguments stored earlier to run the program.
        
if __name__ == '__main__':
    main()

