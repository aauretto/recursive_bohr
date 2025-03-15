# BasicClient.py
# Class: CS-21
# Author: recursive_bohr
# Purpose:
#     Class that wraps socket functionality into a basic transmit and receive
#     functions a client could use to connect to and communitcate with a server.

import socket
import select
import MessageBrokers

class BasicServer:
    def __init__(self, 
                 host : str, 
                 port : int, 
                 qLen : int, 
                 msgBroker = MessageBrokers.LEN_AND_PAYLOAD_BROKER()):
        """
        Constructor
        Params:
          host -- Address this server can be reached at
          port -- Port this server will listen on
          qLen -- Number of incoming connection requests that can wait to be 
                  accepted before one is refused.
          msgBroker -- a class that implements the following static methods:
            tx(socket, message) -- sends message over a socket
            rx(socket)          -- receives a message over a socket
            This class defines the over-the-wire protocol this client uses and 
            should be the same for both server and client.

        This class supports only one connection at a time.
        """
        self.host = host
        self.port = port
        self.msgBroker = msgBroker

        # Set up a server socket that we can use to accept connections
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(qLen)

        # List of all open connections
        self.clients = []

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
            newClients.append(addr)
        return newClients

    def __del__(self):
        """
        Destructor -- Close all connections
        """
        for c in self.clients:
            c.close()
        self.sock.close()

    def tx_message(self, client, msg):
        """
        Send message msg to client client
        """
        self.msgBroker.tx(client, msg)

    def broadcast_message(self, msg):
        """
        Send message msg to all clients
        """
        for c in self.clients:
            try:
                self.tx_message(c, msg)
            except:
                continue

    def handle_message(self, client, msg):
        """
        Dummy function -- for now just echos messages to all clients but 
        eventually we want to put something here that does server-y things.
        
        Plan is to erlang it up and have the user register a handle_message fx
        """
        self.broadcast_message(msg)

    def rx_message(self):
        """
        Blocks until we get a message from any client. Then calls handle_message
        on that client.
        """
        readable, writable, exceptional = select.select(self.clients, [], self.clients)

        for client in readable:
            try:
                msg = self.msgBroker.rx(client)
                self.handle_message(client, msg)
            except ConnectionAbortedError:
                self.remove_client(client)
            except ConnectionResetError:
                self.remove_client(client)

    def remove_client(self, client):
        """
        Removes a client from our list of clients
        """
        self.clients.remove(client)
        client.close()

