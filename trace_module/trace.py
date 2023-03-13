from trace_module import data_handler
from trace_module import trace_handler
from trace_module import message_bus

class Main:
    def __init__(self, tool, pid):
        """
        setup data handling to extract sycall statistics 
        and evaluate syscalls with the models
        """
        self.data_handling = data_handler.DataHandler()

        """
        set up listener
        """
        self.listener = message_bus.Listener()

        """
        setup trace handling to record system calls
        """
        self.trace_handler = trace_handler.TraceHandler(pid, data_handler=self.data_handling, tool=tool)

    def retrain_ids(self, training_size=None, trained_model=None):
        """
        TODO
        retrain ids
            reinitialize data_handling with ids
            and start new sysdig process with new statistc
        :params training_size
        :params trained_model
        """
        pass

def main(tool, pid):
    IDS = Main(tool, pid)