import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfTransformer
import scipy
import datetime
from decouple import config

import logging
logging.getLogger('pika').setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

from trace_module import message_bus

DETECTION_THRESHOLD = float(config('DETECTION_THRESHOLD'))

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DataHandler:
    def __init__(self):
        """
        Initialize the data handler subcomponent 
        - Calculates statistics of the system calls (sum, calls per bucket (set to second -> bucket delay), distribution)
        - Collection of IDS information (score, state, etc)
        """
        file = open("./resources/chi2.pk", "rb")
        self.fs_chi2 = pickle.load(file)
        file.close()

        # Load TFIDF/Ngram2 Pickle
        file = open("./resources/vectorizer_chi2.pk", "rb")
        self.vectorizer_chi2 = pickle.load(file)
        file.close()

        # Load Models
        json_file = open('resources/model_chi2.json', 'r')
        json_model = json_file.read()
        json_file.close()
        #self.model_chi2 = model_from_json(json_model)
        #self.model_chi2.load_weights("./res/model_chi2.h5")

        self.loaded_model = pickle.load(open('./resources/mlp_model.sav', 'rb'))

        self.malicious_counter = 0
        self.benign_counter = 0

        self.intrusions = dict()

    def run_decision_engine(self, sequence, pid, program_name, sequence_length, flag):

        main_corpus_x = []

        for i in range(len(sequence) - sequence_length + 1):
            line = ' '.join(sequence[i:i+sequence_length])
            main_corpus_x.append(line)

        x_test = self.vectorizer_chi2.transform(main_corpus_x)
        x_test = x_test.toarray()

        x_test = self.fs_chi2.transform(x_test)
        x_test = np.asarray(x_test)

        #y_pred = self.model_chi2.predict(x_test, verbose=0)
        y_pred = self.loaded_model.predict(x_test)
        y_pred = self.loaded_model.predict_proba(x_test)
        
        for i in range(len(y_pred)):
            ct = datetime.datetime.now()
            ts = ct.timestamp()
            if y_pred[i][1] <= DETECTION_THRESHOLD:
                confidence_level = (DETECTION_THRESHOLD - y_pred[i][1]) / (DETECTION_THRESHOLD)
                #confidence_level = y_pred[i][0]
                self.print_stats(pid, program_name, confidence_level, main_corpus_x[i], "Benign",  ct, -1, -1, flag) 
                #self.clear_screen()
                
            else:
                if program_name not in self.intrusions.keys():
                    self.intrusions[program_name] = [ts]
                else:
                    self.intrusions[program_name].append(ts)

                ts_start = self.intrusions[program_name][0]
                occurence_number = len(self.intrusions[program_name])

                confidence_level = (y_pred[i][1] - DETECTION_THRESHOLD) / (1 - DETECTION_THRESHOLD)
                #confidence_level = y_pred[i][1]
                self.print_stats(pid, program_name, confidence_level, main_corpus_x[i], "Malign", ts, ts_start, occurence_number, flag)
                #message_bus.send(str(ct), str(ts), " ".join(sequence), program_name, pid, str(confidence_level), ts_start, occurence_number)
                
                #self.clear_screen()

    def clear_screen(self):
        os.system("clear")

    def print_stats(self, pid, program_name, confidence, sequence_string, Classification, ts, ts_start, occurence_number, flag):
        if flag == 0:
            print()
            print(f"{bcolors.BOLD}{bcolors.WARNING}Classification Result:{bcolors.ENDC}" + f"{bcolors.BOLD}\nTimestamp: {bcolors.ENDC}" + str(ts) + f"{bcolors.BOLD}\nFirst Attack Timestamp: {bcolors.ENDC}" + str(ts_start) + f"{bcolors.BOLD}\nPID: {bcolors.ENDC}" + str(pid) + f"{bcolors.BOLD}\nProgram/Service: {bcolors.ENDC}" + str(program_name) + f"{bcolors.BOLD}\nSequence: {bcolors.ENDC}" + str(sequence_string) + f"{bcolors.BOLD}\nClassification: {bcolors.ENDC}" + str(Classification) + f"{bcolors.BOLD}\nConfidence Level: {bcolors.ENDC}" + str(confidence))
        else:
            print()
            print(f"{bcolors.BOLD}{bcolors.OKCYAN}Classification Result:{bcolors.ENDC}" + f"{bcolors.BOLD}\nTimestamp: {bcolors.ENDC}" + str(ts) + f"{bcolors.BOLD}\nFirst Attack Timestamp: {bcolors.ENDC}" + str(ts_start) + f"{bcolors.BOLD}\nPID: {bcolors.ENDC}" + str(pid) + f"{bcolors.BOLD}\nProgram/Service: {bcolors.ENDC}" + str(program_name) + f"{bcolors.BOLD}\nSequence: {bcolors.ENDC}" + str(sequence_string) + f"{bcolors.BOLD}\nClassification: {bcolors.ENDC}" + str(Classification) + f"{bcolors.BOLD}\nConfidence Level: {bcolors.ENDC}" + str(confidence))
        
