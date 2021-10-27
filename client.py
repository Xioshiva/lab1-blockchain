import json
import socket

def kill_node(id,address):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((address, 8080+id))
            m = json.dumps({'sender':'kill','type':'kill', 'message':'kill'})
            s.sendall(bytes(m,"utf-8"))
            s.close()


def kill_all_nodes(n,address):
    for i in range(n):
        kill_node(i+1,address)





def client(n,ip):
    on = 1
    while on:
        addr = input("address ? ")
        port = int(input("port ? "))
        if port == 0:
            kill_all_nodes(n,ip)
            on = 0
            break

        type = input('command ? ')
        jsonb = None

        if type == "create_transaction":
            sender = int(input('sender ? '))
            receiver = int(input('receiver ? '))
            amount = int(input('amount ? '))

            jsonb = {"type": type, 'transaction':{'sender':sender,'receiver':receiver,'amount':amount}}

        elif type == "fake":
            jsonb = {"type": type, 'transaction':{'sender':12,'receiver':23,'amount':100}}

        else:
            jsonb = {"type": type}
        data_send = json.dumps(jsonb)

        

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((ip,8080))
            s.connect((addr, port))
            s.sendall(bytes(data_send,"utf-8"))
            s.shutdown(socket.SHUT_RDWR) 



client(6,'127.0.0.1')