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
        msg = input('\n > ')
        clientSocket.send(msg.encode())

def receive():
    while True:
        
        data = clientSocket.recv(2048).decode()
        if (data == "LOG_OUT"):
            #close the socket and end program
            clientSocket.close()
            exit()
        
        print('\n' + ' > ' + str(data))


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

#start receive new threads - one for sending/receiving
    # send_thread=threading.Thread(name="SendHandler",target=send)
    # send_thread.daemon=True
    # send_thread.start()

recv_thread=threading.Thread(name="RecvHandler", target=receive)
recv_thread.daemon=True
recv_thread.start()

send()


#clientSocket.close()

    
    
    

    # message = input().split()  # wait for the input
    # # send the message back to server
    # # wait for reply

    # # prepare to exit. Send Unsubscribe message to server
    # # clientSocket.sendto(message.encode(),(serverName, serverPort))
    

    # after finishing the loop close the socket



