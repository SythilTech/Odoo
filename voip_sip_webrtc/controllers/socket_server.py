import socket
import threading
import logging
_logger = logging.getLogger(__name__)
from base64 import b64encode
from hashlib import sha1

clients = []

def parse_headers (data):
    headers = {}
    lines = data.splitlines()
    for l in lines:
        parts = l.split(": ", 1)
	if len(parts) == 2:
	    headers[parts[0]] = parts[1]
    headers['code'] = lines[len(lines) - 1]
    return headers

def handshake(clientsocket):
    _logger.error("Hand Shake")
    data = clientsocket.recv(1024)
    headers = parse_headers(data)

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    #client_key = "dGhlIHNhbXBsZSBub25jZQ=="
    client_key = headers['Sec-WebSocket-Key']
    response_key = b64encode(sha1(client_key + GUID).digest())

    shake = "HTTP/1.1 101 Switching Protocols\r\n"
    shake += "Upgrade: WebSocket\r\n" 
    shake += "Connection: Upgrade\r\n"
    shake += "Sec-WebSocket-Accept: %s\r\n\r\n" % (response_key)

    return clientsocket.send(shake)

def client_socket_thread(clientsocket, address):
    handshake(clientsocket)

    #Listen for the sdp description
    while 1:
        data = clientsocket.recv(524288)
        
        #Broadcast the data
        for c in clients:
            if c == clientsocket:
                c.send(data)

def socket_server():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', 8045));
    serversocket.listen(5);

    while 1:
        #accept connections from outside
        (clientsocket, address) = serversocket.accept()

        clients.append(clientsocket)

        client_socket_threading = threading.Thread(target=client_socket_thread, args=(clientsocket, address))
        client_socket_threading.start()

#Start a new thread so you don't block the main Odoo thread
voip_socket_thread = threading.Thread(target=socket_server, args=())
voip_socket_thread.start()