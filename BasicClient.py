# BasicClient.py
# Class: CS-21
# Author: recursive_bohr
# Purpose:
#     Class that wraps socket functionality into a basic transmit and receive
#     functions a client could use to connect to and communitcate with a server.

import socket
import MessageBrokers

class BasicClient:
    def __init__(self, msgBroker = MessageBrokers.LEN_AND_PAYLOAD_BROKER()):
        """
        Constructor. msgBroker should be a class that implements the following 
        static methods:
            tx(socket, message) -- sends message over a socket
            rx(socket)          -- receives a message over a socket
        This class defines the over-the-wire protocol this client uses and 
        should be the same for both server and client.

        This class supports only one connection at a time.
        """
        self.msgBroker = msgBroker
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __del__(self):
        """
        Destructor - Close connection
        """
        self.disconnect()

    def connect_to(self, host, port):
        """
        Connect to a host on some port.
        """
        try:
            self.sock.connect((host, port))
            return True
        except OSError as err:
            return False

    def disconnect(self):
        """
        Disconnect from the currently connected host. Does nothing if not 
        connected to anything.
        """
        if self.is_connected():
            self.sock.close()

    def tx_message(self, msg):
        """
        Send a message
        """
        self.msgBroker.tx(self.sock, msg)

    def rx_message(self):
        """
        Receive a message
        """
        return self.msgBroker.rx(self.sock)

    def is_connected(self):
        """
        Returns True if currently connected to a socket, False otherwise.
        """
        try:
            # MSG_PEEK to check for data without consuming it
            data = self.sock.recv(1, socket.MSG_PEEK)
            return len(data) > 0
        except BlockingIOError:
            # No data available, but the socket is still open
            return True
        except Exception:
            # Any other exception means the socket is likely closed
            return False