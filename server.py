import socket
import threading
import select

HEADER_LENGTH = 10
bind_port = 9999
bind_ip =  "127.0.0.1"

CONN_ACCEP   = "ACC"
NICK_EXIST   = "NE"
NICK_CHANGED = "NC"
RECEIVED     = "ACK"

LIST_USERS = "list"
NEW_NICK   = "nick"
MESSAGE    = "msg"
FILE       = "file"
QUIT       = "quit"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Permite a reconexão
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((bind_ip, bind_port))

server_socket.listen()

sockets_list = []

clients_dict = {}

print("[*] Listening on %s:%d" % (bind_ip,bind_port))

def handle_client(client_socket):
    
    while True:

        try:

            message_header_rcv = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

            if not len(message_header_rcv):
                #Cliente desconectou
                del clients_dict[client_socket]
                sockets_list.remove(client_socket)
                client_socket.close()

                break

            message_parse = message_header_rcv.split()
            command = message_parse[0]

            #Pedido pra listar usuários conectados
            if command == LIST_USERS:
                users_names = ""

                for client in clients_dict:
                    if client != client_socket:
                        nick_string = clients_dict[client][nick] + "\n"
                        users_names += nick_string

                message_header = f"{len(users_names):<HEADER_LENGTH}".encode('utf-8')

                client_socket.send(message_header + users_names)

            #Pedido de troca de nick
            elif command == NEW_NICK:

                nick_length = int(message_parse[1])
                
                try:
                    new_nick_try = client_socket.recv(nick_length).decode('utf-8')
                    can_change = True

                    for client in sockets_list:
                        if client != client_socket:
                            if clients_dict[client]['nick'] == new_nick_try:
                                can_change = False
                                break

                    message_header = ""

                    if can_change:
                        message_header = f"{NICK_CHANGED:<{HEADER_LENGTH}}".encode('utf-8')
                    
                    else:
                        message_header =f"{NICK_EXIST:<{HEADER_LENGTH}}".encode('utf-8')

                    client_socket.send(message_header)

                except:
                    #deu algum problema com a conexão
                    client_socket.close()
                    break

            #envio de mensagem
            elif command == MESSAGE:

                message_size = int(message_parse[1])

                message = client_socket.recv(message_size)

                client_nick_size = clients_dict[client_socket]['header']
                client_nick = clients_dict[client_socket]['header']
                
                parcial_header = f"{MESSAGE} {client_nick_size} {message_size}"

                message_header = f"{parcial_header:<{HEADER_LENGTH}}".encode('utf-8')

                message_to_send = message_header + client_nick.encode('utf-8') + message.encode('utf-8')

                for socket in sockets_list:
                    if socket != client_socket:

                        socket.send(message_to_send)

        except:
            #ocorreu alguma desconexão
            client_socket.close()
            break 


def main():
    #Só vai emitir a thread de cliente se a conexão for bem sucedida
    while True:

        client_socket,addr = server_socket.accept()

        try:

            rcv_message_header = client_socket.recv(HEADER_LENGTH)

            if not len(message_header):
                #continua no loop aguardando conexões
                continue

            
            nick_length = int(rcv_message_header.decode('utf-8').strip())
            user_nick = client_socket.recv(nick_length).decode('utf-8')

            if len(sockets_list):
                nick_existent = False

                for client in clients_dict:
                    if clients_dict[client]['nick'] == user_nick:
                        nick_existent = True
                        break

                if nick_existent:
                    snd_message_header = f"{NICK_EXIST:<{HEADER_LENGTH}}"

                    client_socket.send(snd_message_header)

                    client_socket.close()

                    continue


            clients_dict[client_socket] = {'header': nick_length, 'nick': user_nick}
            sockets_list.append(client_socket)

            snd_message_header = f"{CONN_ACCEP:<{HEADER_LENGTH}}"

            client_socket.send(snd_message_header)

            print("[*] Accepted connection from: %s:%d" % (addr[0],addr[1]))

            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()

        except:
            continue


main()