"""
File: IPCutils.py
Authors: Aiden Auretto, Peter Scully, Simon Webber, Claire Williams
Date: 4/28/2025

Purpose
------- 
    This file contains definitions for Inter-Process Communication utilities.
    Namely, it defines a base server and a base client modeled after the Erlang
    gen-server which provide simple server-client interactions over TCP sockets.
"""


import socket
import select
import MessageBrokers
from abc import ABC, abstractmethod

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
class BaseServer(ABC):
    def __init__(self, 
                 host : str, 
                 port : int, 
                 qLen : int = 1, 
                 msgBroker = MessageBrokers.LenAndPayload(),
                 timeout   = None):
        """
        Constructor for the Base Server

        Parameters
        ----------
        host: str
            Address this server can be reached at
        port: int
            Port this server will listen on
        qLen: int
            Number of incoming connection requests that can wait to be 
            accepted before one is refused.
        msgBroker: LenAndPayload
            an object that implements the following methods:
                tx(socket, message) -- sends message over a socket
                rx(socket)          -- receives a message over a socket
                Defines the over-the-wire protocol this client uses and should
                be the same for both server and client.
        timeout: float
            A time (in s) that the server will wait for a message before taking
            a break to handle signals.
        """
        self._host = host
        self._port = port
        self._msgBroker = msgBroker
        self.__timeout = timeout
        
        # List of all open connections
        self._clients = []

        self._keepGoing = True # Flag that stops server operations

        # Set up a server socket that we can use to accept connections
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((self._host, self._port))
        self._sock.listen(qLen)

    def __del__(self):
        """
        Destructor -- Close all connections
        """
        for c in self._clients:
            c.close()
        self._sock.close()

    def reject_connections(self, nConx = 1):
        """
        Rejects n connections from clients. Blocks until we get through all 
        nConx connections.

        Parameters
        ----------
        nConx: int
            The number of connections to reject
        """
        rejClients = []
        for _ in range(nConx):
            conx, addr = self._sock.accept() # Let them in then close the door
            print(f"Rejecting connection from {addr[0]}")
            rejClients.append(conx)
            conx.close()
        return rejClients
    
    def accept_connections(self, nConx = 1):
        """
        Accepts n connections from clients. Blocks until we get all nConx 
        connections.

        Parameters
        ----------
        nConx: int
            The number of connections to accept
        """
        newClients = []
        for _ in range(nConx):
            conx, addr = self._sock.accept() # wait for connection
            print(f"Connection accepted from {addr[0]}")
            conx.setblocking(0)
            self._clients.append(conx)        
            newClients.append(conx)
        return newClients

    def tx_message(self, client, msg):
        """
        Send message msg to client client

        Parameters
        ----------
        client: socket.socket
            The socket object of the client to send the message to 
        msg: any
            The message to send to the client
        """
        try:
            self._msgBroker.tx(client, msg)
            return True
        except:
            return False

    def broadcast_message(self, msg):
        """
        Send message msg to all clients

        Parameters
        ----------
        msg: any
            The message to broadcast
        """
        for c in self._clients:
            self.tx_message(c, msg)
    
    def exclusive_broadcast(self, clientsToExclude, msg):
        """
        Broadcasts a message to all but clients in list clientsToExclude

        Parameters
        ----------
        clientsToExclude: list(socket.socket)
            The list of client sockets to not broadcast the message to
        msg: any
            The message to broadcast
        """
        for c in self._clients:
            if c not in clientsToExclude:
                self.tx_message(c, msg)
    
    def rx_message(self):
        """
        Blocks until we get a message from any client. Then calls handle_message
        on that client.
        """
        readable, _, _ = select.select([self._sock] + self._clients, 
                                       [], 
                                       self._clients,
                                       self.__timeout)

        for client in readable:
            if not self._keepGoing:
                return

            if client is self._sock:
                self.handle_connection()
            else:
                try:
                    msg = self._msgBroker.rx(client)
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

    @abstractmethod
    def handle_message(self, client, msg):
        """
        Echos messages to all clients. Override this for server-specific 
        behavior.

        Parameters
        ----------
        client: socket.socket
            The socket of the client the message came from
        msg: any
            The message recieved from the client
        """

    def stop(self):
        """
        Sets the server to not keep going
        """
        self._keepGoing = False

    def is_running(self):
        """
        Returns whether the server is currently running.
        """
        return self._keepGoing

    def remove_client(self, client):
        """
        Removes a client from our list of clients

        Parameters
        ----------
        client: socket.socket
            The socket of the client to remove
        """
        self._clients.remove(client)
        client.close()

# BaseClient.py
# Purpose:
#     Class that wraps socket functionality into a basic transmit and receive
#     functions a client could use to connect to and communitcate with a server.
class BaseClient(ABC):
    def __init__(self, msgBroker = MessageBrokers.LenAndPayload()):
        """
        Constructor for the BaseClient class        
        
        Parameters
        ----------
        msgBroker: LenAndPayload
            should be an object that implements the following methods:
                tx(socket, message) -- sends message over a socket
                rx(socket)          -- receives a message over a socket
            Defines the over-the-wire protocol this client uses and should be
            the same for both server and client.

        This class supports only one connection at a time.
        """
        self._msgBroker = msgBroker
        self._is_connected = False
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            self._sock.connect((host, port))
            self._is_connected = True
            return True
        except OSError as err:
            return False

    def disconnect(self):
        """
        Disconnect from the currently connected host. Does nothing if not 
        connected to anything.
        """
        if self._is_connected:
            self._sock.close()
            self._is_connected = False

    def tx_message(self, msg):
        """
        Send a message

        Parameters
        ----------
        msg: any
            The message to send to the connection
        """
        try:
            self._msgBroker.tx(self._sock, msg)
            return True
        except BrokenPipeError:
            print("Failed to send Message, socket likely closed")
            return False

    def rx_message(self):
        """
        Receive a message
        """
        msg = self._msgBroker.rx(self._sock)
        return self.handle_message(msg)

    @abstractmethod
    def handle_message(self, msg):
        """
        What to do when we get a message. Override this to define custom 
        behavior

        Parameters
        ----------
        msg: any
            The received message
        """


