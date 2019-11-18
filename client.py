# Python 3
# Usage: python3 UDPClient3.py localhost 12000
# coding: utf-8
from socket import *
import sys
import json
import threading
import os


def login():
        global usr
        global pas

        usr = input("Username: ")
        pas = input("Password: ")    
        message = json.dumps({"username": usr, "password": pas})  # serialise
        clientSocket.send(message.encode())

def receivePrivate():
    #create another main socket that you bind to and listen for
    #peers who want to PM you
    privPort = 12000
    privateSocket = socket(AF_INET, SOCK_STREAM)
    
    privateSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    #bind it to port 0, which means "any port"

    
    #once you accept something start a new thread



    #IDEA????? use same port your using to connect w server????

    #start send thread to private peers
    # recvThread=threading.Thread(name="RecvHandler", target=receive)
    # recvThread.daemon=True
    # recvThread.start()


def handlePrivate(peerSocket, addr, usr):
    while True:
        print("what")





def send(): #send to server
    while True:
        msg = input('\n > ')
        clientSocket.send(msg.encode())

        #if the command is "private" try to 
            # see if a connection exist w the person
            # else: "Error. Private messaging to ____ not enabled"
        #else pass to server

def receive():
    while True:
        
        data = clientSocket.recv(2048).decode()
        if data[:15] == "approvedPrivate":
            m = data.split(' ', 3)
            user = m[1]
            sock = m[2]
            port = m[3]
            #start another thread to talk private
            print("starting private")

        if (data == "LOG_OUT"):
            #close the socket and end program
            clientSocket.close()
            os._exit(0)
            #threading.current_thread()._stop
            #_thread.interrupt_main()
        
        print('\n' + ' > ' + str(data))


#START OF THE MAIN PROGRAM HERE

# python client.py server_IP server_port
# Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

p2p = {} #dict of people you currently are private messaging

# first send the login info
login()

receivedMessage = clientSocket.recv(2048)
decoded = receivedMessage.decode()

#while the server keeps asking you to login, try logging in
while ( decoded != "Welcome! You can now start messaging!"):
        print(decoded)
        if (decoded == "Invalid username. Please try again"):
            login() #login and send to server
        elif (decoded == "Invalid login. Please try again"):
            print("user is "+usr)
            pas = input("Password: ")    
            message = json.dumps({"username": usr, "password": pas})  # serialise
            clientSocket.send(message.encode())
        elif decoded == "You're already logged in.":
            clientSocket.close()
            exit()
        else: #blocked
            login() ##ask them to login again? or just close connection?
        
        #ask for message again
        decoded = clientSocket.recv(2048).decode()

#successfully logged in:
print("made it here")
print(decoded)


#start receive thread from private peers
servePrivate=threading.Thread(name="servePrivate", target=receivePrivate)
servePrivate.daemon=True
servePrivate.start()

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



