# Sample code for Multi-Threaded Server
#Python 3
# Usage: python3 UDPserver3.py
#coding: utf-8
from socket import *
import threading
import time
import datetime as dt
import json
import sys
from queue import Queue 


t_lock=threading.Condition()
#will store clients info in this list
clients={} #dict of online users
log_blocked={} #dict of users who are currently blocked because failed to login
logins = {} #dict of all users, passwords, tries and people they block
pending_msg = {} #dict of users and pending messages to be sent

# would communicate with clients after every second
UPDATE_INTERVAL= 1
timeout=False

#create a dictionary of the logins at the credentials.txt

with open("credentials.txt") as f:
    #content = f.readlines()
    for line in f:
        tmp = line.split()
        logins[tmp[0]] = {'pas': tmp[1], 'tries': 0, 'blocked': []} #key = username, value = {password, tries}
f.close()


def authenticate(usr, password):
    return (logins[usr]['pas'] == password)   

#function to check if the usr is inactive
def check_timeout():
    global timeout
    while True:
        #look for clients who still online but timed out
        #for c in clients:
        for c in list(clients):
            if clients[c]['online'] == False:
                continue
            currT = dt.datetime.now()
            lastT = clients[c]['last_active']
            if (currT-lastT).total_seconds() >= timeout:
                clients[c]['online'] = False
                clients[c]['last_active'] = dt.datetime.now()
                serverMessage = "LOG_OUT"
                sock = clients[c]['socket']
                sock.send(serverMessage.encode())
                sock.close()
            
def invalid_command(sock):
    serverMessage = " > Please type a valid command."
    sock.send(serverMessage.encode())


def handle_request(connectionSocket, addr, usr):
    while True:
        try: 
            message = connectionSocket.recv(2058).decode()
        except OSError: #OSerror if the connection was closed
            sys.exit()
        
        #update the last active time
        clients[usr]['last_active'] = dt.datetime.now()

        #parse the message: get the first word
        parsed = message.split(' ', 1)
        
        #Startprivate <user>
        if (parsed[0] == "startprivate"):
            m = message.split()
            #catch invalid command - not enough arguments
            if len(m) != 2:
                invalid_command(connectionSocket)
                
            else:
                other = m[1]
                #other is self
                if usr == other:
                    serverMessage = " > Error. Cannot message self"

                #other doesnt exist
                elif other not in logins:
                    serverMessage = " > Error. Invalid user provided."

                #other not online
                elif other not in clients or clients[other]['online']==False:
                    serverMessage = " > Error. Cannot establish a connection with user."

                # other blocked user - server should NOT provide ip and port + give error
                elif usr in logins[other]['blocked']:
                    serverMessage = " > IP and Port number cannot be obtained."

                # Client should obtain IP and port of <user> from server
                else:
                    ip = clients[other]['addr'][0]
                    port = clients[other]['privPort']

                    print(usr + " is trying to connect to "+ str(port)) #debug
                    #send back the message in format
                    #startPrivateAck <user> <IP> <port>
                    serverMessage = "startPrivateAck " + other + " " + ip + " " + str(port)
                
                connectionSocket.send(serverMessage.encode())

        #message <user> <message>
        elif (parsed[0] == "message"):
            m = message.split(' ', 2)
            if len(m) != 3:
                invalid_command(connectionSocket)
                
            else:
                recipient = m[1]
                mess = " > " + usr + ": "+ m[2]

                print(recipient) #debug
                print(mess) #debug

                #find the user
                if recipient in logins and recipient != usr:
                    #if they're blocked then dont send message
                    if usr in logins[recipient]['blocked']:
                        serverMessage = " > You can no longer send messages to this person."
                        connectionSocket.send(serverMessage.encode())
                    
                    #check if they're online - send message to them
                    elif recipient in clients and clients[recipient]['online'] == True:
                        toSend = clients[recipient]['socket']
                        toSend.send(mess.encode())
                        
                    #otherwise store the message for them
                    else:
                        #if the person already has other pending messages
                        if recipient in pending_msg:
                            pending_msg[recipient].append(mess)
                        #else you're the only pending message
                        else:
                            pending_msg[recipient] = [mess]     
                
                #user doesnt exist or user is self
                else:
                    serverMessage = " > Error. Invalid user"   
                    connectionSocket.send(serverMessage.encode()) 
        
        #whoelse
        elif (message == "whoelse"):  
            serverMessage = ""
            for k in clients:
                if k != usr and clients[k]['online'] == True:
                    serverMessage += ' > '+ k + '\n'

            connectionSocket.send(serverMessage.encode()) 
        
        #broadcast <message>
        elif (parsed[0] == "broadcast"):
            m = message.split(' ', 1)
            if len(m) != 2:
                invalid_command(connectionSocket)
            else:    
                mess = " > " + usr + ": " + m[1]
                
                #go through all online people
                #if they don't block the current user trying to send - send
                flag = False
                for c in clients:
                    if usr == c: #skip self
                        continue
                    
                    list = logins[c]['blocked']
                    if usr in list:
                        flag = True
                    elif clients[c]['online'] == True:
                        toSend = clients[c]['socket']
                        toSend.send(mess.encode())
                    
                #if the flag is true, that means the message was unable to be sent to all
                #server should send message back
                if flag == True:
                    serverMessage = " > Your message could not be delivered to some recipients"
                    connectionSocket.send(serverMessage.encode()) 
        
        #whoelsesince <time>
        elif (parsed[0] == "whoelsesince"):
            m = message.split()
            if len(m) != 2:
                invalid_command(connectionSocket)
            else: 
                sec = int(m[1])
                #find the time that you're looking for
                since_time = dt.datetime.now() - dt.timedelta(seconds=sec)

                #send anyone active since that^ time
                serverMessage = ""
                for p in clients:
                    if p == usr: #skip references of self
                        continue
                    
                    if clients[p]['last_active'] >= since_time or clients[p]['online'] == True:
                        serverMessage += ' > ' + p + '\n'
                        
                connectionSocket.send(serverMessage.encode()) 
                    
        #block <user>
        elif (parsed[0] == "block"):
            m = message.split()
            if len(m) != 2:
                invalid_command(connectionSocket)
            elif m[1] == usr:
                serverMessage = " > Error. Cannot block self"
            elif m[1] not in logins:
                serverMessage = " > Error. Invalid username"
            elif m[1] not in logins[usr]['blocked']:
                logins[usr]['blocked'].append(m[1])
                serverMessage = " > " + m[1] + " is now blocked."
            
            connectionSocket.send(serverMessage.encode()) 

        #unblock <user>
        elif (parsed[0] == "unblock"):
            m = message.split()
            if len(m) != 2:
                invalid_command(connectionSocket)
            elif m[1] == usr:
                serverMessage = " > Error. Cannot unblock self"
            elif m[1] in logins[usr]['blocked']:
                logins[usr]['blocked'].remove(m[1])
                serverMessage = " > " + m[1] + " is unblocked."
            else:
                serverMessage = " > Error. "+ m[1] + " was not blocked."
            
            connectionSocket.send(serverMessage.encode()) 
        
        #logout
        elif (message == "logout"):
            clients[usr]['online'] = False
            m = " > " + usr + " logged out"
            # Blocked users also do not get presence notifications 
            for c in clients:
                if clients[c]['online'] == True and c not in logins[usr]['blocked']:
                    toSend = clients[c]['socket']
                    toSend.send(m.encode())
            
            serverMessage = "LOG_OUT"
            connectionSocket.send(serverMessage.encode())
            connectionSocket.close()
            sys.exit() #exit this thread

        #invalid command
        else:
            invalid_command(connectionSocket)

def ver_new_client(connectionSocket, addr):
    global t_lock
    global clients
    global serverSocket

    while True:
        message = connectionSocket.recv(1024)
        #received data from the client, now we know who we are talking with
        message = json.loads(message.decode())
        usr = message.get("username")
        pas = message.get("password")
        port = message.get("privPort")
        
        #check if already logged in or they are blocked coz > 3 tries
        if usr in clients and clients[usr]['online']:
            serverMessage = "You're already logged in."
            connectionSocket.send(serverMessage.encode())
            #break
            connectionSocket.close()
            sys.exit()
        
        if usr in log_blocked:
            #check if you cant unblock
            currT = dt.datetime.now()
            log = log_blocked[usr]
            if (currT-log).total_seconds() < block_duration:
                serverMessage = "You failed the login too many times, please try again later"
                connectionSocket.send(serverMessage.encode())
                connectionSocket.close()
                sys.exit()

            #unblock the user
            else: 
                del log_blocked[usr] #delete from the block
                logins[usr]['tries'] = 0 #make the value of tries back to 0

        #check if password is in the backend (logins dictionary)
        if logins.get(usr) != None:
            #check if the password is right
            if (authenticate(usr, pas) and logins[usr]['tries'] < 3):
                #correct password
                serverMessage = "Welcome! You can now start messaging!"
                connectionSocket.send(serverMessage.encode())
                
                logins[usr]['tries'] = 0 #reset their no. of tries

                #client dictionary stores:
                    # Boolean - still online
                    # Client socekt and port
                    # Timeactive
                    # Login
                    # privPort they can be contacted on
                time = dt.datetime.now()
                clients[usr] = {'online': True, 'socket': connectionSocket, 'addr': addr, 'last_active': time, 'login': time, 'privPort': port}
                #let the other peers know that this client logged in 
                # Blocked users do not get presence notifications 
                m = usr + " logged in"
                for c in clients:
                    if c == usr:
                        continue
                    if clients[c]['online'] == True and usr not in logins[c]['blocked']:
                        toSend = clients[c]['socket']
                        toSend.send(m.encode())
                
                #now they logged in, send them any pending messages
                if usr in pending_msg:
                    for m in pending_msg[usr]:
                        connectionSocket.send(m.encode())

                handle_request(connectionSocket, addr, usr)

                
            elif logins[usr]['tries'] < 2: #wrong password but havent exhausted tries
                print("wrong")
                serverMessage = "Invalid login. Please try again"
                connectionSocket.send(serverMessage.encode())
                logins[usr]['tries'] += 1
            
            else: #if tries > 3 now block the user
                serverMessage = "You failed the login too many times, please try again later"
                log_blocked[usr] = dt.datetime.now() 
                connectionSocket.send(serverMessage.encode())
                connectionSocket.close()
                sys.exit() #close the thread
            
        
        #username doesnt exist in backend
        else:
            serverMessage = "Invalid username. Please try again"
            connectionSocket.send(serverMessage.encode())
    
#python server.py server_port block_duration timeout

#Server will run on this port
serverPort = int(sys.argv[1])
block_duration = int(sys.argv[2])
timeout = int(sys.argv[3])


serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)
print("starting here")

server_start = dt.datetime.now()
#handle timeout
handle_timeout = threading.Thread(name="Timeout", target=check_timeout)
handle_timeout.daemon=True
handle_timeout.start()
#this is the main thread
while True:
    #check for client
    connectionSocket, addr = serverSocket.accept()
    #handle login for each client
    new_client = threading.Thread(name="NewClient", target=ver_new_client, args=(connectionSocket, addr))
    new_client.daemon=True #daemon thread will shut down immediately when program exits
    new_client.start()

    
    

    #time.sleep(0.1)