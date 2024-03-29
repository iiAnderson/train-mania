import os
import socket
import time
import click
from messages.parser import MessageType
import stomp

from messages.parser import MessageService

from stomp_client import StompClient

USERNAME = os.environ['DARWIN_USERNAME']
PASSWORD = os.environ['DARWIN_PASSWORD']
HOSTNAME = 'darwin-dist-44ae45.nationalrail.co.uk'
HOSTPORT = 61613

TOPIC = '/topic/darwin.pushport-v16'

CLIENT_ID = socket.getfqdn()
HEARTBEAT_INTERVAL_MS = 15000

@click.command()
@click.option(
    "--message-type",
    "-m",
    type=str,
    required=False
)
@click.option(
    "--rid",
    "-r",
    type=str,
    required=False
)
def main(message_type: str, rid: str) -> None:
    conn = stomp.Connection12([(HOSTNAME, HOSTPORT)],
                          auto_decode=False,
                          heartbeats=(HEARTBEAT_INTERVAL_MS, HEARTBEAT_INTERVAL_MS))

    msg_service = MessageService(message_filter=MessageType.TS)

    conn.set_listener('', StompClient(msg_service))

    connect_header = {'client-id': USERNAME + '-' + CLIENT_ID}
    subscribe_header = {'activemq.subscriptionName': CLIENT_ID}

    conn.connect(username=USERNAME,
                       passcode=PASSWORD,
                       wait=True,
                       headers=connect_header)

    conn.subscribe(destination=TOPIC,
                         id='1',
                         ack='auto',
                         headers=subscribe_header)
    print("Connected")
    try:
        while True:
            time.sleep(1)
    finally:
        print("Closing connection")
        conn.disconnect()


if __name__ == "__main__":
    main()