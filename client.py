# Python 3
# Usage: python3 UDPClient3.py localhost 12000
# coding: utf-8
from socket import *
import sys
import json
import threading


def login():
        global usr
        global pas

        usr = input("Username: ")
        pas = input("Password: ")    
        message = json.dumps({"username": usr, "password": pas})  # serialise
        clientSocket.send(message.encode())


def send(): #send to server
    while True:
        msg = input('\nMe > ')
            
        clientSocket.send(msg)

def receive():
    while True:
        sen_name = clientSocket.recv(2048)
        data = clientSocket.recv(2048)

        print('\n' + str(sen_name) + ' > ' + str(data))


# python client.py server_IP server_port
# Server would be running on the same host as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))


# first send the login info
login()

receivedMessage = clientSocket.recv(2048)
decoded = receivedMessage.decode()

#while the server keeps asking you to login, try logging in
while ( decoded != "Welcome! You can now start messaging!"):
        if (decoded == "Invalid username. Please try again"):
            print(decoded)
            login() #login and send to server
        elif (decoded == "Invalid login. Please try again"):
            print(decoded)
            print("user is "+usr)
            pas = input("Password: ")    
            message = json.dumps({"username": usr, "password": pas})  # serialise
            clientSocket.send(message.encode())
        else: #blocked
            print(decoded)
            login()
        
        #ask for message again
        decoded = clientSocket.recv(2048).decode()

#successfully logged in:
print("made it here")
print(receivedMessage.decode())
#start 2 new threads - one for sending/receiving
    # send_thread=threading.Thread(name="SendHandler",target=send)
    # send_thread.daemon=True
    # send_thread.start()

    # recv_thread=threading.Thread(name="RecvHandler", target=receive)
    # recv_thread.daemon=True
    # recv_thread.start()
#clientSocket.close()

    
    
    

    # message = input().split()  # wait for the input
    # # send the message back to server
    # # wait for reply

    # # prepare to exit. Send Unsubscribe message to server
    # # clientSocket.sendto(message.encode(),(serverName, serverPort))
    

    # after finishing the loop close the socket



