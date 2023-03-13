from _thread import *
import numpy as np
import socket
import time
import logging
import os
import json
from json import JSONEncoder
from decouple import config
from Utils import FedAvg

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Environment Variables
TOTAL_CLIENTS = int(config('TOTAL_CLIENTS'))
HOST = config('HOST')
PORT = int(config('PORT'))
EPOCHS = int(config('EPOCHS'))

# Other Variables
CUR_EPOCH = 0
SIZE = 248
FORMAT = "utf-8"
CLIENT_WEIGHTS = {}
CLIENTS_UPDATED = 0

print("--------------------------------------------")
print("Setup Variables:")
print("--------------------------------------------")
print("Total Clients/Users: %s" % TOTAL_CLIENTS)
print("Host IP: %s" % HOST)
print("Port: %s" % PORT)
print("Comunication Rounds (Global Epochs): %s" % EPOCHS)
print("--------------------------------------------")

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def client_handler(connection, address):
    """
    Client handler that manages each client connection
    """

    global CLIENT_WEIGHTS
    global CUR_EPOCH
    global EPOCHS
    global CLIENTS_UPDATED

    """ Send the amount of communication rounds to client """
    data = f"{EPOCHS}"
    connection.send(data.encode("utf-8"))

    """ Receive data about filename and filesize """
    data = connection.recv(SIZE).decode(FORMAT)
    item = data.split("_")

    option = item[0]
    CLIENT = item[1]

    if option == "Local Model":
        data = connection.recv(SIZE).decode(FORMAT)
        item = data.split("_")
        FILENAME = item[0]
        FILESIZE = int(item[1])
        CLIENT = item[2]
        logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT + "] Filename and filesize received from client.")
        connection.send("Server: Filename and filesize received".encode(FORMAT))

        """ Data transfer """
        logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT + "] Data Transfer Started to Client.")
        with open(f"recv_{FILENAME}", "w") as f:
            while True:
                data = connection.recv(SIZE).decode(FORMAT)
                if not data:
                    break
                f.write(data)
                connection.send("Server: Model Weights Received.".encode(FORMAT))

        """ Add models to dict """
        data = open(f"recv_{FILENAME}") 
        data = json.load(data)

        CLIENT_WEIGHTS[CLIENT] = data['weights']

    if option == "Model Update":
        info_flag = 0
        ts = time.time()

        while True:
            if len(CLIENT_WEIGHTS.keys()) == TOTAL_CLIENTS:
                break
            else:
                if info_flag == 0 or time.time() >= ts + 10:
                    logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT + "] Waiting for other client updates.")
                    info_flag = 1
                    ts = time.time()
                continue

        logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT + "] Send Updated Model Weights to Client.")
        logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT + "] Aggregating Models for Epoch " + str(CUR_EPOCH + 1) + ".")
        
        weights = FedAvg.aggregate_models(CLIENT_WEIGHTS, TOTAL_CLIENTS) 
        weights = np.array(weights, dtype=object)

        message = json.dumps({"weights": weights}, cls=NumpyArrayEncoder)
        FILENAME = f"global-weights-{CLIENT}-{CUR_EPOCH + 1}.json"
        with open(FILENAME, "w") as outfile:
            outfile.write(message)

        FILESIZE = os.path.getsize(FILENAME)
        data = f"{FILENAME}_{FILESIZE}"
        connection.send(data.encode("utf-8"))

        msg = connection.recv(SIZE).decode("utf-8")
        logging.info(f"[Client: {address[0]} {str(address[1])}/{CLIENT}] {msg}")

        """ Data transfer. """
        with open(FILENAME, "r") as f:
            while True:
                data = f.read(SIZE)
                if not data:
                    break
                connection.send(data.encode(FORMAT))
                msg = connection.recv(SIZE).decode(FORMAT)
        
        logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT + "] " + msg)
        logging.info("[Client: " + address[0] + ':' + str(address[1]) + "/" + CLIENT +  "] Global Model Transfer Done for Client.")
        
        CLIENTS_UPDATED += 1
        if CLIENTS_UPDATED == TOTAL_CLIENTS:
            CUR_EPOCH += 1
            CLIENTS_UPDATED = 0
            CLIENT_WEIGHTS = {}

        if CUR_EPOCH == EPOCHS - 1:
            """ Closing connection. """
            connection.close()

def accept_connections(ServerSocket):
    ''' function that continuosly run to accept client connections
    return:
        none '''
    Client, address = ServerSocket.accept()
    logging.info("[Client: " + address[0] + ':' + str(address[1]) + "] Client connected.")
    start_new_thread(client_handler, (Client, address, ))

def start_server():
    ''' function that starts up the server socket listener
    return:
        none '''
     
    logging.info('Starting Server Listener.')
    ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ServerSocket.bind((HOST, PORT))
    except socket.error as e:
        print(str(e))
    logging.info(f'Server is listening on the port {PORT}')
    ServerSocket.listen()

    while True:
        accept_connections(ServerSocket)

start_server()