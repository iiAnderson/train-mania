import stomp
import time
import logging
from messages.parser import Message, NoValidMessageTypeFound, MessageService

RECONNECT_DELAY_SECS = 15

class StompClient(stomp.ConnectionListener):

    def __init__(self, message_service: MessageService):
        self._message_service = message_service

    def on_heartbeat(self):
        print('Received a heartbeat')

    def on_heartbeat_timeout(self):
        print('Heartbeat timeout')

    def on_error(self, headers, message):
        print(message)

    def on_disconnected(self):
        time.sleep(RECONNECT_DELAY_SECS)
        exit(-1)

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])

    def on_message(self, frame):
        
        try:
            msg = Message.from_frame(frame)
            self._message_service.parse(msg)    

        except NoValidMessageTypeFound: 
            ...
