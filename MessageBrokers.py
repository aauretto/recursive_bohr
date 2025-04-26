# MessageBrokers.py
# Class: CS-21
# Author: recursive_bohr
# Purpose:
#     Classes that define an over-the-wire format for messages to be sent.
#     Classes in this file should provide the static methods:
#      tx(socket, message) -- Serializes and sends message over socket
#      rx(socket)          -- Receives messa-ge or group of messages from socket


#================================ LenAndPayload ==============================#
# Format that prepends an int defining the length of the message to the 
# message itself. Supports variable length messages.
#=============================================================================#

import pickle
class LenAndPayload():

    def __init__(self, headerLen = 4):
        """
        Constructor

        Parameters
        ----------
        headerLen: int
            the number of bytes used to encode the length of the payload
            of a message
        """
        self.__headerLen = 4

    def tx(self, sock, msg):
        """
        Send a message on socket sock.

        Parameters
        ----------
        sock: socket.socket
            The socket over which to send the message
        msg: any
            The message to send

        Returns
        -------
        None
        """
        sock.sendall(self.__serialize(msg))
    
    def rx(self, sock):
        """
        Receive a message from a socket sock. If sock is set to not block, none
        will be returned if no data is present, otherwise blocks until a message
        is received on socket.

        Parameters
        ----------
        sock: socket.socket
            The scoket over which to recieve a message

        Returns
        -------
        msg: any | None
        """
        try:
            data = self.__consume_msg(sock)
            return data
        except BlockingIOError:
            return None

    def __serialize(self, data):
        """
        Serialize message to bytes that can then be sent over a socket. 

        Parameters
        ----------
        data: any
            The data to serialize
        """
        payload = pickle.dumps(data)
        return len(payload).to_bytes(self.__headerLen, byteorder='big') + \
            payload

    def __consume_msg(self, sock):
        """
        Consumes one message from socket by reading length then the message. 

        Parameters
        ----------
        sock: socket.socket
            The socket to consume the message from
        """
        # Get header / message len
        dataLen = int.from_bytes(sock.recv(self.__headerLen), byteorder='big')

        # Grab next n bytes where n is length of message and decode them
        rawPayload = b''
        while len(rawPayload) < dataLen:
            chunk = sock.recv(dataLen - len(rawPayload))
            if not chunk:
                break
            rawPayload += chunk

        if rawPayload == b'':
            return None

        return pickle.loads(rawPayload)
    

