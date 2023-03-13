#!/usr/bin/env python
import pika, logging, threading
import sys, os, json
from decouple import config
import cbor2
from time import sleep

logging.getLogger('pika').setLevel(logging.ERROR)

class Listener:
    def receive_message(self):
        
        try:
            PORT = int(config('PORT'))
            HOST = config('HOST')
            VIRTUAL_HOST = config('VIRTUAL_HOST')
            CREDENTIALS_USERNAME = config('CREDENTIALS_USERNAME')
            CREDENTIALS_PASSWORD = config('CREDENTIALS_PASSWORD')
            ROUTING_KEY = config('ROUTING_KEY_IN')
            EXCHANGE_KEY = config('EXCHANGE_KEY')
            DEVICE_ID = config('DEVICE_ID')

            if HOST == "" or PORT == 0 or VIRTUAL_HOST == "" or CREDENTIALS_PASSWORD == "" or CREDENTIALS_USERNAME == "" or ROUTING_KEY == "" or EXCHANGE_KEY == "" or DEVICE_ID == "":
                logging.info("RabbitMQ connection not possible. Please verify that you provided the .env file on trace_module folder with the correct variables ('HOST', 'PORT', 'VIRTUAL_HOST', 'CREDENTIALS_USERNAME', 'CREDENTIALS_PASSWORD', 'ROUTING_KEY', 'EXCHANGE_KEY', 'DEVICE_ID').")
                return
        except:
            logging.info("RabbitMQ connection not possible. Please verify that you provided the .env file on trace_module folder with the correct variables ('HOST', 'PORT', 'VIRTUAL_HOST', 'CREDENTIALS_USERNAME', 'CREDENTIALS_PASSWORD', 'ROUTING_KEY', 'EXCHANGE_KEY', 'DEVICE_ID').")
            return
        try:
            credentials = pika.PlainCredentials(CREDENTIALS_USERNAME, CREDENTIALS_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(HOST, PORT, VIRTUAL_HOST, credentials))
            channel = connection.channel()

            #channel.queue_declare(queue='device_behaviour_monitoring_queue', durable=True)
            channel.exchange_declare(exchange='dbm_exchange', exchange_type='topic', durable='true')
            channel.queue_bind(exchange='dbm_exchange', queue='device_behaviour_monitoring_queue')
        except:
            logging.info("Connection refused to RabbitMQ. Will retry in 30 seconds.")
            sleep(30)
            self.receive_message()
            return
        
        logging.info("Connection successful to RabbitMQ exhange listener.")

        def callback(ch, method, properties, body):
            body_bytes = json.loads(body)
            logging.info(body_bytes)

        channel.basic_consume(queue=ROUTING_KEY, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    def __init__(self):
        # Initiate process that reads deque thread
        self.read_thread = threading.Thread(target=self.receive_message, args=([]))
        self.read_thread.start()

def send_message(ts, program_name, pid, confidence_level, ts_start, occurence_number):

    try:
        PORT = int(config('PORT'))
        HOST = config('HOST')
        VIRTUAL_HOST = config('VIRTUAL_HOST')
        CREDENTIALS_USERNAME = config('CREDENTIALS_USERNAME')
        CREDENTIALS_PASSWORD = config('CREDENTIALS_PASSWORD')
        DEVICE_ID = config('DEVICE_ID')

    except:
        logging.info("RabbitMQ connection not possible. Please verify that you provided the .env folder with the correct variables ('HOST', 'PORT', 'VIRTUAL_HOST', 'CREDENTIALS_USERNAME', 'CREDENTIALS_PASSWORD', 'ROUTING_KEY', 'EXCHANGE_KEY', 'DEVICE_ID').")
        sleep(2)
        send(ts, program_name, pid, confidence_level, ts_start, occurence_number)
        return 
    
    data_set = {"timestamp": ts,
                "attack_start_date": ts_start,
                "occurence_number": occurence_number,
                "sender": "behaviour_monitoring",
                "device_id" : DEVICE_ID,
                "cause" : program_name,
                "process_id": pid}

    json_dump = json.dumps(data_set)
    logging.info(f"Message Content: {json_dump}")
    message = cbor2.dumps(json_dump)

    credentials = pika.PlainCredentials(CREDENTIALS_USERNAME, CREDENTIALS_PASSWORD)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(HOST, PORT, VIRTUAL_HOST, credentials))
    channel = connection.channel()

    channel.basic_publish(exchange='reputation_updates', routing_key='rs_queue', body=json_dump)
    channel.basic_publish(exchange='dsp_exchange', routing_key='device_self_protection', body=message)
    logging.info("Message successfully submitted to RabbitMQ.")
    connection.close()

def send(ct, ts, syscall_sequence, program_name, pid, confidence_level, ts_start, total_occurences):
    try:
        send_message(ts, program_name, pid, confidence_level, ts_start, total_occurences)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)