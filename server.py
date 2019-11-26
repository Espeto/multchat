import socket
import threading
import select

HEADER_LENGTH = 10
bind_port = 9999
bind_ip =  "127.0.0.1"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Permite a reconexão
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((bind_ip, bind_port))

server_socket.listen()

sockets_list = [server_socket]

clients = {}

print("[*] Listening on %s:%d" % (bind_ip,bind_port))

def receive_message(client_socket):
    try:
        
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())

        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        return False

def handle_client(client_socket):

    #exibe o que o cliente quer enviar
    request = client_socket.recv(1024)

    print("[*] Received: %s" % request)

    #envia pacote de volta
    client_socket.send(bytes("ACK", "utf-8"))

    client_socket.close()

def main():

    while True:

        client,addr = server_socket.accept()

        print("[*] Accepted connection from: %s:%d" % (addr[0],addr[1]))

        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

main()