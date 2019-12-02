import socket
import threading
import select
import os

HEADER_LENGTH = 10
bind_port = 1234
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

server_socket.listen(10)

sockets_mutex = threading.Lock()
sockets_list = []
clients_dict = {}

print("[*] Listening on %s:%d" % (bind_ip,bind_port))

def handle_client(client_socket):

    print("THREAD DE USUÁRIO CRIADA")
    
    while True:

        try:

            message_header_rcv = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

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
       
                new_nick_try = client_socket.recv(nick_length).decode('utf-8')

                if not len(new_nick_try):
                    print("Prolema na conexão")
                    break

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


            #envio de mensagem
            elif command == MESSAGE:

                message_size = int(message_parse[1])

                message = client_socket.recv(message_size)

                if not len(message):
                    print("Problema na comunicação")
                    break

                client_nick_size = clients_dict[client_socket]['header']
                client_nick = clients_dict[client_socket]['header']

                parcial_header = f"{MESSAGE} {client_nick_size} {message_size}"

                message_header = f"{parcial_header:<{HEADER_LENGTH}}".encode('utf-8')

                message_to_send = message_header + client_nick.encode('utf-8') + message.encode('utf-8')

                for socket in sockets_list:
                    if socket != client_socket:

                        socket.send(message_to_send)


            elif command == FILE:

                #Recebimento do arquivo
                file_name_size = int(message_parse[1])
                
                file_name = client_socket.recv(file_name_size).decode('utf-8')

                if not len(file_name):
                    print("PROBLEMA COM A COMUNICAÇÃO")
                    break

                server_response = f"{RECEIVED:<{HEADER_LENGTH}}".encode('utf-8')

                #envia um ack confirmando reccebimento do nome arquivo
                client_socket.send(server_response)

                file_size = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())

                if not file_size:
                    print("PROBLEMA COM A COMUNICAÇÃO")
                    break

                server_response = f"{RECEIVED:<{HEADER_LENGTH}}".encode('utf-8')

                #envia um ack confirmando reccebimento do tamanho do arquivo
                client_socket.send(server_response)

                #Recebe os dados do arquivo
                file_data = client_socket.recv(file_size)

                if not len(file_data):
                    print("Problema na conexão")
                    break

                #prepara para fazer o broadcast do arquivo

                message_header = f"{FILE} {clients_dict[client_socket]['header']}"
                message_header = f"{message_header:<{HEADER_LENGTH}}".encode('utf-8')

                for socket in sockets_list:
                    if socket != client_socket:
                        socket.send(message_header + clients_dict[client_socket]['nick'].encode('utf-8'))

                        socket_response = socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                        #Cliente recebeu mensagem com nick do emissor
                        if socket_response == RECEIVED:

                            server_response = f"{file_name_size:<{HEADER_LENGTH}}".encode('utf-8')

                            #Enviando o header com tamanho do nome do arquivo mais o nome
                            socket.send(server_response + file_name.encode('utf-8'))

                            socket_response = socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                            #Aguarda o ack confirmando o recebimento
                            if socket_response == RECEIVED:

                                server_response = f"{file_size:<{HEADER_LENGTH}}".encode('utf-8')

                                #Envia o header com o tamanho do arquivo
                                socket.send(server_response)
                                
                                #Aguarda o Ack de recebimento
                                socket_response = socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                                if socket_response == RECEIVED:
                                    #Envia os dados do arquivo
                                    socket.send(file_data)

                                else:
                                    print("PROBLEMA NA COMUNICAÇÃO")
                                    break

                        else:
                            print("PROBLEMA NA COMUNICAÇÃO")
                            break
                            
            elif command == QUIT:
                #finalizando recursos de usuário
                print("Finalizando conexão com usuário")
                break

        except:
            #ocorreu alguma desconexão
            break 

    sockets_mutex.acquire()
    try:
        del clients_dict[client_socket]
        sockets_list.remove(client_socket)
    finally:
        sockets_mutex.release()

    client_socket.close()


def main():
    #Só vai emitir a thread de cliente se a conexão for bem sucedida
    while True:

        try:

            print("Aguardando conexões...")
            client_socket,addr = server_socket.accept()

            print("[*] Tentativa de conexão de: %s:%d" % (addr[0],addr[1]))

            rcv_message_header = client_socket.recv(HEADER_LENGTH)

            if not len(rcv_message_header):
                #continua no loop aguardando conexões
                print("RCV_MSG_HEADER VAZIO")
                client_socket.close()
                continue

            
            nick_length = int(rcv_message_header.decode('utf-8').strip())
            user_nick = client_socket.recv(nick_length).decode('utf-8')

            sockets_mutex.acquire()
            try:
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
            finally:
                sockets_mutex.release()

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