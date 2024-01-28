"""
********************************************************************************
;
;   MODULE       IscsiComms.py       
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
import IscsiPDU as PDU
import time
import threading

# Global Constants
# Pass and fail for the IscsiComms start method
OUT_START_PASS = 1  
OUT_START_FAIL = 0

class IscsiComms(threading.Thread):



   PDU_CHUNKSIZE   = 1200           # size of a pdu chunk for sending
                                    # this is effectively the MTU of the 
                                    # network minus the frame header (if any).
   LINE_SIZE       = 16             # number of byte per line (for logging )
   ISCSI_BHS_SIZE  = 48             # BHSs are 48 bytes (with no ahs)
   LOGFILE_ASCII_SPACER = " | "     # spacer between hex & ascii output
   LOGFILE_RXPDU_HDR = "PDU RECEIVED\n"   # header for received pdu
   LOGFILE_RXDATA_HDR = "DATA RECEIVED\n" # header for data received
                                         
   def __init__(self,logfile):
      
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.__init__
      ;
      ;   RESPONSIBILITY  IscsiComms class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance to
      ;                                  initialize
      ;                logfile     I/O  The iSCSI log file to use
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # init the threading stuff
      threading.Thread.__init__(self) 
      # since all PDU's are logged to the output, there's a log line counter
      # to format the log nicely.
      self.setDaemon(True)
      self.logLineCounter = 0
      # keep track of the log file
      self.logFile = logfile
      self.dataString = ''
      self.rxPduList = []
      self.rxPduLock = threading.Lock()
      self.terminateAtNextOpportunity = False

      # keep track of what we are communicating to (either a DUT or a
      # proxy to the DUT)
      self.commWithProxy = False

            
   def CookPDU(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.CookPDU
      ;
      ;   RESPONSIBILITY  Pure virtual function: chunks a PDU up into frames 
      ;     and to prepare them for being sent.  As they're being chunked up
      ;     they should be written to the logfile. 
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;                pdu           I    The PDU to send 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      self.logFile.write("Preparing to send PDU on link\n")
      self.logFile.write("Warning: Cook not implemented on this interface!\n")
      
      # serialize the PDU to prepare for sending
      serialPdu = pdu.Serialize(self.testcase)
      pdulen = bytesLeft = len(serialPdu)
                  
      # now that I have a serialized PDU, update all the
      # applicable test variables.
      self.testcase.UpdateSendVars(serialPdu)
      # we may need to turn digests on for the return trip
      if pdu.headerDigest != "0":
         print("turning on header digest ")
         self.testcase.headerDigest = True
      else:
         print("turning off header digest")
         self.testcase.headerDigest = False
         
      if pdu.dataDigest != "0":
         print("turning on data digest")
         self.testcase.dataDigest = True
      else:
         print("turning off data digest")
         self.testcase.dataDigest = False
                  
      # send the PDU in chunks
      while bytesLeft:
         bytesThisChunk = min(bytesLeft,self.PDU_CHUNKSIZE)
         bytesLeft -= bytesThisChunk
         while bytesThisChunk:
            # each line is 64 bytes long     
            bytesThisLine = min(bytesThisChunk, self.LINE_SIZE)
            for i in range(bytesThisLine):
               bytetowrite = serialPdu.pop(0)
               self.logFile.write("%02x" % bytetowrite)
               # put a space in, but not at the end of a line
               if i != (self.LINE_SIZE-1):
                  self.logFile.write(" ")
               
               
            # end of line, write a CR
            self.logFile.write("\n")
            bytesThisChunk -= bytesThisLine
      
   
   def Open(self,testcase):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.Open
      ;
      ;   RESPONSIBILITY  Opens a comms link.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;                testcase      I/O  the test case to use
      ;
      ;   RETURNS     PASS or FAIL, depending on needs of link
      ;
      ************************************************************************
      """    
           
      self.logFile.write("Opening link\n")
      self.testcase= testcase
      self.terminateAtNextOpportunity = False
      return(OUT_START_PASS)
         
            
         
   def ForwardPDUs(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.ForwardPDUs
      ;
      ;   RESPONSIBILITY  Sends the PDUs out on the link
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """    
           
      self.logFile.write("sending PDUs out on the link\n")
      self.logFile.write("Warning: Forward not implemented on this interface\n")
         
            
   def ReadInPdus(self,wait):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.ReadInPdus
      ;
      ;   RESPONSIBILITY  Reads data from the host and parses the outputs
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;                wait          I/O  how long to wait for pdus
      ;
      ;   RETURNS    The list of PDUs returned.
      ;
      ;   Note: it's a good idea to call ForwardPdus right before calling
      ;     this method.
      ;
      ************************************************************************
      """ 
      # nothing here is implemented, just sleep, then return the pdu list.
      time.sleep(wait)
      
      return self.rxPduList
  
   def RestartComms(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.RestartComms
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
             
 
   def SendRestart(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.SendRestart
      ;
      ;   RESPONSIBILITY  Asks DUT to restart itself
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      self.logFile.write("sending restart message out on the link\n")
      self.logFile.write("Warning: restart not implemented on this interface\n")
      
   def run(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.run
      ;
      ;   RESPONSIBILITY  Thread to read in pdus and place them on pdulist
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      while 1:
          # for each pdu read in , place it on the PDU list to return.  Like so.
          pduTmp = PDU.IscsiPdu()
          pduTmp.DeSerialize(self.dataString,self.testcase)
          self.rxPduList.append(pduTmp)
           
          time.sleep(30) 
          if self.terminateAtNextOpportunity : 
              break;
           
   def Kill(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.Kill
      ;
      ;   RESPONSIBILITY  cause the main thread to terminate
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;                self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      self.terminateAtNextOpportunity = True
      threading.Thread.join(self,5)

   def ProxyPause(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.ProxyPause
      ;
      ;   RESPONSIBILITY  Issues a proxy pause command to a proxy
      ;                   connection (supported interfaces only)
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      self.logFile.write("sending proxy pause message\n")
      self.logFile.write("Warning: ProxyPause not implemented\n")

   def ProxyContinue(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.ProxyContinue
      ;
      ;   RESPONSIBILITY  Issues a proxy continue command to a proxy
      ;                   connection (supported interfaces only)
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      self.logFile.write("sending proxy continue messge\n")
      self.logFile.write("Warning: ProxyContinue not implemented\n")

   def ProxyReset(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiComms.ProxyReset
      ;
      ;   RESPONSIBILITY  Issues a proxy reset command to a proxy
      ;                   connection (supported interfaces only)
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiComms class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ;
      ************************************************************************
      """
      self.logFile.write("sending proxy reset message\n")
      self.logFile.write("Warning: ProxyReset not implemented\n")


