import socket

HEADER_LENGTH = 10

CONN_ACCEP = "ACC"
NICK_EXIST = "NE"
RECEIVED = "ACK"

LIST_USERS = "list"
NEW_NICK = "nick"
MESSAGE = "msg"
FILE = "file"
QUIT = "quit"

bind_port = 9999
bind_ip = "127.0.0.1"
my_username = ""

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


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket((bind_ip, bind_port))
    client_socket.setblocking(False)

    while True:

        my_username = input("Username: ")

        if len(my_username) > 0:

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

        else:
            print("Nick inválido")

    while True:

        user_input = input(f'{my_username} >> ')

        if user_input:

            split_input = user_input.split("/")