import traceback
from darwin.messages.src.common import NotURMessage
import stomp
import time
import logging
from darwin.messages.src.common import Message, RawMessage, NoValidMessageTypeFound
from darwin.service.src.message_service import MessageService
from darwin.messages.src.ts import IncorrectMessageFormat


RECONNECT_DELAY_SECS = 15

class StompClient(stomp.ConnectionListener):

    def __init__(self, message_service: MessageService, show_raw: bool = False):
        self._message_service = message_service
        self._show_raw = show_raw

    def on_heartbeat(self):
        print('Received a heartbeat')

    def on_heartbeat_timeout(self):
        print('Heartbeat timeout')

    def on_error(self, headers, message):
        print("Error message")
        print(message)

    def on_disconnected(self):
        time.sleep(RECONNECT_DELAY_SECS)
        print("Disconnected")

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])

    def on_message(self, frame):

        raw_message = RawMessage.parse(frame)
        
        if self._show_raw:
            print(raw_message)
            return
        
        try:
            msg = Message.from_message(raw_message)
            self._message_service.parse(msg)
        except NoValidMessageTypeFound: 
            ...
        except IncorrectMessageFormat:
            ...
        except NotURMessage:
            ...
        except Exception as e: 
            print(raw_message.body)
            print(traceback.format_exc())
