# -*- conding: utf-8 -*-

import socket
import subprocess
import sys, os
from pathlib import Path
import errno
import time
import threading

FILES_PATH =  str(Path.home())+"/chatRoom/"

HEADER_LENGTH = 10
bind_port = 1234
bind_ip = "192.168.165.8"

CONN_ACCEP   = "ACC"
NICK_EXIST   = "NE"
NICK_CHANGED = "NC"
RECEIVED     = "ACK"

LIST_USERS     = "list"
NEW_NICK       = "nick"
MESSAGE        = "msg"
FILE_CMD       = "sendFile"
FILE_HEADER    = "file"
QUIT           = "quit"
HELP           = "help"
CLEAR          = "clear"

LIST_OF_COMMANDS = '''
LISTA DE COMANDOS\n
\n
Comando   [param]            Descrião\n\n
/list                           Lista todos os usuários conectados\n
/help                           Lista os comandos disponíveis\n
/clear                          Limpa a janela do usuário\n
/quit                           Desconecta do servidor\n
/nick      novo_nick            Trocar apelido\n
/sendFile  nome_do_arquivo.ext  Enviar arquivo\n\n
'''

my_username = ""

def senderThread(client_socket):
    global my_username

    while True:

        try:

            user_input = input(f'{my_username} >> ')

            #se tiver alguma coisa no input
            if len(user_input):

                #checa se é um comando
                if user_input[0] == "/":
                    command_list = user_input[1:].split()

                    command = command_list[0]

                    if command == LIST_USERS:
                        message_header = f"{LIST_USERS:<{HEADER_LENGTH}}".encode('utf-8')

                        client_socket.send(message_header)


                    elif command == NEW_NICK:
                        nick = command_list[1]

                        header = f"{NEW_NICK} {len(nick)}"

                        message_header = f"{header:<{HEADER_LENGTH}}".encode('utf-8')

                        final_message = message_header + nick.encode('utf-8')

                        client_socket.send(final_message)

                    
                    elif command == FILE_CMD:

                        filePath = command_list[1]

                        print("FILE PATH = ", filePath)

                        fileName = filePath.split("/")[-1]

                        print("FILE NAME = ", fileName)

                        header = f"{FILE_HEADER} {len(fileName)}"

                        print("FILE HEADER = ", header)

                        message_header_1 = f"{header:<{HEADER_LENGTH}}".encode('utf-8')

                        file_name_header = fileName.encode('utf-8')

                        myFile = open(filePath, 'rb')
                        fileBytes = myFile.read()
                        fileSize = len(fileBytes)

                        print("FILE SIZE = ", fileSize)

                        message_header_2 = f"{fileSize:<{HEADER_LENGTH}}".encode('utf-8')

                        final_message = message_header_1 + file_name_header + message_header_2 + fileBytes
                        
                        #envia o header com o tamanho do arquivo seguido do nome do arquivo
                        client_socket.send(final_message)

                        myFile.close()


                    elif command == QUIT:
                        message_header = f"{QUIT:<{HEADER_LENGTH}}".encode('utf-8')
                        client_socket.send(message_header)
                        print("ADEUS!")
                        sys.exit()

                    elif command == HELP:
                        print(LIST_OF_COMMANDS)

                    elif command == CLEAR:
                        subprocess.call("reset")

                    else:
                        print("Comando inválido")

                #se não é um comando é uma mensagem
                else:
                    
                    header = f"{MESSAGE} {len(user_input)}"
                    message_header = f"{header:<{HEADER_LENGTH}}".encode('utf-8')
                    message = user_input.encode('utf-8')
                    
                    final_message = message_header + message
                    client_socket.send(final_message)

        except Exception as e:
            print("Erro: {}".format(str(e)))


def receiverThread(client_socket):
    global my_username
        
    while True:
    
        #loop em mensagem recebidas
        try:
            #print("\n THREAD MENSAGENS RECEBIDAS \n")
            recv_usr_header = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

            parsed_header = recv_usr_header.split()
            server_message = parsed_header[0]

            # print("\n FOI RECEBIDA MENSAGEM EM RECEIVER THREAD")
            # print("MENSAGEM DO SERVIDOR: ", server_message)
            if server_message == MESSAGE:

                nick_sender_size = int(parsed_header[1])
                recv_message_size = int(parsed_header[2])

                nick_sender = client_socket.recv(nick_sender_size).decode('utf-8')

                sent_message = client_socket.recv(recv_message_size).decode('utf-8')

                print("{} >> {}".format(nick_sender, sent_message))


            elif server_message == LIST_USERS:
                #print("\nRECEBIDO LISTAGEM\n")
                sizeof_list = int(parsed_header[1])

                if sizeof_list == 0:
                    print("Você está sozinho aqui!")

                else:
                    list_data = client_socket.recv(sizeof_list).decode('utf-8')

                    print(list_data)

            elif server_message == NEW_NICK:

                server_response = parsed_header[1]
                
                if server_response == NICK_EXIST:
                    print("Nick já em uso")

                elif server_response == NICK_CHANGED:
                    nick_len = int(parsed_header[2])
                    print("TAMANHO NOVO NICK ", nick_len)
                    nick = client_socket.recv(nick_len).decode('utf-8')

                    my_username = nick
                    print("Nick trocado com sucesso")

                else:
                    print("Erro de conexão")
                    print("Fechando Cliente")
                    sys.exit()

            elif server_message == FILE_HEADER:

                print("=+=+=+=+=+=+= Recebendo Arquivo =+=+=+=+=+=+=")

                nick_sender_size = int(parsed_header[1])

                print("TAM NICK SENDER = ", nick_sender_size)

                nick_sender = client_socket.recv(nick_sender_size).decode('utf-8')

                print("NICK SENDER = ", nick_sender)

                recv_file_name_size = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())

                print("FILE NAME SIZE = ", recv_file_name_size)

                file_name = client_socket.recv(recv_file_name_size).decode('utf-8')

                print("FILE NAME = ", file_name)

                file_size = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())

                print("FILE SIZE = ", file_size)

                file_data = client_socket.recv(file_size)
                
                complete_file_path = FILES_PATH + file_name


                myFile = open(complete_file_path, 'wb')

                myFile.write(file_data)

                print("{} enviou o arquivo {}".format(nick_sender, complete_file_path))

                myFile.close()

        except IOError as e:

            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print("Erro de leitura 1: {}".format(str(e)))
                sys.exit()

            continue

        except IndexError as e:
            print("Erro de conexão: {}".format(str(e)))
            print("\n Saindo do Programa\n")
            sys.exit()


        except Exception as e:

            print("Erro de leitura 2: {}".format(str(e)))
            sys.exit()


def main():
    global my_username

    subprocess.call("reset")

    print("Criando diretório para receber arquivos\n")

    try:
        subprocess.call(["mkdir", FILES_PATH])

    except subprocess.SubprocessError as e:
        print("Erro: {}\n".format(str(e)))

    print("\n")

    while True:

        my_username = input("Username: ")

        if len(my_username):

            try:

                print("Requisitando conexão...")
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((bind_ip, bind_port))

                username = str(my_username).encode('utf-8')
                username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
                client_socket.send(username_header + username)

                response = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                if response == CONN_ACCEP:
                    print("CONEXÃO ESTABELECIDA")
                    print("BEM VIND@")
                    break

                elif response == NICK_EXIST:
                    print("Nick em uso")
                    client_socket.close()

                else:
                    print("BUG: ", response)
                    client_socket.close()

            except Exception as e:
                print("Mensagem de erro: {}".format(str(e)))
                print("\n")
                exc_type, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                client_socket.close()

        else:
            print("Nick inválido")

    sender_handler = threading.Thread(target=senderThread, args=(client_socket,))
    receiver_handler = threading.Thread(target=receiverThread, args=(client_socket,))

    sender_handler.start()
    receiver_handler.start()



main()
