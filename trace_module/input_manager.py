import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5556")

while True:
    system_call_sequence = input("Insert Sequence: ")
    print("Sending sequence: %s" % system_call_sequence)
    socket.send_string(system_call_sequence)
    message = socket.recv()
    print("Received reply: %s" % (message.decode("utf-8")))