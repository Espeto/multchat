import socket
import subprocess
import sys, os
from pathlib import Path
import errno
import time

FILES_PATH =  str(Path.home())+"/chatRoom/"

HEADER_LENGTH = 10
bind_port = 1234
bind_ip = "127.0.0.1"

CONN_ACCEP   = "ACC"
NICK_EXIST   = "NE"
NICK_CHANGED = "NC"
RECEIVED     = "ACK"

LIST_USERS = "list"
NEW_NICK   = "nick"
MESSAGE    = "msg"
FILE_CMD   = "sendFile"
FILE_HEADER    = "file"
QUIT       = "quit"
HELP       = "help"
CLEAR      = "clear"

LIST_OF_COMMANDS = '''
LISTA DE COMANDOS\n
\n
Comando   [param]            Descrião\n\n
/list                           Lista todos os usuários conectados\n
/help                           Lista os comandos disponíveis\n
/clean                          Limpa a janela do usuário\n
/quit                           Desconecta do servidor\n
/nick      novo_nick            Trocar apelido\n
/sendFile  nome_do_arquivo.ext  Enviar arquivo\n\n
'''

my_username = ""

def main():
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
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                client_socket.close()

        else:
            print("Nick inválido")


    while True:

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

                    server_response = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                    if server_response == NICK_EXIST:
                        print("Nick já em uso")

                    elif server_response == NICK_CHANGED:
                        my_username = nick
                        print("Nick trocado com sucesso")

                    else:
                        print("Erro de conexão")
                        print("Fechando Cliente")
                        sys.exit()
                
                elif command == FILE_CMD:

                    filePath = command_list[1]

                    fileName = filePath.split("/")[-1]

                    header = f"{FILE_HEADER} {len(fileName)}"

                    message_header = f"{header:<{HEADER_LENGTH}}".encode('utf-8')

                    message = fileName.encode('utf-8')

                    final_message = message_header + message
                    
                    #envia o header com o tamanho do arquivo seguido do nome do arquivo
                    client_socket.send(message_header)

                    response = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                    #Se recebeu ACK
                    #Prepara para enviar o tamanho do arquivo
                    if response == RECEIVED:

                        myFile = open(filePath, 'rb')
                        fileBytes = myFile.read()
                        fileSize = len(fileBytes)

                        message_header = f"{fileSize:<{HEADER_LENGTH}}".encode('utf-8')

                        #Envia o tamanho do arquivo
                        client_socket.send(message_header)

                        #Aguarda ACK confirmando recebimento do tamanho do arquivo
                        response = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                        #Se recebeu ACK o servidor está pronto para receber o arquivo
                        if response == RECEIVED:

                            client_socket.send(fileBytes)

                        else:
                            print("DEU RUIM ENVIO DE DADOS")

                    else:
                        print("DEU PROBLEMA AO ENVIAR O TAMANHO DO ARQUIVO")


                elif command == QUIT:
                    message_header = f"{QUIT:<{HEADER_LENGTH}}".encode('utf-8')
                    client_socket.send(message_header)

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

        try:
            #loop em mensagem recebidas
            while True:

                recv_usr_header = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

                if not len(recv_usr_header):
                    print("Servidor fechou a conexão")
                    sys.exit()

                parsed_header = recv_usr_header.split()
                server_message = parsed_header[0]

                if server_message == MESSAGE:

                    nick_sender_size = int(parsed_header[1])
                    recv_message_size = int(parsed_header[2])

                    nick_sender = client_socket.recv(nick_sender_size).decode('utf-8')

                    if not len(nick_sender):
                        print("Servidor fechou a conexão")
                        sys.exit()

                    sent_message = client_socket.recv(recv_message_size).decode('utf-8')

                    if not len(sent_message):
                        print("Servidor fechou a conexão")
                        sys.exit()

                    print("{} >>> {}".format(nick_sender, sent_message))

                elif server_message == FILE_HEADER:

                    nick_sender_size = int(parsed_header[1])

                    nick_sender = client_socket.recv(nick_sender_size).decode('utf-8')

                    if not len(nick_sender):
                        print("Servidor fechou a conexão")
                        sys.exit()

                    client_response = f"{RECEIVED:<{HEADER_LENGTH}}".encode('utf-8')

                    #Envia ack confirmando recebimento do nick de quem enviou o arquivo
                    client_socket.send(client_response)

                    #recebimento do tamanho do nome arquivo
                    file_name_size = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())

                    if not file_name_size:
                        print("Servidor fechou a conexão")
                        sys.exit()

                    file_name = client_socket.recv(file_name_size).decode('utf-8')

                    if not len(file_name):
                        print("Servidor fechou a conexão")
                        sys.exit()

                    complete_file_path = FILES_PATH + file_name

                    client_response = f"{RECEIVED:<{HEADER_LENGTH}}".encode('utf-8')

                    #Envia ack confirmando recebimento do nome arquivo
                    client_socket.send(client_response)

                    file_size = int(client_socket.recv(HEADER_LENGTH).decode('utf-8').strip())

                    if not file_size:
                        print("Servidor fechou a conexão")
                        sys.exit()

                    client_response = f"{RECEIVED:<{HEADER_LENGTH}}".encode('utf-8')

                    #Envia ack confirmando recebimento do tamanho do arquivo
                    client_socket.send(client_response)

                    file_data = client_socket.recv(file_size)

                    if not file_data:
                        print("Servidor fechou a conexão")
                        sys.exit()

                    myFile = open(complete_file_path, 'wb')

                    myFile.write(file_data)
                    myFile.close

                    print("{} enviou o arquivo {}".format(nick_sender, complete_file_path))

        except IOError as e:

            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print("Erro de leitura: {}".format(str(e)))
                sys.exit()

            continue
                
        except Exception as e:

            print("Erro de leitura: {}".format(str(e)))
            sys.exit()


main()