# -*- conding: utf-8 -*-

import socket
import threading
import select
import os, sys

HEADER_LENGTH = 10
bind_port = 1234
bind_ip =  "192.168.165.8"

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

server_socket.listen(10)

sockets_mutex = threading.Lock()
sockets_list = []
clients_dict = {}

print("[*] Listening on %s:%d" % (bind_ip,bind_port))

def handle_client(client_socket):
    global sockets_list
    global clients_dict

    print("THREAD DE USUÁRIO CRIADA")
    
    while True:

        try:

            message_header_rcv = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

            print("\nSOLICITAÇÃO DE USUÁRIO\n")

            message_parse = message_header_rcv.split()
            command = message_parse[0]

            #Pedido pra listar usuários conectados
            if command == LIST_USERS:
                print("Pedido: Listar usuário")
                users_names = ""

                for client in clients_dict:
                    print(clients_dict[client]['header'])
                    print(clients_dict[client]['nick'])
                    if client != client_socket:
                        nick_string = clients_dict[client]['nick'] + "\n"
                        users_names += nick_string

                print(users_names)

                message_header = f"{LIST_USERS} {len(users_names)}"
                message_header = f"{message_header:<{HEADER_LENGTH}}".encode('utf-8')

                print(message_header)

                client_socket.send(message_header + users_names.encode('utf-8'))

            #Pedido de troca de nick
            elif command == NEW_NICK:
                print("Pedido: Troca de nick")
                nick_length = int(message_parse[1])
       
                new_nick_try = client_socket.recv(nick_length).decode('utf-8')

                print("Novo nick: ", new_nick_try)

                can_change = True

                for client in sockets_list:
                    if client != client_socket:
                        if clients_dict[client]['nick'] == new_nick_try:
                            can_change = False
                            break

                message_header = f"{NEW_NICK}"

                if can_change:
                    clients_dict[client_socket]['header'] = len(new_nick_try)
                    clients_dict[client_socket]['nick'] = new_nick_try

                    message_header = f"{message_header} {NICK_CHANGED} {nick_length}"
                    message_header = f"{message_header:<{HEADER_LENGTH}}".encode('utf-8')

                    print("HEADER: ", message_header)

                    client_socket.send(message_header + new_nick_try.encode('utf-8'))

                else:
                    message_header = f"{message_header} {NICK_EXIST}"
                    message_header =f"{message_header:<{HEADER_LENGTH}}".encode('utf-8')

                    print("HEADER: ", message_header)

                    client_socket.send(message_header)


            #envio de mensagem
            elif command == MESSAGE:
                # print("Pedido: Mensagem")
                message_size = int(message_parse[1])
                # print("Tamanho da mensagem = ", message_size)

                message = client_socket.recv(message_size).decode('utf-8')

                # print(message)

                client_nick_size = clients_dict[client_socket]['header']
                client_nick = clients_dict[client_socket]['nick']

                parcial_header = f"{MESSAGE} {client_nick_size} {message_size}"

                # print("Header Parcial = ", parcial_header)

                message_header = f"{parcial_header:<{HEADER_LENGTH}}".encode('utf-8')

                # print("Header Final = ", message_header)

                message_to_send = message_header + client_nick.encode('utf-8') + message.encode('utf-8')

                for socket in sockets_list:
                    if socket != client_socket:

                        socket.send(message_to_send)


            elif command == FILE:
                # print("Pedido: Arquivo")
                #Recebimento do arquivo
                file_name_size = int(message_parse[1])
                
                file_name = client_socket.recv(file_name_size)

                file_data_size = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())

                file_bytes = client_socket.recv(file_data_size)

                #prepara para fazer o broadcast do arquivo

                message_header = f"{FILE} {clients_dict[client_socket]['header']}"
                message_header_1 = f"{message_header:<{HEADER_LENGTH}}".encode('utf-8')
                message_header_1 = message_header_1 + clients_dict[client_socket]['nick'].encode('utf-8')
                
                message_header_2 = f"{file_name_size:<{HEADER_LENGTH}}".encode('utf-8')
                message_header_2 = message_header_2 + file_name

                message_header_3 = f"{file_data_size:<{HEADER_LENGTH}}".encode('utf-8')
                message_header_3 = message_header_3 + file_bytes


                for socket in sockets_list:
                    if socket != client_socket:
                        socket.send(message_header_1 + message_header_2 + message_header_3)

                                         
            elif command == QUIT:
                #finalizando recursos de usuário
                print("Finalizando conexão com usuário")
                break

        except IndexError as e:
            print("Erro de comunicação - Conexão precisa ser fechada")
            print("Error: {}".format(str(e)))
            break

        except Exception as e:
            print("Error: {}".format(str(e)))
            continue

  
    del clients_dict[client_socket]
    sockets_list.remove(client_socket)

    client_socket.close()


def main():
    #Só vai emitir a thread de cliente se a conexão for bem sucedida
    while True:

        try:

            print("Aguardando conexões...")
            client_socket,addr = server_socket.accept()

            print("[*] Tentativa de conexão de: %s:%d" % (addr[0],addr[1]))

            rcv_message_header = client_socket.recv(HEADER_LENGTH)
            
            nick_length = int(rcv_message_header.decode('utf-8').strip())
            user_nick = client_socket.recv(nick_length).decode('utf-8')

            if len(sockets_list):
                nick_existent = False

                for client in clients_dict:
                    if clients_dict[client]['nick'] == user_nick:
                        nick_existent = True
                        break

                if nick_existent:
                    snd_message_header = f"{NICK_EXIST:<{HEADER_LENGTH}}".encode('utf-8')

                    client_socket.send(snd_message_header)

                    client_socket.close()

                    continue

            clients_dict[client_socket] = {'header': nick_length, 'nick': user_nick}
            sockets_list.append(client_socket)

            snd_message_header = f"{CONN_ACCEP:<{HEADER_LENGTH}}".encode('utf-8')

            client_socket.send(snd_message_header)

            print("[*] Accepted connection from: %s:%d" % (addr[0],addr[1]))

            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()

        except Exception as e:
            print("Exception Message: {}".format(str(e)))
            print("\n")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            continue


main()
