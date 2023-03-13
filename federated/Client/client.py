# Imports
import os
import json
import socket
import logging
import numpy as np
from json import JSONEncoder
from sklearn.utils import shuffle
from decouple import config

from Utils import DataPreparation
from Utils import MLUnit

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Environment Variables
HOST = config('HOST')
PORT = int(config('PORT'))
EPOCHS = int(config('LOCAL_EPOCHS'))
CLIENT = config('CLIENT_ID')

print("--------------------------------------------")
print("Setup Variables:")
print("--------------------------------------------")
print("Client ID: %s" % CLIENT)
print("Host IP: %s" % HOST)
print("Port: %s" % PORT)
print("Local Epochs: %s" % str(EPOCHS))
print("--------------------------------------------")

TRAINING_BATCH_SIZE = 50000
BATCH_SIZE = 1024
SIZE = 248
FORMAT = "utf-8"

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def client_program():
    cur_epoch = 0
    global CLIENT

    while True:
        client_socket = socket.socket()  # instantiate
        client_socket.connect((HOST, PORT))  # connect to the server

        data = client_socket.recv(SIZE).decode(FORMAT)
        epochs = int(data)

        logging.info("Connected to server to send model.")

        x_train, y_train, x_test, y_test = DataPreparation.get_data()
        weights = MLUnit.train(x_train, y_train, x_test, y_test, BATCH_SIZE, TRAINING_BATCH_SIZE, epochs)

        data = f"Local Model_{CLIENT}"
        client_socket.send(data.encode(FORMAT))

        message = json.dumps({"weights": weights}, cls=NumpyArrayEncoder)
        CLIENT = config('CLIENT_ID')
        FILENAME = f"{CLIENT}-weights.json"
        with open(FILENAME, "w") as outfile:
            outfile.write(message)

        FILESIZE = os.path.getsize(FILENAME)
        
        data = f"{FILENAME}_{FILESIZE}_{CLIENT}"
        client_socket.send(data.encode("utf-8"))

        msg = client_socket.recv(SIZE).decode("utf-8")
        logging.info(f"{msg}")

        """ Data transfer. """
        with open(FILENAME, "r") as f:
            while True:
                data = f.read(SIZE)
                if not data:
                    break
                client_socket.send(data.encode(FORMAT))
                msg = client_socket.recv(SIZE).decode(FORMAT)
        logging.info(msg)

        client_socket.close()

        client_socket = socket.socket()  # instantiate
        client_socket.connect((HOST, PORT))  # connect to the server
        logging.info("Connected to server to receive model.")

        """ Global model transfer """
        data = client_socket.recv(SIZE).decode(FORMAT)
        epochs = int(data)

        data = f"Model Update_{CLIENT}"
        client_socket.send(data.encode(FORMAT))

        data = client_socket.recv(SIZE).decode(FORMAT)
        item = data.split("_")
        FILENAME = item[0]
        FILESIZE = int(item[1])

        logging.info("Filename and filesize received from server.")
        client_socket.send("Filename and filesize received.".encode(FORMAT))

        """ Data transfer """
        logging.info("Data Transfer Started from server.")
        with open(f"recv_{FILENAME}", "w") as f:
            while True:
                data = client_socket.recv(SIZE).decode(FORMAT)
                if not data:
                    break
                f.write(data)
                client_socket.send("Global Model Received.".encode(FORMAT))

        data = open(f"recv_{FILENAME}") 
        data = json.load(data)
        global_weights = data['weights']
        global_weights = np.array(weights, dtype=object)

        MLUnit.test(global_weights, x_test, y_test)

        if cur_epoch == epochs:
            client_socket.close()
            break
        cur_epoch += 1

if __name__ == '__main__':
    client_program()