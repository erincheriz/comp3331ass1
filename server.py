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



t_lock=threading.Condition()
#will store clients info in this list
clients={} #dict of online users
log_blocked={} #dict of users who are currently blocked because failed to login
logins = {} #dict of all users, passwords, tries and people they block
pending_msg = {} #dict of users and pending messages to be sent
log_book = {} #dict of users and when last logged in

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


#function to continually log out people if they time out/inactive
def check_timeout():
    global timeout
    while True:
        for k in clients.items():
            if dt.datetime.now() - clients[k]['last_active'] >= timeout:
                print("overtime")


def authenticate(usr, password):
    return (logins[usr]['pas'] == password)   

def handle_request(connectionSocket, addr, usr):
    while True:
        message = connectionSocket.recv(2058).decode()

        #parse the message

        #message <user> <message>
        if (message[:7] == "message"):
            m = message.split(' ', 2)
            recipient = m[1]
            mess = usr + ": "+ m[2]

            print(recipient)
            print(mess)

            #find the user if it exists
            #make sure theyre not sending message to themselves
            if recipient in logins and recipient != usr:
                #if they're blocked then dont send message
                if usr in logins[recipient]['blocked']:
                    serverMessage = "You can no longer send messages to this person."
                    connectionSocket.send(serverMessage.encode())
                #check if they're online - send message to them
                elif recipient in clients:
                    #send message
                    toSend = clients[recipient]['socket']
                    toSend.send(mess.encode())
                    print("sent to peer")
                #otherwise store the message for them
                else:
                    print("saving for peer")
                    pending_msg[recipient] = [mess]
            
            #user doesnt exist or user is self
            else:
                serverMessage = "Error. Invalid user"   
                connectionSocket.send(serverMessage.encode()) 
            

        #whoelse
        elif (message == "whoelse"):  
            serverMessage = ""
            for k in clients:
                if k != usr:
                    serverMessage = k
                    connectionSocket.send(serverMessage.encode()) 
        
        #broadcast <message>
        elif (message[:9] == "broadcast"):
            m = message.split(' ', 1)
            mess = usr + ": " + m[1]
            
            #go through all online people
            #if they don't block the current user trying to send - send
            flag = False
            for c in clients:
                list = logins[c]['blocked']
                if usr == c:
                    continue
                if usr not in list:
                    toSend = clients[c]['socket']
                    toSend.send(mess.encode())
                else:
                    flag = True
            
            #if the flag is true, that means the message was unable to be sent to all
            #server should send message back
            if flag == True:
                serverMessage = "Your message could not be delivered to some recipients"
                connectionSocket.send(serverMessage.encode()) 
        

        #whoelsesince <time>
        if (message[:12] == "whoelsesince"):
            m = message.split()
            

        #block <user>
        elif (message[:5] == "block"):
            m = message.split()
            if m[1] == usr:
                serverMessage = "Error. Cannot block self"
            elif m[1] not in logins:
                serverMessage = "Error. Invalid username"
            elif m[1] not in logins[usr]['blocked']:
                logins[usr]['blocked'].append(m[1])
                serverMessage = m[1]+" is now blocked."
            
            connectionSocket.send(serverMessage.encode()) 

        #unblock <user>
        elif (message[:7] == "unblock"):
            m = message.split()
            if m[1] == usr:
                serverMessage = "Error. Cannot unblock self"
            try:
                logins[usr]['blocked'].remove(m[1])
                serverMessage = m[1] + " is unblocked."
            except ValueError:
                serverMessage = "Error. "+ m[1] + " was not blocked."
            finally:
                connectionSocket.send(serverMessage.encode()) 
        
        #logout
        elif (message == "logout"):
            del clients[usr]
            m = usr + " logged out"
            for c in clients:
                toSend = clients[c]['socket']
                toSend.send(m.encode())
            serverMessage = "LOG_OUT"
            connectionSocket.send(serverMessage.encode())
            #just close the socket here? - close the client??
            #close the thread???
            connectionSocket.close()


        #invalid command
        else:
            serverMessage = "Please type a valid command."
            connectionSocket.send(serverMessage.encode()) 
            
            


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
        
        #check if already logged in or they are blocked coz > 3 tries
        if usr in clients:
            serverMessage = "You're already logged in."
            connectionSocket.send(serverMessage.encode())
            break
            #connectionSocket.close()
            #close thread???
        if usr in log_blocked:
            #check if you cant unblock
            if (dt.datetime.now().time()-log_blocked[usr] < block_duration):
                serverMessage = serverMessage = "You failed the login too many times, please try again later"
                connectionSocket.send(serverMessage.encode())

            #unblock the user
            else: 
                del log_blocked[usr] #delete from the block
                logins[usr]['tries'] = 0 #make the value of tries back to 0

        #check if password is in the backend (logins dictionary)
        if logins.get(usr) != None:
            #check if the password is right
            if (authenticate(usr, pas) and logins[usr]['tries'] < 3):
                #correct password
                print("right")
                serverMessage = "Welcome! You can now start messaging!"
                connectionSocket.send(serverMessage.encode())
                
                logins[usr]['tries'] = 0

                #client dictionary stores:
                    # List of people theyve blocked - list
                    # Client socekt
                    # Timeactive
                time = dt.datetime.now()
                clients[usr] = {'socket': connectionSocket, 'last_active': time}

                #add the user to the log_book which stores when people log in
                log_book[usr] = time

                #let the other peers know that this client logged in 
                m = usr + " logged in"
                for c in clients:
                    if c != usr:
                        toSend = clients[c]['socket']
                        toSend.send(m.encode())
                        print("sent message to " + c)
                    
                #start new threads to send/receive????
                # recv_thread=threading.Thread(name="RecvHandler", target=recv_handler, args=(connectionSocket, addr, usr))
                # recv_thread.daemon=True 
                # recv_thread.start()

                # send_thread=threading.Thread(name="SendHandler",target=send_handler, args=(connectionSocket, addr, usr))
                # send_thread.daemon=True
                # send_thread.start()

                #now they logged in, send them any pending messages
                if usr in pending_msg:
                    for m in pending_msg[usr]:
                        connectionSocket.send(m.encode())

                handle_request(connectionSocket, addr, usr)

                
            elif logins[usr]['tries'] < 2: #wrong password but havent exhausted tries
                print("wrong")
                serverMessage = "Invalid login. Please try again"
                logins[usr]['tries'] += 1
            
            else: #if tries > 3 now block the user
                serverMessage = "You failed the login too many times, please try again later"
                log_blocked[usr] = dt.datetime.now().time() #add user to blocked along w the time theyre blocked
                connectionSocket.send(serverMessage.encode())
                #close the thread
            
            connectionSocket.send(serverMessage.encode())
        
        #username doesnt exist in backend
        else:
            serverMessage = "Invalid username. Please try again"
            connectionSocket.send(serverMessage.encode())
    




def recv_handler(connectionSocket, addr, usr):
    global t_lock
    global clients
    
    global serverSocket
    print('Server is ready for service')
    while(1):
        
        message = connectionSocket.recv(2048)
        message = message.decode()

        

        #get lock as we might me accessing some shared data structures
        with t_lock:
            #currtime = dt.datetime.now()
            #date_time = currtime.strftime("%d/%m/%Y, %H:%M:%S")
            print("receiving from "+usr)

            print("message is " + message)



            # if(message == 'Subscribe'):
            #     #store client information (IP and Port No) in list
            #     clients.append(clientAddress)
            #     serverMessage="Subscription successfull"
            # elif(message=='Unsubscribe'):
            #     #check if client already subscribed or not
            #     if(clientAddress in clients):
            #         clients.remove(clientAddress)
            #         serverMessage="Subscription removed"
            #     else:
            #         serverMessage="You are not currently subscribed"
            # else:
            serverMessage="Unknown command, send Subscribe or Unsubscribe only"
            #send message to the client
            connectionSocket.send(serverMessage.encode())
            #notify the thread waiting
            t_lock.notify()


def send_handler(connectionSocket, addr, usr):
    global t_lock
    global clients
    
    global serverSocket
    global timeout
    #go through the list of the subscribed clients and send them the current time after every 1 second
    while(1):
        #get lock
        with t_lock:
            for i in clients:
                #currtime =dt.datetime.now()
                #date_time = currtime.strftime("%d/%m/%Y, %H:%M:%S")
                date_time = "blah"
                message='Current time is ' + date_time
                connectionSocket.send(message.encode())
                print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
            #notify other thread
            t_lock.notify()
        #sleep for UPDATE_INTERVAL
        time.sleep(UPDATE_INTERVAL)



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

#this is the main thread
while True:
    
    #check for client
    connectionSocket, addr = serverSocket.accept()

    #handle login for each client
    new_client = threading.Thread(name="NewClient", target=ver_new_client, args=(connectionSocket, addr))
    new_client.daemon=True #daemon thread will shut down immediately when program exits
    new_client.start()

    
    #handle timeout
    #check_timeout = thread.Thread(name="Timeout")

    #time.sleep(0.1)