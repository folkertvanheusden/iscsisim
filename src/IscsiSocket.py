"""
********************************************************************************
;
;   MODULE       IscsiSocket.py       
;
;   DESCRIPTION  Interface class for output from iSCSI tester.
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
;   The iSCSI output class needs to:
;     * Send output to the DUT however that's supposed to be done
;           - Output happens in two stages:  First the pdus are 'cooked',
;             that is, they are prepared for output.  Second the PDU's are 
;             transferred to the DUT. 
;           - For the socket-based link, that means that all PDU's are stored
;             until the call to ForwardPDUs()
;           - For the serial-based link, that means that cooked PDU's are sent
;             to the DUT uppon the call to CookPDU() and the Test Message is 
;             sent upon the call to Forward PDUs.
;     * Read in all expected test results in PDU-sized chunks.
;           - This doesn't have to be multi-threaded, since unsolicited PDU-in's
;             are not supported by the test tool.
;           - There may be more that one PDU recieved for a particular test. The
;             PDU's need to be chunked up by the particular interface in 
;             question.
;     * Place a copy of all PDU's sent or received in the log file.
;
;   COPYRIGHT (c) ATTO TECHNOLOGY, INC. 2008
;   ALL RIGHTS RESERVED.
;
********************************************************************************
"""

# import section
 # 2.5 only
import IscsiPDU as PDU
import sys
import time
import IscsiComms as ISOT
import io
from socket import *
from copy import copy
from array import array


# Global Constants

class IscsiSocket(ISOT.IscsiComms):

   READ_SOCKET_TIMEOUT = 0.5     # in seconds
   RX_CHUNKSIZE = 9600 # read 9600 bytes at once
   WRITE_MAXLEN = 1024 #max bytes to write to logfile of any one PDU being sent
   READ_MAXLINES = 128 # max lines to write to logfile of any one PDU received
   PROXY_CTRL_PORT = 3000 # Port used for proxy control messages
   PAUSE_PROXY_CMD = "pause "
   CONTINUE_PROXY_CMD = "continue "
   PAUSEALL_PROXY_CMD = "pauseall"
   CONTINUEALL_PROXY_CMD = "continueall"
   RESET_PROXY_CMD = "reset "
   PROXY_READBUF_SIZE = 64
                                       
   def __init__(self,logfile,ipaddr,tcpport,proxyconn):
      
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.__init__
      ;
      ;   RESPONSIBILITY  IscsiSocket class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance to
      ;                                  initialize
      ;                logfile       I   The iSCSI log file
      ;                ipaddr        I   The ip address for the socket
      ;                tcpport       I   The tcp port to open
      ;                proxyconn     I   True if this is a proxied socket
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # init base class stuff
      ISOT.IscsiComms.__init__(self,logfile)
      
      # set up local variables.  This actually won't be 
      self.ipAddr = ipaddr
      self.tcpPort = tcpport
      self.socket = socket(AF_INET,SOCK_STREAM)
      self.logBuf = ''
      self.logAsciiText = ''
      self.logLineCount = 0
      self.logNumLinesThisPDU = 0
      # create the list of PDUs
      self.txPduList = []
      self.threadPaused = False
      self.pauseTheThread = False

      # specify what type of connection we have
      self.commWithProxy = proxyconn
      self.proxyCtrlSocket = socket(AF_INET,SOCK_STREAM)
            
   def __del__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.__del__
      ;
      ;   RESPONSIBILITY  IscsiSocket class destructor
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      try:
          self.socket.close()
          if self.commWithProxy:
             self.proxyCtrlSocket.close()
      except:
          print("Error on socket Close")
          
   def CookPDU(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.CookPDU
      ;
      ;   RESPONSIBILITY  Serializes pdu's, writes them out to the logfile, 
      ;        adds them to the internal pdu list.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;                pdu           I    The PDU to send 
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # achar is the character representation for the log file
      cstr = ""
            
      # serialize the PDU to prepare for logging & update of send vars
      serialPdu = pdu.Serialize(self.testcase)
      pdulen = bytesLeft = len(serialPdu)
                  
      # now that I have a serialized PDU, update all the
      # applicable test variables.
      self.testcase.UpdateSendVars(serialPdu)
      # we may need to turn digests on for the return trip
      if pdu.headerDigest != "0":
         self.testcase.headerDigest = True
      else:
         self.testcase.headerDigest = False
         
      if pdu.dataDigest != "0":
         self.testcase.dataDigest = True
      else:
         self.testcase.dataDigest = False
                  
      # put a copy of the serial pdu to the pdulist
      self.txPduList.append(copy(serialPdu))
      
      # write out the PDU to the log file as long as amt written so far is under 1K
      writeCntr = 0
      while writeCntr < self.WRITE_MAXLEN and bytesLeft:
          
         bytesThisLine = min(bytesLeft, self.LINE_SIZE)          
         
         #break up into lines  
         for i in range(bytesThisLine):  
             bytetowrite = serialPdu.pop(0)
            
             if writeCntr < self.WRITE_MAXLEN:           
                self.logFile.write("%02x " % bytetowrite)
                if chr(bytetowrite) in "\r\n\t\0":
                    cstr = cstr + ' '
                else:
                    cstr = cstr + chr(bytetowrite)
           
         if writeCntr < self.WRITE_MAXLEN:   
             # pad to end of line
             self.logFile.write("%*s" % ((self.LINE_SIZE - bytesThisLine)*3,""))    
                   
             # end of line, write the string value plus eol
             self.logFile.write("%s%s\n" % (self.LOGFILE_ASCII_SPACER,cstr))
             cstr = ""
             writeCntr += bytesThisLine
         bytesLeft -= bytesThisLine
        

   def Open(self,testcase):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.Open
      ;
      ;   RESPONSIBILITY  Opens up the TCP link to the configured ip address
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;                testcase      I/O  The testcase to use for this run
      ;                                   if None, commits an open without 
      ;                                    updating the local testcase
      ;
      ;   RETURNS     PASS or FAIL, depending on needs of link
      ;
      ************************************************************************
      """    
           
      print("Socket: connecting to %s on port %d" %(self.ipAddr,self.tcpPort))
      if testcase != None:
          self.testcase = testcase
          
      self.logFile.write("Socket: connecting to %s on port %d :" %
                         (self.ipAddr,self.tcpPort))
      
      # try to socket connect twice.  If it doesn't work the first time,
      # clean up as best you can and try again.
      try:
          self.socket.connect((self.ipAddr,self.tcpPort))
          self.logFile.write(" passed\n")
      except:
          print("Socket Connection failed.")
          print(sys.exc_info())
          self.logFile.write(" failed\n")
          return(ISOT.OUT_START_FAIL) 
      
      # if we are using a proxy connection, open up the proxy ctrl socket
      if self.commWithProxy:
          try:
              self.proxyCtrlSocket.connect((self.ipAddr,self.PROXY_CTRL_PORT))
              self.logFile.write("Connected proxy control socket")
          except:
              print("Proxy socket connection failed.")
              print(sys.exc_info())
              self.logFile.write("Proxy control socket could not connect")
              return(ISOT.OUT_START_FAIL)

      # clear the self.termination flag.
      self.TerminateAtNextOpportunity = False
      return(ISOT.OUT_START_PASS)
  
  
   def RestartComms(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.RestartComms
      ;
      ;   RESPONSIBILITY  Closes the tcp link and reopens it
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     nothing
      ;
      ************************************************************************
      """    
      #shut down the receive thread.  The socket will close when it's done.      
      if not self.threadPaused:
         #shrink the rx timeout to 100 ms
         self.socket.settimeout(0.1)
         self.pauseTheThread = True
      
      #wait for the pause
      while not self.threadPaused:
          time.sleep(0.2)   
         
      # close the socket
      self.socket.close()
      if self.commWithProxy:
         self.proxyCtrlSocket.close()
      
      # reopen the socket
      self.socket = socket(AF_INET,SOCK_STREAM)
      self.Open(None)
      
      # release the run thread 
      self.pauseTheThread = False
      self.threadPaused = False
            
         
   def ForwardPDUs(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.ForwardPDUs
      ;
      ;   RESPONSIBILITY  Sends the stored-up PDUs out on the link
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """    
      numPdusSent=0
           
      self.logFile.write("Socket : sending PDUs \n")
      
      for serializedPdu in self.txPduList:
          arrayPdu = array('B',serializedPdu)
          totalSent = 0
          # We have to track how much data is sent and continuously
          # call socket.send() until all data has been sent.
          while totalSent < len(serializedPdu):
             try:
                sent = self.socket.send(arrayPdu[totalSent:])
             except:
                raise RuntimeError("Socket timeout on send")            
             
             if sent == 0:
                raise RuntimeError("Socket connection broken")
            
             totalSent = totalSent + sent

          numPdusSent += 1
        
      # clear out the pdu list
      self.txPduList = []
           
      print("Sent %d PDUs" % numPdusSent)

            
   def ReadInPdus(self,wait):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.ReadInPdus
      ;
      ;   RESPONSIBILITY  After waiting the specified time, pulls all received 
      ;        pdus from the rxpdulist, empties the list, and returns the new
      ;        list of pdus.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS    The list of PDUs returned.
      ;
      ;   In order to read multiple PDU's, reads until socket timeout 
      ;    expires.
      ;
      ************************************************************************
      """ 
      iter = 0
      
      # give the tgt 100 ms to get caught up (No worries: we'll wait later 
      # if need be.)
      time.sleep(0.1)
      
      while iter < 5:

          with self.rxPduLock:
              # return everything on the rx pdu list
              pdulist = self.rxPduList[:]
              # remove everything on the rx pdu list
              self.rxPduList = []
          if len(pdulist) > 0:
            break
          else:
            iter = iter + 1
         
          #wait for the read thread to get the pdus in
          time.sleep(wait)
                  
      print("read %d pdus" % len(pdulist))
      return pdulist

   def SendRestart(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.SendRestart
      ;
      ;   RESPONSIBILITY  Asks DUT to restart itself
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      print("Send Restart is not implemented on sockets (yet?)")
      print("Closing Socket")
      self.socket.close()
      if self.commWithProxy:
         self.proxyCtrlSocket.close()

   def run(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.run
      ;
      ;   RESPONSIBILITY  Thread that reads data from the host, writes all bytes 
      ;    recieved to the logfile, then places the recieved data into the 
      ;    given list.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS    never.
      ;
      ************************************************************************
      """ 
      # set up the socket timeout - if a PDU starts but is not rx'd by 
      # timeout, an error is logged.
      self.socket.settimeout(self.READ_SOCKET_TIMEOUT)
      
      # set our internal state to running
      self.threadPaused = False
      
      while 1:
          
         # make sure terminate flag has not been set
         if self.terminateAtNextOpportunity:
             break
        
         #if a pause is requested do that
         while self.pauseTheThread:
             if self.TerminateAtNextOpportunity:
                 break
             self.threadPaused = True
             time.sleep(0.200)

          
         # logbuf holds the data to be written to the log.  Fill in its header
         # and get it ready for a new PDU.
         self.logBuf = self.LOGFILE_RXPDU_HDR
         self.logLineCount = 0;
         self.logAsciiText = ''
         self.dataString = ''
         dataBuffer = ''
          
         # read a single PDU
         byteList = [] 
         # writeCntr keeps track of how many bytes of data have been written for a
         # given PDU
         writeCntr = 0 
      
         # read the bhs.  That's 48 bytes, 52 if header digest is on
         readSize = self.ISCSI_BHS_SIZE
    
         try:
             bhsbuffer=self.socket.recv(readSize)
         except timeout:
             continue;
      
         # see if small bhs (discard) was rx'd.
         if len(bhsbuffer) != readSize:
             continue;
         
         # see if we need to read in a header digest
         if self.testcase.headerDigest:
             try:
                 digest = self.socket.recv(4)
             except timeout:
                 self.logFile.write("ERROR:TIMEOUT IN RXing Header digest!\r\n")
                 # timeout.  Make a fake digest so that lengths all work out.
                 digest = "aaaa"
             # put the digest into bhsbuffer
             bhsbuffer += digest
         
         # place the BHS into dataString
         self.dataString = bhsbuffer
         # write the data out to the logfile
         self.AddDataToLogfileBuf(bhsbuffer)
         self.FinishLogfileBufPdu()
                 
         # figure out the data length of this PDU
         """ ******** WARNING - AHS IS NOT SUPPORTED ***************** """
         readSize = (bhsbuffer[5]<<16) + \
                    (bhsbuffer[6]<<8) + \
                    (bhsbuffer[7])   
                    
         if readSize:
            # read in the data
            if self.testcase.dataDigest:
                readSize += 4
            # account for pad
            # read in (and discard) pad
            if readSize % 4 != 0:
                padLen = 4 - readSize % 4
                readSize += padLen
            
            
            # readCount is a temp variable to allow bite-sized read from 
            # the network.
            readCount = readSize
            # now read all of readSize bytes, but only in RX_chunksize pieces
            while (readCount):
                try:
                   chunkBuffer =                                               \
                              self.socket.recv(min(self.RX_CHUNKSIZE,readCount))
                except timeout:
                    # timeout, break out of loop
                    self.logFile.write("READ TIMEOUT AFTER %d BYTES \r\n" %    
                                       readCount)
                    break;
                    
                readCount -= len(chunkBuffer)
                print(chunkBuffer)
                print(chunkBuffer.decode('ascii'))
                print()
                dataBuffer += chunkBuffer.decode('ascii')
                if self.terminateAtNextOpportunity:
                    break
            if self.TerminateAtNextOpportunity:
                break
                
            self.logBuf = self.logBuf + self.LOGFILE_RXDATA_HDR
            
            self.AddDataToLogfileBuf(dataBuffer)
                
            # put databuffer into the String     
            self.dataString += dataBuffer.encode('ascii')
            
         # write the last line of the log
         self.FinishLogfileBufPdu()
        
         # check length of data
         if len(dataBuffer) != readSize:
            self.logFile.write("%s"%self.logBuf)
            self.logFile.write("\n ERROR - BAD DATA LEN Expected %d got %d\r\n" %
                                (readSize,len(dataBuffer)))
            self.logFile.write("(This may be due to a digest problem.)\r\n")
         else: 
            # for each pdu read in , place it on the PDU list to return. 
            pduTmp = PDU.IscsiPdu()
            pduTmp.DeSerialize(self.dataString,self.testcase)
            with self.rxPduLock:
               self.rxPduList.append(pduTmp)
            # dump the log output to the buffer

            self.logFile.write("%s"%self.logBuf)

         # Sleep for a smidge to prevent starvation
         time.sleep(0)
         
      # terminating, close the socket
      self.socket.close()
      if self.commWithProxy:
         self.proxyCtrlSocket.close()

      # no longer in running state
      self.running = False
            
   def AddDataToLogfileBuf(self,buf):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.AddDataToLogfileBuf
      ;
      ;   RESPONSIBILITY  Put the data in buf in bytewise formatted hex into 
      ;      the logfile buffer in the socket class.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self         I/O  The IscsiSocket class instance 
      ;                buf           I   The buffer containing bytes to add  
      ;
      ;   RETURNS    happily.
      ;
      ************************************************************************
      """ 
      
      # if max lines exceeded, just return
      if self.logNumLinesThisPDU > self.READ_MAXLINES:
          return

      if type(buf) == type(""):  # hack by FvH
          buf = buf.encode('ascii')
      
      #  So we start with whatever's currently in logBuf (I hope its the 
      #  header) and whatever line is currently in logAsciiText.  Append
      #  to these things and when we've reached the end of a line, restart
      #  the counters.  (Boy, that's clear.  I should become a professional
      #  tech writer.)
      
      # Use cstring io to try to speed this up.  We're making the output string
      # from the buf passed in.
      cst = io.StringIO()
      for c in buf:
         # drop the hex encoded byte into the current logbuf
         cst.write(" %02x" % c)
         # now add the character to the ascii encoded string
         # translate tab cr or lf to space.
         if chr(c) in "\r\t\n\0":
            self.logAsciiText += ' '
         else:    
            self.logAsciiText += chr(c)
         self.logLineCount += 1

         if self.logLineCount == self.LINE_SIZE:
            # end of line, write out the spacer and the ascii version
            self.logLineCount = 0
            cst.write( "%s%s\n" %                                          \
                               (self.LOGFILE_ASCII_SPACER,self.logAsciiText))
            self.logAsciiText = ''
            self.logNumLinesThisPDU += 1
            # if exceeded limit, break out of for loop.
            if self.logNumLinesThisPDU > self.READ_MAXLINES:
                break
                
      self.logBuf += cst.getvalue()

   def FinishLogfileBufPdu(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.AddDataToLogfileBuf
      ;
      ;   RESPONSIBILITY  Writes the last line of a PDU output into the
      ;        logfile buf.  Essentially, write a bunch of spaces and then
      ;        the asii version of the line
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self         I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS    nothing.
      ;
      ************************************************************************
      """ 
      if self.logLineCount < self.LINE_SIZE:
          self.logBuf += "%*s%s\n" %                                           \
              ((self.LINE_SIZE - self.logLineCount +1 )*3,
                self.LOGFILE_ASCII_SPACER,
                self.logAsciiText)

      self.logLineCount = 0
      self.logAsciiText = '';
      self.logNumLinesThisPDU = 0

   def ProxyPause(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.ProxyPause
      ;
      ;   RESPONSIBILITY  Issues a proxy pause command to a proxy
      ;                   connection 
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      if self.commWithProxy:
          self.logFile.write("sending proxy pause message\n")
          msg = self.PAUSEALL_PROXY_CMD + "\x00"
          try:
            arrayMsg = array('B',msg)
            self.proxyCtrlSocket.send(arrayMsg)            
          except:
            self.logFile.write("error sending ProxyPause command\n")

          try:
            cmdpat = re.compile(r"([a-zA-Z]+)( \d*)?")
            buf = ""

            r = self.proxyCtrlSocket.recv(self.PROXY_READBUF_SIZE)

            # Parse packet
            buf += r
            li = buf.split("\x00")
            if len(li) > 1:
                for i in li[:-1]:
                    m = cmdpat.match(i)
                    if m:
                        cmd = m.group(1)
                        if cmd == "ok":
                            self.logFile.write("proxy response ok")
                        else:
                            self.logFile.write("error received in proxy" \
                                    "response" + cmd + "\n")
                buf = li[-1]
          except:
            self.logFile.write("error receiving ProxyPause response\n")

      else:
          self.logFile.write("Warning: ProxyPause called on nonproxy socket\n")

   def ProxyContinue(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.ProxyContinue
      ;
      ;   RESPONSIBILITY  Issues a proxy continue command to a proxy
      ;                   connection (supported interfaces only)
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      if self.commWithProxy:
          self.logFile.write("sending proxy continue message\n")
          msg = self.CONTINUE_PROXY_CMD + str(self.tcpPort) + "\x00"
          try:
            arrayMsg = array('B',msg)
            self.proxyCtrlSocket.send(arrayMsg)            
          except:
            self.logFile.write("error sending ProxyContinue command\n")

          try:
            cmdpat = re.compile(r"([a-zA-Z]+)( \d*)?")
            buf = ""

            r = self.proxyCtrlSocket.recv(self.PROXY_READBUF_SIZE)

            # Parse packet
            buf += r
            li = buf.split("\x00")
            if len(li) > 1:
                for i in li[:-1]:
                    m = cmdpat.match(i)
                    if m:
                        cmd = m.group(1)
                        if cmd == "ok":
                            self.logFile.write("proxy response ok")
                        else:
                            self.logFile.write("error received in proxy" \
                                    "response " + cmd + "\n")
                buf = li[-1]
          except:
            self.logFile.write("error receiving ProxyContinue response\n")

      else:
          self.logFile.write("Warning: ProxyContinue called on nonproxy " \
                             "socket\n")

   def ProxyReset(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSocket.ProxyReset
      ;
      ;   RESPONSIBILITY  Issues a proxy reset command to a proxy
      ;                   connection (supported interfaces only)
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      if self.commWithProxy:
          self.logFile.write("sending proxy reset message\n")
          msg = self.RESET_PROXY_CMD + str(self.tcpPort) + "\x00"
          try:
            arrayMsg = array('B',msg)
            self.proxyCtrlSocket.send(arrayMsg)            
          except:
            self.logFile.write("error sending ProxyReset command\n")

          try:
            cmdpat = re.compile(r"([a-zA-Z]+)( \d*)?")
            buf = ""

            r = self.proxyCtrlSocket.recv(self.PROXY_READBUF_SIZE)

            # Parse packet
            buf += r
            li = buf.split("\x00")
            if len(li) > 1:
                for i in li[:-1]:
                    m = cmdpat.match(i)
                    if m:
                        cmd = m.group(1)
                        if cmd == "ok":
                            self.logFile.write("proxy response ok")
                        else:
                            self.logFile.write("error received in proxy" \
                                    "response" + cmd + "\n")
                buf = li[-1]
          except:
            self.logFile.write("error receiving ProxyReset response\n")

      else:
          self.logFile.write("Warning: ProxyReset called on nonproxy socket\n")

   
