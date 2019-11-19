# Python 3
# Usage: python3 UDPClient3.py localhost 12000
# coding: utf-8
from socket import *
import sys
import json
import threading
import os

p2p = {} #dict of people you currently are private messaging

def login(port):
        global usr
        global pas

        usr = input("Username: ")
        pas = input("Password: ")    
        message = json.dumps({"username": usr, "password": pas, "privPort": port})  # serialise
        clientSocket.send(message.encode())



#function that listens for private messages 
def listenPrivate():
    global usr

    print('listening on port:', privateSocket.getsockname()[1])
    while True:
        #accept connections from peers
        connectionSocket, addr = privateSocket.accept()

        #receive the “startprivate <A>”
        m = connectionSocket.recv(2058).decode().split()
        peer = m[1]
        #Adds A to list of p2p{usr: peersocket}
        p2p[peer] = connectionSocket
        print("I added "+peer)
        
        #Sends “privateACK <B>” to A once
        message = "privateACK " + usr
        connectionSocket.send(message.encode())

        #make new thread per peer connection 
        newPeerThread = threading.Thread(name="NewPeer", target=handlePrivate, args=(connectionSocket, addr))
        newPeerThread.daemon=True #daemon thread will shut down immediately when program exits
        newPeerThread.start()

#function that handles receiving private messaging        
def handlePrivate(peerSocket, addr):
    while True:
        message = peerSocket.recv(2058).decode()
        m = message.split()
        #privateACK <B>
        if m[0] == "privateACK":
            print(" > Start private messaging with "+m[1])
        else:
            print(message)

#function to talk 
def initiatePrivate(peer, ip, port):
    global usr

    addr = (ip, port)
    #create a new socket to initiate w this peer
    peerSocket = socket(AF_INET, SOCK_STREAM)
    peerSocket.connect((ip, port))

    #sending “startprivate <A>” to B
    message = "startPrivate " + usr 
    peerSocket.send(message.encode())

    #add peer to people you're currently talking to
    p2p[peer] = peerSocket
    print("I added "+peer)
    handlePrivate(peerSocket, addr)



def send(): #send to server or peer
    global usr
    while True:
        msg = input('\n > ')

        m = msg.split(' ', 1)
        #if the message you sent was "start private" before sending to 
        #server, check that you havent already started a connection w them 
        #by checking p2p

        #the message you're trying to send is private
        #private <user> <message>
        if (m[0] == "private"):
            m = msg.split(' ', 2)
            peer = m[1]
            message = usr + ": " + m[2]

            #check if you've established a connection w this peer
            #if yes: send it to them
            if peer in p2p:
                sock = p2p[peer]
                sock.send(message.encode())
            
            #otherwise: print(>Error. Private messaging to ___ not enabled)

        else:
            clientSocket.send(msg.encode())

#receive messages from server
def receive():
    while True:
        
        data = clientSocket.recv(2048).decode()
        d = data.split()
        #message from server approving a start private action
        #startPrivateAck <user> <socket> <port>
        #Client uses this and starts a new thread where it tries to connect()
        if (d[0] == "startPrivateAck"): 
            m = data.split(' ', 3)
            peer = m[1]
            ip = m[2]
            port = int(m[3])

            #start another thread to talk private
            talkPrivateThread = threading.Thread(name="talkPrivate", target=initiatePrivate, args=(peer, ip, port))
            talkPrivateThread.daemon=True
            talkPrivateThread.start()

            print("starting private")

        elif (data == "LOG_OUT"):
            #close the socket and end program
            clientSocket.close()
            os._exit(0)
            #threading.current_thread()._stop
            #_thread.interrupt_main()
        
        else:
            print('\n' + str(data))


#START OF THE MAIN PROGRAM HERE

# python client.py server_IP server_port
# Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

privateSocket = socket(AF_INET, SOCK_STREAM)
privateSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
privateSocket.bind(('localhost', 0))
privPort = privateSocket.getsockname()[1]
privateSocket.listen(1)

# first send the login info
login(privPort)

receivedMessage = clientSocket.recv(2048)
decoded = receivedMessage.decode()

#while the server keeps asking you to login, try logging in
while ( decoded != "Welcome! You can now start messaging!"):
        print(decoded)
        if (decoded == "Invalid username. Please try again"):
            login(privPort) #login and send to server
        elif (decoded == "Invalid login. Please try again"):
            print("user is "+usr)
            pas = input("Password: ")    
            message = json.dumps({"username": usr, "password": pas})  # serialise
            clientSocket.send(message.encode())
        # elif decoded == "You're already logged in.":
        #     clientSocket.close()
        #     exit()
        else: #blocked or "You're already logged in."
            clientSocket.close()
            exit()

        #ask for message again
        decoded = clientSocket.recv(2048).decode()

#successfully logged in:
print("made it here")
print(decoded)


#start a new thread to handle listening for private messages
listenPrivThread=threading.Thread(name="listenPriv", target=listenPrivate)
listenPrivThread.daemon=True
listenPrivThread.start()

#start receive thread from server
recvThread=threading.Thread(name="RecvHandler", target=receive)
recvThread.daemon=True
recvThread.start()

# function that sends to server
send()

#clientSocket.close()

    
    
    

    # message = input().split()  # wait for the input
    # # send the message back to server
    # # wait for reply

    # # prepare to exit. Send Unsubscribe message to server
    # # clientSocket.sendto(message.encode(),(serverName, serverPort))
    

    # after finishing the loop close the socket



