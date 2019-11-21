# Python 3
# Usage: python3 UDPClient3.py localhost 12000
# coding: utf-8
from socket import *
import sys
import json
import threading
import os
import time

p2p = {} #dict of people you currently are private messaging

def login(port):
        global usr
        global pas

        usr = input("Username: ")
        pas = input("Password: ")    
        message = json.dumps({"username": usr, "password": pas, "privPort": port})  # serialise
        clientSocket.send(message.encode())

def invalid_command(sock):
    message = " > Please type a valid command."
    sock.send(message.encode())

#function that listens for private messages 
def listenPrivate():
    global usr

    while True:
        #accept connections from peers
        connectionSocket, addr = privateSocket.accept()

        #receive the “startprivate <A>”
        m = connectionSocket.recv(2058).decode().split()
        peer = m[1]
        #Adds A to list of p2p{usr: peersocket}
        p2p[peer] = connectionSocket
        
        #Sends “privateACK <B>” to A once
        message = "privateACK " + usr
        connectionSocket.send(message.encode())

        #make new thread per peer connection 
        newPeerThread = threading.Thread(name="NewPeer", target=handlePrivate, args=(connectionSocket, addr))
        newPeerThread.daemon=True #shut down immediately when program exits
        newPeerThread.start()

#function that handles receiving private messaging        
def handlePrivate(peerSocket, addr):
    while True:
        try:
            message = peerSocket.recv(2058).decode()
        except OSError: #OSerror if the connection was abruptly closed (stopped private)
            sys.exit()

        m = message.split()
        #privateACK <B>
        if m[0] == "privateACK":
            print(" > Start private messaging with "+m[1])
        
        #stopprivate <user> received from a peer
        elif m[0] == "stopprivate":
            if len(m) != 2:
                invalid_command(peerSocket)
            else:
                peer = m[1]
                print(" > " + peer + " wishes to discontinue private messaging session.")
                
                #find the socket of peer and close
                sock = p2p[peer]
                sock.close()
                del p2p[peer]
                sys.exit() #close this thread

        #user logged off before executing stop private
        elif m[0] == "LOGOUT":
            peer = m[1]
            peerSocket.close()
            del p2p[peer]
            sys.exit()
            
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
    handlePrivate(peerSocket, addr)

def send(): #send to server or peer
    global usr
    while True:
        time.sleep(0.02)
        msg = input(' > ')

        m = msg.split(' ', 1)
        #if the message you sent was "start private" before sending to 
        #server, check that you havent already started a connection w them 
        #by checking p2p
        if m[0] == "startprivate":
            if len(m) != 2: #name of user not provided
                print(" > Please type a valid command")
            elif m[1] in p2p:
                print(" > You have already enabled private messaging with " + m[1])
            else:
                clientSocket.send(msg.encode())

        #the message you're trying to send is private
        #private <user> <message>
        elif m[0] == "private":
            m = msg.split(' ', 2)
            if len(m) != 3: #incomplete command
                print(" > Please type a valid command")
            
            else:
                peer = m[1]
                message = " > " + usr + "(private): " + m[2]

                #check if you've established a connection w this peer
                if peer in p2p:
                    sock = p2p[peer]
                    try:
                        sock.send(message.encode())
                    except OSError: #catch os error in case abrupt connection loss
                        del p2p[peer]
                        sock.close()
                        print(" > Error. Lost connection to "+peer)
                
                #otherwise: ERROR
                else:
                    print(" > Error. Private messaging to " + peer + " not enabled")
        
        #Stopprivate <user> 
        elif m[0] == "stopprivate":
            if len(m) != 2:
                print(" > Please type a valid command")
            else: 
                peer = m[1]
                message = "stopprivate "+usr
                if peer in p2p:
                    sock = p2p[peer]
                    sock.send(message.encode())
                    #close the connection
                    del p2p[peer]
                    sock.close()

                #error message displayed if no active p2p
                else:
                    print(" > Error. Private messaging to " + peer + " not enabled")

        #other messages sent to server
        else:
            clientSocket.send(msg.encode())
        
        time.sleep(0.02)

#receive messages from server
def receive():
    global usr
    while True:
        try:
            data = clientSocket.recv(2048)
        
        #catch OSError - abrupt logouts
        except OSError: 
            sys.exit() #close receive thread
        
        data = data.decode()
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

        elif (data == "LOG_OUT"):
            clientSocket.close()
            #if theres ongoing p2p connections message them that youre logging out
            message = "LOGOUT "+usr
            for p in p2p:
                sock = p2p[p]
                sock.send(message.encode())
                sock.close()

            # shut down program
            os._exit(0)
        
        else:
            print(" > " + str(data))
            time.sleep(0.05)
            


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
while ( decoded != "SUCCESS"):
        if (decoded == "INVALID_USR"):
            print("Invalid username. Please try again")
            login(privPort) #login and send to server
        elif (decoded == "INVALID_PAS"):
            print("Invalid login. Please try again")
            print("Username: "+usr)
            pas = input("Password: ")   
            message = json.dumps({"username": usr, "password": pas, "privPort": privPort})  # serialise 
            clientSocket.send(message.encode())
        else: #blocked or "You're already logged in."
            print(decoded)
            clientSocket.close()
            exit()

        #ask for message again
        decoded = clientSocket.recv(2048).decode()

#successfully logged in:
print("Welcome! You can now start messaging!")


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