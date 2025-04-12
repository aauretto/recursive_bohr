# IPCutils.py
# Class: CS-21
# Author: recursive_bohr
# Purpose: 
#   This file contains definitions for Inter-Process Communication utilities.

import socket
import select
import MessageBrokers

#=============== Any Exceptions related to socket comms go here ===============#
class UnableToConnectError(Exception):
    def __init__(self, addr, port):
        super().__init__(f"Unable to connect to: {addr}:{port}")

def get_ip():
    """
    Function that gets the IP address we can be reached at if we host a server
    on 0.0.0.0
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Use Google's DNS as a dummy target
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Error: {e}"

# Purpose:
#     Class that wraps socket functionality into a basic transmit and receive
#     functions a client could use to connect to and communitcate with a server.
class BaseServer:
    def __init__(self, 
                 host : str, 
                 port : int, 
                 qLen : int = 1, 
                 msgBroker = MessageBrokers.LenAndPayload()):
        """
        Constructor
        Params:
          host -- Address this server can be reached at
          port -- Port this server will listen on
          qLen -- Number of incoming connection requests that can wait to be 
                  accepted before one is refused.
          msgBroker -- an object that implements the following methods:
            tx(socket, message) -- sends message over a socket
            rx(socket)          -- receives a message over a socket
            Defines the over-the-wire protocol this client uses and should be 
            the same for both server and client.
        """
        self.host = host
        self.port = port
        self.msgBroker = msgBroker
        
        # List of all open connections
        self.clients = []

        self.__keepGoing = True # Flag that stops server operations

        # Set up a server socket that we can use to accept connections
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(qLen)

    def reject_connections(self, nConx = 1):
        """
        Rejects n connections from clients. Blocks until we get through all 
        nConx connections.
        """
        rejClients = []
        for _ in range(nConx):
            conx, addr = self.sock.accept() # Let them in then close the door
            rejClients.append(conx)
            conx.close()
        return rejClients
    
    def accept_connections(self, nConx = 1):
        """
        Accepts n connections from clients. Blocks until we get all nConx 
        connections.
        """
        newClients = []
        for _ in range(nConx):
            conx, addr = self.sock.accept() # wait for connection
            conx.setblocking(0)
            self.clients.append(conx)        
            newClients.append(conx)
        return newClients

    def __del__(self):
        """
        Destructor -- Close all connections
        """
        print("delling")
        for c in self.clients:
            c.close()
        self.sock.close()

    def tx_message(self, client, msg):
        """
        Send message msg to client client
        """
        try:
            self.msgBroker.tx(client, msg)
            return True
        except:
            return False

    def broadcast_message(self, msg):
        """
        Send message msg to all clients
        """
        for c in self.clients:
            self.tx_message(c, msg)
    
    def exclusive_broadcast(self, clientsToExclude, msg):
        """
        Broadcasts a message to all but clients in list clientsToExclude
        """
        for c in self.clients:
            if c not in clientsToExclude:
                self.tx_message(c, msg)
    
    def rx_message(self):
        """
        Blocks until we get a message from any client. Then calls handle_message
        on that client.
        """
        readable, _, _ = select.select([self.sock] + self.clients, 
                                       [], 
                                       self.clients)

        for client in readable:
            if not self.__keepGoing:
                return
            
            if client is self.sock:
                self.handle_connection()
            else:
                try:
                    msg = self.msgBroker.rx(client)
                    if msg == None:
                        self.remove_client(client)
                    else:
                        self.handle_message(client, msg)
                except (ConnectionAbortedError, ConnectionResetError) as err:
                    print(f"Got {err} from {client}. Removing connection...")
                    self.remove_client(client)
    
    def handle_connection(self):
        """
        Called whenver theres a new client trying to connect. Default behavior 
        is to accept the connection.
        """
        self.accept_connections()

    def handle_message(self, client, msg):
        """
        Echos messages to all clients. Override this for server-specific 
        behavior.
        """
        if msg == STOP_SERVER_MSG:
            self.stop()
            print("Set stop flag")
            return
        self.broadcast_message(msg)

    def stop(self):
        self.__keepGoing = False

    def is_running(self):
        """
        Returns whether the server is currently running.
        """
        return self.__keepGoing

    def remove_client(self, client):
        """
        Removes a client from our list of clients
        """
        self.clients.remove(client)
        client.close()

# BaseClient.py
# Purpose:
#     Class that wraps socket functionality into a basic transmit and receive
#     functions a client could use to connect to and communitcate with a server.
class BaseClient:
    def __init__(self, msgBroker = MessageBrokers.LenAndPayload()):
        """
        Constructor. msgBroker should be an object that implements the following 
        methods:
            tx(socket, message) -- sends message over a socket
            rx(socket)          -- receives a message over a socket
        Defines the over-the-wire protocol this client uses and should be the 
        same for both server and client.

        This class supports only one connection at a time.
        """
        self.msgBroker = msgBroker
        self.is_connected = False
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
            self.is_connected = True
            return True
        except OSError as err:
            return False

    def disconnect(self):
        """
        Disconnect from the currently connected host. Does nothing if not 
        connected to anything.
        """
        if self.is_connected:
            self.sock.close()
            self.is_connected = False

    def tx_message(self, msg):
        """
        Send a message
        """
        try:
            self.msgBroker.tx(self.sock, msg)
            return True
        except BrokenPipeError:
            print("Failed to send Message, socket likely closed")
            return False

    def rx_message(self):
        """
        Receive a message
        """
        msg = self.msgBroker.rx(self.sock)
        return self.handle_message(msg)

    def handle_message(self, msg):
        """
        What to do when we get a message. Override this to define custom 
        behavior
        """
        print(msg)

