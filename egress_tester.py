#!/usr/bin/python

import sys
import threading
import socket
import optparse
import select

VERBOSE = False
MESSAGE = "oQFhS0h1tq7ndveW0lNa"
QUEUE = set()
TIMEOUT = 3
RUNNING = True

def connect_thread(host):
    while True:
        try:
            port = QUEUE.pop()
        except:
            return 0
        s = socket.socket()
        s.settimeout(TIMEOUT)
        print "[*] Trying %s:%s" % (host,port)
        try:
            s.connect((host,port))
            s.send(MESSAGE)
            s.close()
        except Exception, ex:
            if VERBOSE:
                print ex
            pass

def listen_thread(host,port):
    global RUNNING
    try:
        server = socket.socket()
        server.bind((host,port))
        server.listen(1)
        input = [server,sys.stdin]

        while RUNNING:
            inputr,outputr,exceptr = select.select(input,[],[],1)
            for i in inputr:
                if i == server:
                    conn,addr = server.accept()
                    data = conn.recv(1024)
                    if data == MESSAGE:
                        print '[*] Connection on port %d from %s.' % (port,addr[0])
                        running = False
                        conn.close()

                elif i == sys.stdin:
                    command = sys.stdin.readline().strip('\n')
                    if command.lower() in ['quit','q','exit']:
                        RUNNING = False
                    else:
                        print "entering quit, q, or exit will stop the listening threads."
        server.close()
    except Exception, ex:
        print '[!] Error listing on %s:%d %s' % (host,port,str(ex))

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-H','--host',help='target host to connect',action='store')
    parser.add_option('-p','--ports',help='port range to test. example: 1000-1500',action='store')
    parser.add_option('-l','--listen',help='set address to listen',action='store',default=False)
    parser.add_option('-t','--threads',help='set number of threads to test connection',action='store',type=int,default=1)
    parser.add_option('-v','--verbose',help='turn on verbose output',action='store_true',default=False)

    args,_ = parser.parse_args(sys.argv)

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    if args.verbose:
        VERBOSE = True

    lp = 0
    up = 0
    try:
        lp,up = map(lambda x: int(x),args.ports.split('-'))
        for i in xrange(lp,up):
            QUEUE.add(i)

    except Exception,ex:
        print "[!] Error setting queue: %s " % (ex)
        sys.exit(1)

    threads = []
    if args.listen and args.ports:
        if VERBOSE:
            print "[i] Attempting to listen on ports %s. Enter \"q\" or \"quit\" to exit." % (args.ports)
        for port in QUEUE:
            t = threading.Thread(target=listen_thread,args=(args.listen,port))
            t.start()
            threads.append(t)

    elif args.host and args.ports:
        if VERBOSE:
            print "[i] Attempting to connect to host %s on ports %s" % (args.host,args.ports)
        for _ in xrange(4):
            t = threading.Thread(target=connect_thread,args=(args.host,))
            t.start()
            threads.append(t)

    try:
        for t in threads:
            t.join()
    #typing exit is the proper way to ensure all threads are killed, and their ports released
    except KeyboardInterrupt:
        for t in threads:
            t.join()
