import yaml
import socket
import threading
import json
import sys
from ipaddress import ip_interface

class Node:

    def __init__(self,id,parent,address):
        self.id = id
        self.address = address
        self.parent = parent
        self.neighbours = []
        self.transactions = []

    def addNeighbour(self,*n):
        for i in n:

            if i.id != self.id:
                self.neighbours.append(i)
            else:
                print("you cannot add the parent or the node himself as neighbour !")
    
    def addTransaction(self,t):
        self.transactions.append(t)

    def __str__(self):
        parent = None
        if self.id !=0 and self.parent != None:
            parent = self.parent.id

        return f"""
        NODE
        ================================
        ID: {self.id}
        Parent ID: {parent}
        Address: {self.address}
        Neighbours: {self.neighbours}
        Transactions {self.transactions}
        ================================
        """
    def __repr__(self):
        return f"Node(ID='{self.id}', " \
               f"{self.address})"
            

    def __eq__(self,other):
        return True if self.id == other.id else False


class Neighbour:

    def __init__(self,id,address):
        self.id = id
        self.address = address
    
    def __str__(self):

        return f"""
        NEIGHBOUR
        ================================
        ID: {self.id}
        Address: {self.address}
        ================================
        """

    def __repr__(self):
        return f"Neighbour(ID='{self.id}', " \
               f"address: {self.address})"
            

    def __eq__(self,other):
        return True if self.id == other.id else False


class Transaction:

    def __init__(self,id,sender,receiver,amount,isFake):
        self.id = id
        self.receiver = receiver
        self.sender = sender
        self.amount = amount
        self.isFake = isFake
    
    def __str__(self):

        return f"""
        TRANSACTION
        ================================
        ID: {self.id}
        Receiver: {[self.receiver]}
        Sender: {[self.sender]}
        Amount: {self.amount}
        isFake: {self.isFake}
        ================================
        """

    def __repr__(self):
        return f"Transaction(ID='{self.id}'," \
               f"amount: '{self.amount}'," \
               f"sender: '{self.sender}'," \
               f"receiver: {self.receiver})"
            

    def __eq__(self,other):
        return True if self.id == other.id else False



 

def yamlConvert(filename):

    nodes = None

    with open(filename,"r") as file:
        nodes = yaml.load(file, Loader=yaml.FullLoader)

    test = []

    for node in nodes:
        nouveau = Node(node["id"],None,node["address"])
        for neighbour in node["neighbours"]:
            nouveau.addNeighbour(Neighbour(neighbour["id"],neighbour["address"]))
        test.append(nouveau)

    return test




def send_to_all_neighbours(node,m,info,exc):              
    for neighbour in node.neighbours:
        if int(neighbour.address) == int(exc):
            continue
        send_to(m, int(neighbour.address))


def send_to(m,port):
    on = 1
    while on:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:     
                s.connect(('127.0.0.1', port))
                s.sendall(m)
                s.close()
        except Exception as e:
            print(e)
        else:
            on = 0



def broadcast_by_waves(node,port,data,info):

    """"ip1 = ip_interface(addr1)
    ip2 = ip_interface(addr2)
    if ip1.network.overlaps(ip2.network):"""

    if port == 8080:
        info[1] = True
        send_to_all_neighbours(node,data,info,8080)
        return
      
    info[0] += 1
    if info[1] == False:
        info[1] = True
        send_to_all_neighbours(node,data,info,8080)


def broadcast_by_waves_with_ack(node,port,data,info,vote):
    
    if port == 8080:
        info[1] = True
        send_to_all_neighbours(node,data,info,8080)
        return
      
    info[0] += 1
    if info[1] == False:
        info[1] = True
        info[2] = node.address
        send_to_all_neighbours(node,data,info,info[2])

    if info[0] == len(node.neighbours) and info[2] != None:
        str_data = data.decode("utf-8")
        json_data = json.loads(str_data)

        
        json_data.update({'rate':vote})

        data = bytes(json.dumps(json_data),"utf-8")
        send_to(data, int(info[2]))


def rate(sended_trans, local_trans):

    val1 = 0
    val2 = len(local_trans)

    for i in range(len(sended_trans)):
        for j in range(val2):
            if sended_trans[i] == local_trans[j].id:              
                val1 +=1
    return val1,val2
            
    

def server(address,idn):

    import socket

    node = yamlConvert('node'+str(idn)+'.yaml')[0]
    name = "node " + str(node.id)
    on = 1
    #INFO 0 = count INFO 1 = reach INFO 2 = parent
    count = 0
    reach = False
    parent = None
    info = [count,reach,parent]
    id_trans = 0
    json_data = None
    data = None
    vote = None

    print("{} Launched !".format(name)) 

    while(on):
        
        if count == len(node.neighbours):
            info[0] = 0
            info[1] = False
            info[2] = None
            print(vote)
            vote = None

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((address, int(node.address)))
            s.listen()
            conn, addr = s.accept()
            with conn:
                
                print('Connected to ', s.getsockname()[1])
                while True:
                    
                    recv = conn.recv(2048)
                    port = addr[1]
                    
                    if not recv:
                        break
                    data = recv

            str_data = data.decode("utf-8")
            json_data = json.loads(str_data)

            if json_data['type'] == "kill":
                on = 0

            if json_data['type'] == "fake":
                trans = Transaction(-1*(id_trans+1), json_data['transaction']['sender'], json_data['transaction']['receiver'], json_data['transaction']['amount'], False)
                node.transactions.append(trans)

            if json_data['type'] == "create_transaction":
                if reach == False:
                    trans = Transaction(id_trans, json_data['transaction']['sender'], json_data['transaction']['receiver'], json_data['transaction']['amount'], False)
                    node.transactions.append(trans)
                    id_trans += 1
                test = threading.Thread(target=broadcast_by_waves, args=(node,int(port),data,info))
                test.start()

            if json_data['type'] == 'list_of_trans':
                print(node.transactions)
                    
            if json_data['type'] == 'rate':
                        
                if int(port) == 8080:
                    transactions = []
                    for trans in node.transactions:
                        transactions.append(trans.id)

                    json_data.update({'trans':transactions})
                    data = bytes(json.dumps(json_data),"utf-8")
                    test = threading.Thread(target=broadcast_by_waves_with_ack, args=(node,int(port),data,info,0))
                    test.start()
                else:
                    #print(json_data['rate'])
                    vote = rate(json_data['trans'],node.transactions)
                    test = threading.Thread(target=broadcast_by_waves_with_ack, args=(node,int(port),data,info,vote))
                    test.start()
                
            #print("{} received: {}".format(name,json_data['type']))
            s.close()



    
if __name__ == "__main__":
  
    
    address = sys.argv[1]
    idn = sys.argv[2] 
    server(address, idn)

    """for idn in range(1,7):

        node = threading.Thread(target=server, name="socket {}".format(idn), args=(address,idn))
        node.start()"""
        

    
  
  








