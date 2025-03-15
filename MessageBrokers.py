# MessageBrokers.py
# Class: CS-21
# Author: recursive_bohr
# Purpose:
#     Classes that define an over-the-wire format for messages to be sent.
#     Classes in this file should provide the static methods:
#      tx(socket, message) -- Serializes and sends message over socket
#      rx(socket)          -- Receives message or group of messages from socket


#================================ LenAndPayload ===============================
# Format that prepends an int defining the length of the message to the 
# message itself. Supports variable length messages.
#==============================================================================

def LEN_AND_PAYLOAD_BROKER(HEADER_LEN = 4):
    """
    Produces a class that can send and receive variable length messages over
    sockets.
    """
    import pickle
    class LenAndPayload():
        @staticmethod
        def tx(sock, msg):
            """
            Send a message on socket sock.
            """
            sock.sendall(LenAndPayload.__serialize(msg))
        
        @staticmethod
        def rx(sock):
            """
            Receive a message from a socket sock. If sock is set to not block, none
            will be returned if no data is present, otherwise blocks until a message
            is received on socket.
            """
            try:
                data = LenAndPayload.__deserialize_one(sock)
                return data
            except BlockingIOError:
                return None

        @staticmethod
        def __serialize(data):
            """
            Serialize message to bytes that can then be sent over a socket. 
            """
            payload = pickle.dumps(data)
            return len(payload).to_bytes(HEADER_LEN, byteorder='big') + payload

        @staticmethod
        def __deserialize_one(sock):
            """
            Consumes one message from socket by reading length then the message. 
            """
            # Get header / message len
            dataLen = int.from_bytes(sock.recv(HEADER_LEN), byteorder='big')

            # Grab next n bytes where n is length of message and decode them
            rawPayload = b''
            while len(rawPayload) < dataLen:
                chunk = sock.recv(dataLen - len(rawPayload))
                if not chunk:
                    break
                rawPayload += chunk

            return pickle.loads(rawPayload)
    
    # Produce class
    return LenAndPayload

