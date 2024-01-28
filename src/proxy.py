"""
********************************************************************************
;
;   MODULE       proxy.py       
;
;   DESCRIPTION  Source file for the iscsi test tool proxy class
;
;   This file is part of iSCSISim.
;
;   Copyright (c) 2009, ATTO Technology, inc.
;   All rights reserved.
;
; Redistribution and use in source and binary forms, with or without 
; modification, are permitted provided that the following conditions are met:
;
;   Redistributions of source code must retain the above copyright notice, 
;       this list of conditions and the following disclaimer. 
;   Redistributions in binary form must reproduce the above copyright notice, 
;       this list of conditions and the following disclaimer in the 
;       documentation and/or other materials provided with the distribution. 
;   Neither the name of ATTO Technology nor the names of its contributors may
;       be used to endorse or promote products derived from this software 
;       without specific prior written permission, with the sole exception of 
;       the "Powered by ATTO" logo contained as part of this software package.
;
; THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
; AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
; IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
; ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
; LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
; CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
; SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
; INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
; CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
; ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
; POSSIBILITY OF SUCH DAMAGE.
;    
********************************************************************************
"""
#!/usr/bin/env python

# Imports
import getopt
import re
import select
import socket
import struct
import sys
import threading
import time

# Module scope variables
CONTROL_PORT = 3000

# Opcode maps
initiator_opcodes = {
    0x00 : "NOP Out",
    0x01 : "SCSI Command",
    0x02 : "Task Mgt. Request",
    0x03 : "Login Request",
    0x04 : "Text Request",
    0x05 : "Data Out",
    0x06 : "Logout Request",
    0x10 : "SNACK Request"
}
target_opcodes = {
    0x20 : "NOP In",
    0x21 : "SCSI Response",
    0x22 : "Task Mgt. Response",
    0x23 : "Login Response",
    0x24 : "Text Response",
    0x25 : "Data In",
    0x26 : "Logout Response",
    0x31 : "R2T",
    0x32 : "Async",
    0x3f : "Reject"
}

# Print debug output with a timestamp
def debug(s):
    print("%s: %s" % (time.strftime("%H:%M:%S"), s))

# Hex dump
def hexdump(buf):
    printable = \
        "................................"  \
        " !\"#$%&'()*+,-./0123456789:;<=>?" \
        "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_" \
        "`abcdefghijklmnopqrstuvwxyz{|}~."  \
        "................................"  \
        "................................"  \
        "................................"  \
        "................................"
    while buf:
        line = buf[:16]
        h = ("%02x " * len(line)) % tuple([ord(i) for i in line])
        a = "".join([printable[ord(i)] for i in line])
        print(h.ljust(48) + a)
        buf = buf[16:]

# Do nothing exception class
class ConnException(Exception):
    pass

# This class encapsulates a thread that handles data connections to the proxy
class ProxyThread(threading.Thread):
    def __init__(self, socket, address, server):
        # Create a thread and save parameters associated with this instance
        threading.Thread.__init__(self)
        self.itrsock = socket
        self.itraddr = address
        self.server = server
        self.tgtsock = None
        self.pause = False
        server.addconn(address[1], self)

    def reset(self):
        # Connection reset now!
        try:
            self.itrsock.setsockopt(socket.SOL_SOCKET,
                                    socket.SO_LINGER,
                                    struct.pack("2H", 1, 0))
            self.itrsock.close()
            self.tgtsock.setsockopt(socket.SOL_SOCKET,
                                    socket.SO_LINGER,
                                    struct.pack("2H", 1, 0))
            self.tgtsock.close()
        except:
            pass

    def run(self):
        # This is the thread's main function
        logf = None
        try:
            # See if saving traffic to a file is desired
            if self.server.logfile != None:
                self.server.lock.acquire()
                logf = file(self.server.logfile + str(self.server.cid), "wb")
                self.server.cid += 1
                self.server.lock.release()

            # Connect to iSCSI target
            debug("Proxy connection from " + repr(self.itraddr))
            self.tgtsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tgtsock.connect(self.server.target)

            # Main loop
            sellist = [self.itrsock.fileno(), self.tgtsock.fileno()]
            while True:
                # Wait for stuff to happen
                (rd, wr, ex) = select.select(sellist, [], sellist)
                if ex:
                    debug("Socket exception!")
                    raise ConnException

                # Handle all sockets requiring attention
                for i in rd:
                    pdu = ""
                    if i == self.tgtsock.fileno():
                        # Target sent a PDU, so receive it
                        while len(pdu) < 0x30:  # Get BHS
                            buf = self.tgtsock.recv(0x30 - len(pdu))
                            if not buf:
                                raise ConnException
                            pdu += buf
                        actual = 0x30       \
                            + ord(pdu[4])   \
                            + struct.unpack(">L", "\x00" + pdu[5:8])[0]
                        length = (actual + 3) & ~3  # Pad to 32-bit word
                        while len(pdu) < length:    # Get rest of PDU
                            buf = self.tgtsock.recv(length - len(pdu))
                            if not buf:
                                raise ConnException
                            pdu += buf

                        # Translate addresses in text responses
                        if (ord(pdu[0]) & 0x3f) == 0x24:
                            pdu = re.sub(
                                r"TargetAddress=[^,\x00]+",
                                r"TargetAddress=%s:%u"
                                    % self.itrsock.getsockname(),
                                pdu[:actual])
                            actual = len(pdu)
                            hdr = 0x30 + ord(pdu[4])
                            pdu = pdu[:5] \
                                + struct.pack(">L", actual - hdr)[1:] \
                                + pdu[8:]
                            length = (actual + 3) & ~3
                            pdu = pdu.ljust(length, "\x00") # Pad to 32-bit word

                        # Write BHS of PDU to file, if it exists
                        if logf:
                            logf.write(pdu[:0x30])

                        # Validate PDU based on opcode in BHS
                        if (ord(pdu[0]) & 0x3f) not in list(target_opcodes.keys()):
                            debug("Invalid opcode in BHS from target!")
                            hexdump(pdu[:0x30])

                        # Send PDU to initiator
                        if not self.pause:
                            if self.itrsock.send(pdu) != len(pdu):
                                raise ConnException
                    else:
                        # Initiator sent a PDU, so receive it
                        while len(pdu) < 0x30:  # Get BHS
                            buf = self.itrsock.recv(0x30 - len(pdu))
                            if not buf:
                                raise ConnException
                            pdu += buf
                        actual = 0x30       \
                            + ord(pdu[4])   \
                            + struct.unpack(">L", "\x00" + pdu[5:8])[0]
                        length = (actual + 3) & ~3  # Pad to 32-bit word
                        while len(pdu) < length:    # Get rest of PDU
                            buf = self.itrsock.recv(length - len(pdu))
                            if not buf:
                                raise ConnException
                            pdu += buf

                        # Write BHS of PDU to file, if it exists
                        if logf:
                            logf.write(pdu[:0x30])

                        # Validate PDU based on opcode in BHS
                        if (ord(pdu[0]) & 0x3f) not in list(initiator_opcodes.keys()):
                            debug("Invalid opcode in BHS from initiator!")
                            hexdump(pdu[:0x30])

                        # Send PDU to target
                        if not self.pause:
                            if self.tgtsock.send(pdu) != len(pdu):
                                raise ConnException
        except socket.error:
            # Handle socket errors
            raise
        except ConnException:
            # Handle socket close events
            pass
        finally:
            # Connection closed by one side or the other
            debug("Proxy connection from " + repr(self.itraddr) + " closed\n")
            self.server.removeconn(self.itraddr[1], self)
            self.itrsock.close()
            if logf:
                logf.close()
            if self.tgtsock:
                self.tgtsock.close()

# This class encapsulates a thread that handles control connections to the proxy
class ControlThread(threading.Thread):
    def __init__(self, socket, address, server):
        # Create a thread and save parameters associated with this instance
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.server = server

    def pause(self, port, status):
        if port != None:
            # Pause or continue one connection
            item = self.server.findconn(port)
            if item:
                item.pause = status
            else:
                s = "pause/continue: Invalid port: %u" % port
                self.socket.send("error: %s\x00" % s)
                debug(s)
                return
        else:
            # Pause or continue all connections
            for item in self.server.listconn():
                item.pause = status

        # Reply to control client
        self.socket.send("ok\x00")

    def run(self):
        # This is the thread's main function
        debug("Control connection from " + repr(self.address))

        # Setup command parser
        cmdpat = re.compile(r"([a-zA-Z]+)( \d*)?")
        buf = ""

        try:
            # Wait for a packet
            r = self.socket.recv(4096)
            while r:
                # Parse packet
                buf += r
                li = buf.split("\x00")
                if len(li) > 1:
                    for i in li[:-1]:
                        m = cmdpat.match(i)
                        try:
                            if m:
                                cmd = m.group(1)
                                if cmd == "pause":
                                    port = int(m.group(2))
                                    self.pause(port, True)
                                elif cmd == "continue":
                                    port = int(m.group(2))
                                    self.pause(port, False)
                                elif cmd == "pauseall":
                                    if m.group(2):
                                        raise ValueError
                                    self.pause(None, True)
                                elif cmd == "continueall":
                                    if m.group(2):
                                        raise ValueError
                                    self.pause(None, False)
                                elif cmd == "reset":
                                    port = int(m.group(2))
                                    item = self.server.findconn(port)
                                    if item:
                                        item.reset()
                                    else:
                                        s = "reset: Invalid port: %u" % port
                                        self.socket.send("error: %s\x00" % s)
                                        debug(s)
                                else:
                                    # Unknown command
                                    raise ValueError
                            else:
                                # No match
                                raise ValueError
                        except ValueError:
                            s = "Unknown command: %s" % repr(i)
                            self.socket.send("error: %s\x00" % s)
                            debug(s)
                    buf = li[-1]

                # Wait for a packet
                r = self.socket.recv(4096)
        except socket.error:
            # Handle socket errors
            raise
        finally:
            # Connection closed by one side or the other
            debug("Control connection from " + repr(self.address) + " closed\n")
            self.socket.close()

# This class encapsulates the proxy server thread which accepts
# TCP connections and creates threads to handle them
class ProxyServer:
    def __init__(self, target, logfile = None):
        # Set up server instance variables
        self.lock = threading.Lock()
        self.cid = 0
        self.target = (target, 3260)
        self.logfile = logfile
        self.conns = {}

    def serve(self):
        # Start the server
        serversocket = [None, None]
        serversocket[0] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket[0].bind(("", 3260))
        serversocket[0].listen(5)
        serversocket[1] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket[1].bind(("", CONTROL_PORT))
        serversocket[1].listen(1)
        while True:
            # Wait for a connection
            (rd, wr, ex) = select.select(
                [serversocket[0].fileno(), serversocket[1].fileno()], [], [])
            for i in rd:
                if i == serversocket[0].fileno():
                    # Accept proxy connection and start a thread to handle it
                    (clientsocket, address) = serversocket[0].accept()
                    pt = ProxyThread(clientsocket, address, self)
                    pt.start()
                else:
                    # Accept control connection and start a thread to handle it
                    (clientsocket, address) = serversocket[1].accept()
                    ct = ControlThread(clientsocket, address, self)
                    ct.start()

    def addconn(self, port, item):
        # Add connection to the control dictionary
        self.lock.acquire()
        try:
            assert port not in self.conns
            self.conns[port] = item
        finally:
            self.lock.release()

    def removeconn(self, port, item):
        # Remove connection from the control dictionary
        self.lock.acquire()
        try:
            del self.conns[port]
            return True
        except KeyError:
            return False
        finally:
            self.lock.release()

    def findconn(self, port):
        # Find connection in the control dictionary
        self.lock.acquire()
        try:
            return self.conns[port]
        except KeyError:
            return None
        finally:
            self.lock.release()

    def listconn(self):
        # List connections in the control dictionary
        self.lock.acquire()
        try:
            return list(self.conns.values())
        finally:
            self.lock.release()

def usage(prog):
    sys.stderr.write(
        "Usage:\n"
        "%s <-t TargetIP> [-L LogFile]\n"
        "%s <--target=TargetIP> [--log=LogFile]\n"
        % (prog, prog))
    sys.exit(2)

def main(argv):
    # Prepare to parse command line arguments
    target, logfile = (None, None)
    goodip = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
         "(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    valid = False

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(
            argv[1:], "t:L:", ("target=", "log="))
    except getopt.GetoptError:
        usage(argv[0])
    for opt, arg in opts:
        if opt in ("-t", "--target"):
            if goodip.match(arg):
                target = arg
                valid = True
            else:
                valid = False
        elif opt in ("-L", "--log"):
            logfile = arg
        else:
            raise ValueError(opt)

    # Validate command line arguments
    valid = valid and not args
    if not valid:
        usage(argv[0])

    # Run proxy server
    proxy = ProxyServer(target, logfile)
    proxy.serve()

# Boilerplate
if __name__ == "__main__":
    main(sys.argv)
