from contextlib import contextmanager
from collections import deque
import multiprocessing
import subprocess
import threading
import time
import psutil
import logging
import os
import sys
from decouple import config
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# System call limit before pausing the tracer
SYSCALL_LIMIT = int(config('SYSCALL_LIMIT'))
# Time that the parser is paused before resuming tracing 
PAUSE_TIME = int(config('PAUSE_TIME'))

SAVE_SYSCALLS = int(config('SAVE_SYSCALLS'))

TRACER = config('TRACER')
FILTER_OUT = config('FILTER_OUT')
FILTER_OUT = FILTER_OUT.split(",")

FILTER_IN = config('FILTER_IN')
FILTER_IN = FILTER_IN.split(",")

class Process:
    def __init__(self, program_name):
        self.program_name = program_name
        self.syscall_queue = list()

class TraceHandler:

    def get_processes(self, pid):
        """
        Parse the output of `ps aux` into a list of dictionaries representing the parsed 
        process information from each row of the output. Keys are mapped to column names,
        parsed from the first line of the process' output.
        :rtype: list[dict]
        :returns: List of dictionaries, each representing a parsed row from the command output
        """
        output = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE).stdout.readlines()
        headers = [str(h) for h in ' '.join(str(output[0]).strip().split()).split() if h]
        headers[0] = str(headers[0][2::])
        raw_data = map(lambda s: str(s).strip().split(None, len(headers) - 1), output[1:])

        processes = [dict(zip(headers, r)) for r in raw_data]

        if pid is None:
            processes = [d for d in processes if d.get("COMMAND\\n'") != "sudo python main.py\\n'"]
            processes = [d for d in processes if d.get("COMMAND\\n'") != "python main.py\\n'"]
        else:
            processes = [d for d in processes if d.get("PID") == str(pid)]

        return processes

    def execute_perf(self, sensor_command_line):
        """
        Executes the perf trace command to trace the system calls made by the current running applications
        :rtype: str
        :returns: each line that the perf trace command outputs to the shell 
        """
        return subprocess.Popen(sensor_command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
    @contextmanager
    def start_tracer_and_read_data(self, pid):
        """
        start strace or perf process on all or a particular process
        """
        self.flag = 0
        self.trace_process = None
        processes = self.get_processes(pid)

        if TRACER == 'perf':
            if pid != None and len(processes) != 0:
                sensor_command_line = "sudo perf trace -p "  + str(pid)
                self.flag = 2
            elif pid != None:
                sensor_command_line = "sudo perf trace "  + str(pid)
                self.flag = 1
            else:
                sensor_command_line = 'perf trace'

            self.p = self.execute_perf(sensor_command_line)
            yield self.p

        if TRACER == 'strace':
            sensor_command_line = 'sudo strace -xx -T'

            i = 0
            not_root = []

            if pid != None and len(processes) != 0:
                sensor_command_line += ' -p ' + str(pid) + ' -f'
                self.flag = 2
            elif pid != None:
                sensor_command_line += ' ' + str(pid)
            else:
                self.process_dict = dict()
                for process in processes:
                    # get processes that are not root
                    if process['USER'][2::] != 'ROOT':
                        self.process_dict[process['PID']] = process["COMMAND\\n'"]
                        not_root.append(process['PID'])
                        if "systemd-oomd" not in process["COMMAND\\n'"] and "systemd-resolved" not in process["COMMAND\\n'"] and "gsd-housekeeping" not in process["COMMAND\\n'"]:
                            sensor_command_line += ' -p ' + process['PID']
                            i += 1
                    if i == 200:
                        break
            self.p = self.execute_perf(sensor_command_line)
            yield self.p
    
    def syscall_parser_strace(self, line):
        """
        parser that retrieves syscall and pid of a strace system call log line
        :rtype: int, str
        :returns: pid and system call
        """
        if line.startswith("[pid"):
            print(line)
            aux = line.split()
            pid = aux[1][:-1]

            if aux[4] != "<..." and aux[4] != "---" and aux[4] != '+++':
                aux = aux[4].split("(")
                syscall = aux[0]
            else:
                return None

        elif line.startswith("["):
            aux = line.split()
            if aux[2] != "<..." and aux[2] != "---" and aux[2] != '+++':
                aux = aux[2].split("(")
                syscall = aux[0]
            else:
                return None
        else:
            return None
        program = "-"
        try:
            program = self.process_dict[pid]
        except:
            pass

        return (pid, syscall, program)
  
    def syscall_parser_perf(self, syscall):
        """
        parser that retrieves syscall and pid of a perf trace system call log line
        :rtype: int, str
        :returns: pid and system call
        """

        if self.flag == 0:
            line = syscall.split("/")
            
            if len(line) > 1:

                try:
                    aux = line[0].split(":")
                    program_name = aux[1].strip()
                    aux = line[1].split("(")
                    aux = aux[0].split()

                    if aux[0] == 'O' or aux[0] == "usr":
                        return None

                    pid = int(aux[0])
                    syscall = aux[1]

                    if syscall != '...':
                        if SAVE_SYSCALLS == 1:
                            f = open("./data/" + str(pid) + ".txt", "a")
                            f.write(syscall + '\n')
                            f.close()
                        if program_name not in FILTER_OUT:
                            if len(FILTER_IN) > 1 and program_name not in FILTER_IN:
                                return None
                            return (pid, syscall, program_name)
                except:
                    return None
            return None

    def write_syscall(self, target_pid, parser):
        """
        get read system calls from strace or perf subprocess call
        write system calls in deque of the respective process
        """
        count = 0

        logging.info("Started Tracing.")
        with self.start_tracer_and_read_data(target_pid) as s_out:
            for line in s_out.stdout:   
                if TRACER == 'perf':  
                    parsed_syscall = self.syscall_parser_perf(line)
                else:
                    parsed_syscall = self.syscall_parser_strace(line)

                if parsed_syscall != None:
                    count += 1
                if count >= SYSCALL_LIMIT:
                    return 0
                
                if parsed_syscall is not None:
                    process = multiprocessing.current_process()
                    if process.pid == parsed_syscall[0]:
                        pass

                    system_call = self.get_sys_to_int(parsed_syscall[1])

                    if system_call == None:
                        pass
                
                    system_call = str(system_call)
            
                    pid = parsed_syscall[0]
                    program_name = parsed_syscall[2]

                    if parsed_syscall[0] not in self.system_call_buffer:
                        self.system_call_buffer[pid] = Process(program_name)
                    else:
                        self.system_call_buffer[pid].syscall_queue.append(system_call)
                                                
    def read_syscall(self):
        time.sleep(2)
        """ 
        read system calls from deque
        if deque not empty send syscall to data_handling to run the decisioin engine
        """
        while True:
            # check if deque is empty
            if self.system_call_buffer:
                aux_dictionary = dict(self.system_call_buffer)
                for process in aux_dictionary:
                    if len(aux_dictionary[process].syscall_queue) >= self.sequence_length:
                        if len(aux_dictionary[process].syscall_queue) > 200:
                            sequence = aux_dictionary[process].syscall_queue[0:200]
                            program = aux_dictionary[process].program_name
                            aux_dictionary[process].syscall_queue = aux_dictionary[process].syscall_queue[200 - self.sequence_length:]
                        else:
                            sequence = aux_dictionary[process].syscall_queue
                            program = aux_dictionary[process].program_name
                            aux_dictionary[process].syscall_queue = aux_dictionary[process].syscall_queue[len(sequence) - self. sequence_length:]

                        self.data_handling.run_decision_engine(sequence, process, program, self.sequence_length, 0)
                        time.sleep(0.5)
                    else:
                        #logging.info("Nothing to analyse.")
                        time.sleep(0.2)
                        continue
                self.locked = False
            else:
                logging.info("Nothing to analyse.")
                time.sleep(3)

    def filter_syscall(self, parsed_syscall):
        """
        TODO: filter out particular system calls
        """
        pass

    def stop_process(self):
        """
        stop strace or perf subprocess
        """
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() == "perf":
                proc.kill()
            if proc.name() == "strace":
                proc.kill()
            print(proc.name())
        
    def get_sys_to_int(self, system_call):
        """
        return the integer that represents the system call
        """
        if system_call in self.system_call_dict.keys():
            return self.system_call_dict[system_call]
        else:
            return None

    def build_system_call_dict(self):
        filename = "./resources/syscall_labels_.txt"
        file = open(filename, "r")
        lines = file.read()

        for line in lines.split('\n'):
            system_call = line.split()
            if len(system_call) > 1:
                self.system_call_dict[system_call[0]] = int(system_call[1])

    def __init__(self, pid, data_handler, tool):
        """
        On initiation start two threads for reading syscalls
        - The first reads incoming syscallS and writes them to deque with
        information such as:
            - rawtime
            - process name
            - threadID
            - direction > start syscall with params listed below
                        < return
            - syscall type
            - arguments of syscall as list

        - Second thread reads syscalls from deque
        """

        self.process_dict = dict()

        # Initialize write deque thread
        self.system_call_buffer = dict()

        # tools for system call log tracing either strace or perf trace
        self.tool = tool

        # Initiate process that reads deque thread
        self.read_thread = threading.Thread(target=self.read_syscall, args=([]))
        self.read_thread.start()

        # Initiate data_handling - where calculations on syscalls are made
        self.data_handling = data_handler

        # Set length of system call sequences to analyse
        self.sequence_length = 50

        # 0 to trace all processes
        self.flag = 0

        self.system_call_dict = dict()
        self.build_system_call_dict()

        self.locked = True

        # Initiate process that writes system calls into deque
        while True:
            self.write_thread = threading.Thread(target=self.write_syscall, args=([pid, tool]))
            self.write_thread.start()
            self.write_thread.join()
            logging.info("Perf Tracer Paused.")
            logging.info("Cleaning the system call buffer.")
            while self.locked:
                continue
            self.locked = True
            self.system_call_buffer.clear()
            self.stop_process()
            time.sleep(PAUSE_TIME)
