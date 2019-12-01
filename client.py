import socket
import subprocess
import sys
from pathlib import Path
import errno

FILES_PATH =  str(Path.home())+"/chatRoom/temp"

HEADER_LENGTH = 10
bind_port = 9999
bind_ip = "127.0.0.1"

CONN_ACCEP   = "ACC"
NICK_EXIST   = "NE"
NICK_CHANGED = "NC"
RECEIVED     = "ACK"

LIST_USERS = "list"
NEW_NICK   = "nick"
MESSAGE    = "msg"
FILE_CMD   = "sendFile"
FILE_HD    = "file"
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
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket((bind_ip, bind_port))
    client_socket.setblocking(False)

    print("Criando diretório para receber arquivos")

    try:
        subprocess.call(["mkdir", FILES_PATH])

    except subprocess.SubprocessError as e:
        print("Erro: {}".format(str(e)))


    while True:

        my_username = input("Username: ")

        if len(my_username):

            print("Requisitando conexão...")

            username = my_username.encode('utf-8')
            username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(username_header + username)

            response = client_socket.recv(HEADER_LENGTH).decode('utf-8').strip()

            if response == CONN_ACCEP:
                print("CONEXÃO ESTABELECIDA")
                print("BEM VIND@")
                break

            elif response == NICK_EXIST:
                print("Nick em uso")

            else:
                print("BUG: ", response)
                exit()

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
                
                elif command == FILE_CMD:

                    filePath = command_list[1]

                    fileName = filePath.split("/")[-1]

                    header = f"{FILE_HD} {len(fileName)}"

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

                        client_socket.send(message_header)

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

                recv_usr_header = client_socket.recv(HEADER_LENGTH)

                if not len(recv_usr_header):
                    print("Servidor fechou a conexão")
                    sys.exit()

                recv_usr_length = int(recv_usr_header.decode('utf-8').strip())

                recv_username = client_socket.recv(recv_usr_length).decode('utf-8')

                #aqui dentro tem que fazer o handle das mensagens enviadas
                #pelos outros usuários

        except IOError as e:

            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print("Erro de leitura: {}".format(str(e)))
                sys.exit()

            continue
                
        except Exception as e:

            print("Erro de leitura: {}".format(str(e)))
            sys.exit()

