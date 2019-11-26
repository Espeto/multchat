import socket

bind_port = 9999
bind_ip = "127.0.0.1"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket((bind_ip, bind_port))

response = client_socket.recv(4096)
print(response.decode("utf-8"))