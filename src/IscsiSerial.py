"""
********************************************************************************
;
;   MODULE       IscsiSerial.py       
;
;   DESCRIPTION  Source file to provide serial port functions to iscsi tester
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

# import section
import serial as SER
import IscsiPDU as PDU
import time
import IscsiComms as ISOT

class IscsiSerial(ISOT.IscsiComms):

   BAUDRATE        = 115200                    # baud rate
   START_MESSAGE   = "test ISCSITstStart \n"   # CLI command to start test
   TEST_MESSAGE    = "test iscsitstmsg %d \n"  # CLI command to send a message
   SEND_MESSAGE    = "test ISCSITstSend \n"    # CLI command to send test
   RESTART_MESSAGE = "firmwarerestart \n"      # CLI command for restart
   SEND_LINEWAIT   = 0.010                     # 10 ms between lines
   CLI_ERROR       = "ERROR"                   # indicates invalid CLI command
   SERIAL_ECHO_TEST = " dsd89032379042s0 \n"   # Random string for testing
                                               # serial port echo on the device

   def __init__(self,logfile):
      
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.__init__
      ;
      ;   RESPONSIBILITY  IscsiSerial class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance to
      ;                                  initialize
      ;                logfile       I    The logfile to use.
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # init base class stuff
      ISOT.IscsiComms.__init__(self,logfile)
      
      # Set up serial port at COM1
      self.ser = SER.Serial()
      self.ser.baudrate = self.BAUDRATE
      self.ser.timeout = 10
      self.ser.port = "COM1"


   def CookPDU(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.CookPDU
      ;
      ;   RESPONSIBILITY  Chunks a PDU up into 1200 byte frames and sends
      ;        them on the serial port.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;                pdu           I    The PDU to send 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
   
      # serialize the PDU to prepare for sending
      serialPdu = pdu.Serialize(self.testcase)
      pdulen = bytesLeft = len(serialPdu)
                  
      # now that I have a serialized PDU, update all the
      # applicable test variables.
      print("Sending a PDU...")
      print("Calling UpdateSendVars")
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
                  
      # send the PDU in chunks
      while bytesLeft:
         bytesThisChunk = min(bytesLeft,self.PDU_CHUNKSIZE)
         bytesLeft -= bytesThisChunk
         self.ser.write(self.TEST_MESSAGE  % bytesThisChunk)
         self.logFile.write(self.TEST_MESSAGE  % bytesThisChunk)

         while bytesThisChunk:
            # each line is 64 bytes long     
            bytesThisLine = min(bytesThisChunk, self.LINE_SIZE)
            for i in range(bytesThisLine):
               bytetowrite = serialPdu.pop(0)
               self.ser.write("%02x" % bytetowrite )
               self.logFile.write("%02x" % bytetowrite)
               # put a space in, but not at the end of a line
               if i != (self.LINE_SIZE-1):
                  self.ser.write(" ")
                  self.logFile.write(" ")
               
               
            # end of line, write a CR
            self.ser.write("\n")
            self.logFile.write("\n")
            bytesThisChunk -= bytesThisLine
            # wait  between lines to be nice.
            time.sleep(self.SEND_LINEWAIT)
         
   def Open(self,testcase):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.Open
      ;
      ;   RESPONSIBILITY  Sends the iscis test start message
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;                pdu           I    The PDU to send 
      ;                testcase      I/O  The current test case (holds globals 
      ;                                      like CMDSN, ITT, etc.
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """    
           
      while 1:
         try:
            self.ser.open()
            break
         except SER.SerialException as e:
           print("Problem opening serial port... Teraterm must be closed.")
           print(e)
           time.sleep(5)
            
      
      if self.ser.isOpen():
         print("Serial Port "+self.ser.port+" Is open.")
         self.ser.timeout = None
      else:
         print("Problem opening serial port. ")

      self.logFile.write( "sending start CLI message...\r\n")
      self.ser.write(self.START_MESSAGE)
      self.logFile.write(self.START_MESSAGE)
      self.ReadToReady()
      self.testcase = testcase
      
      # Check for device serial port echo off
      print("Checking device's serial port echo:", end=' ')
      self.ser.write(self.SERIAL_ECHO_TEST)
      token = self.GetToken()
      if token != self.CLI_ERROR:
          print("Failed.")
          print("DEVICE'S SERIAL PORT ECHO IS ON!!!")
          print("Serial echo must be turned off...")
          print("Please Exit")
          return ISOT.OUT_START_FAIL
          
      self.ReadToReady()
      print("Passed.")
      
      return ISOT.OUT_START_PASS
         
   def ReadInStream(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.ReadInStream
      ;
      ;   RESPONSIBILITY  Reads all of the streaming output data (until a Ready
      ;     prompt) into a list of integers (self.dataList). Assumes that an
      ;     iscsitestsend was just executed
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      endofcmd = False
      self.logLineCounter = 0;
      while not endofcmd:
         token = ""
         token = self.GetToken()
         if self.IsHex(token):
            #append this value onto self's datalist
            self.dataList.append(int(token,16))
         else:
            endofcmd = True
            
   def ReadInPdus(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.ReadInPdus
      ;
      ;   RESPONSIBILITY  Reads data from the host and parses the outputs
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS    The list of PDUs returned.
      ;
      ;   Note: it's a good idea to call ForwardPDus right before calling
      ;     this method.
      ;
      ************************************************************************
      """ 
      # get the current stream of bytes (up to a ready prompt)
      self.ReadInStream()
      self.logFile.write("\n")
      pdulist = []
      while len(self.dataList):
         pduTmp = PDU.IscsiPdu()
         pduTmp.DeSerialize(self.dataList,self.testcase)
         pdulist.append(pduTmp)
      
      return pdulist 

   def RestartComms(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.RestartComms
      ;
      ;   RESPONSIBILITY  Does nothing
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSocket class instance 
      ;
      ;   RETURNS     nothing
      ;
      ************************************************************************
      """    
      time.sleep(wait)
      return
             
   def GetToken(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.GetToken
      ;
      ;   RESPONSIBILITY  skips whitespace, then reads to first non-whitespace
      ;        into the given string
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS     Token
      ;
      ;
      ************************************************************************
      """
      token = ""
      whitespace = (' ','\r','\n')
      
      # skip leading whitespace
      c = ' '
      while c in whitespace:
         c = self.ser.read(1)
         self.logFile.write(c)
         
      # not at whitespace, read until whitespace
      while c not in whitespace:
         token = token + c
         c = self.ser.read()
         self.logFile.write(c)
      
      # bump log line counter
      self.logLineCounter += 1
      if self.logLineCounter == self.LINE_SIZE:
         self.logLineCounter = 0
         self.logFile.write("\n")
      
      return token
   
   def IsHex(self,string):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.IsHex
      ;
      ;   RESPONSIBILITY  returns true if everything in the string is a
      ;        hex digit
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS     true or false
      ;
      ;
      ************************************************************************
      """   
      searchlist = ('0','1','2','3','4','5','6','7','8','9',\
                    'a','b','c','d','e','f','A','B','C','D','E','F')
            
      for c in string:
         if c not in searchlist:
            return False
      return True
                      
         
   def ReadToReady(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.ReadToReady
      ;
      ;   RESPONSIBILITY  reads until a ready is found 
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS     true or false
      ;
      ;
      ************************************************************************
      """  
      keepGoing = True
      
      while keepGoing:
         token = self.GetToken()
         if token == "Ready.":
            keepGoing = False
            
            
   def ForwardPDUs(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.ForwardPDUs
      ;
      ;   RESPONSIBILITY  Asks DUT to execute the test and performs any 
      ;     preliminaries needed before reading stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      # pause for 1/2 second
      time.sleep(0.5)
      # flush all of the input so our read is clean.
      self.ser.flushInput()
      # send the send message
      self.ser.write(self.SEND_MESSAGE)
      self.logFile.write(self.SEND_MESSAGE)
      
   def SendRestart(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiSerial.SendRestart
      ;
      ;   RESPONSIBILITY  Asks DUT to firmwarerestart
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiSerial class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      self.ser.write(self.RESTART_MESSAGE)
      self.logFile.write(self.RESTART_MESSAGE)
