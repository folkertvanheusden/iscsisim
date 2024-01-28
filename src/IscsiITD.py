"""
********************************************************************************
;
;   MODULE       IscsiItd.py       
;
;   DESCRIPTION  Source file for the iscsi Test Description class
;
;   This file is part of iSCSISim.
;
;   Copyright (c) 2009,2018 ATTO Technology, inc.
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
import os
import xml.etree.ElementTree as ET
import IscsiPDU as PDU
import ITDSeqList
import time

class IscsiItd:
   KEY_NONE = "$NONE"
   KEY_DELAY = "Delay"
   READ_TIMEOUT = 1  # read timeout in seconds
    
   CONNECTION_ACT_NOACTION = "Keep"
   CONNECTION_ACT_NEW = "New"
   CONNECTION_ACT_REUSE = "Reuse"
   CONNECTION_ACT_RESET = "GenReset"
   CONNECTION_ACT_PAUSE = "Pause"
   CONNECTION_ACT_CONTINUE = "Continue"
   CONNECTION_TARGET_DUT = "DUT"
   CONNECTION_TARGET_PROXY = "Proxy"
   CONNECTION_ACT_TCPRESET = "TcpReset"
          
   def __init__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.__init__
      ;
      ;   RESPONSIBILITY  IscsiPdu class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiPdu class instance to
      ;                                  initialize
      ;
      ;   Valid Keywords for Test Descriptor fields:
      ;     $NONE : substitute for a trigger in an output file(stored as 0)
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # set up the Itd class.  I probably don't have to do this but, hey,
      # 'c' habits die hard.
      self.name = ""
      # command sequence list and run list are internal structures used
      # to hold the contents of the current ITD.
      self.cmdSeqList = ITDSeqList.ITDSeqList()
      # run list is a list of command identifiers and triggers
      self.runList = []
      # active seq list is used for commands which are outstanding
      self.activeSeqList = ITDSeqList.ITDSeqList()
      # current runlist entry is the index into the run list
      self.currentRunlistEntry = 0
      # error flag
      self.errorOccurred = False
      # indicates test is complete
      self.testDone = False     
       
   def LoadFromXMLFile(self, filename, config):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.LoadFromXMLFile
      ;
      ;   RESPONSIBILITY  Read a test description from an XML file.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test description class instance 
      ;               filename       I   Filename to parse from
      ;               config         I   iscsi config object
      ;
      ;   RETURNS     False if an error occurred
      ;
      ************************************************************************
      """  
      if filename:
      
         print("-------------------------------------")
         print("Loading Test Description: ", filename)
         print("-------------------------------------")
         self.name = filename
         tree = ET.parse(filename)
         tdelem = tree.getroot()
         if tdelem.tag != "ISCSITD":
            exep = Exception("File " + filename + " did not contain ISCSITD tag")
            raise exep
         else:
            # Load the command sequence list
            seqlistelem = tdelem.find("CmdSeqList")
            if seqlistelem is not None:
               # found a list of outfiles in a ITD.  Start filling in fields
               seqlist = seqlistelem.findall("CmdSeq")
               for seqelem in seqlist:
                  seqid = int(seqelem.get("Id"))
                  # ex = Exception("No id found for sequence in "+filename)
                  # raise ex
                  if self.cmdSeqList.FindEntryId(seqid) != None:
                     ex = Exception("Duplicate cmd sequence id of %d in " 
                                     % seqid + filename)
                     raise ex
                  
                  # okay, so there's a new sequence with an id, add an
                  # entry to the command sequence list
                  handle = self.cmdSeqList.PushEntry(seqid)
                  
                  # Read in all of the pdu's 
                  pdulist = seqelem.findall("PDU")
                  for pduelem in pdulist:
                     # get the id of this pdu element 
                     pduid = int(pduelem.get("i"))
                     # get the filename 
                     pdu_filename = pduelem.text
                     pdu_filename_parts = pdu_filename.rsplit(os.sep)
                     pdufilename = os.path.join(*pdu_filename_parts)
             
                     pdu = PDU.IscsiPdu()
                     pdu.LoadFromXMLFile(pdufilename, config)
                  
                     self.cmdSeqList.AddPdu(handle, pdu, pduid)
            else:
                ex = Exception("No Cmd SeqList found in %s" % filename)
                raise ex
            
            # now load the run list(that's a lot simpler, just tuples & triggers)   
            runlistelem = tdelem.find("RunList")
            if runlistelem is not None:
               runlist = runlistelem.findall("R")
               for rle in runlist:
                   # pull in the trigger 
                   trig = rle.get("Trig")
                   if trig == None or trig == self.KEY_NONE:
                      trig = (PDU.IscsiPdu.BAD_TRIGGER, PDU.IscsiPdu.BAD_TRIGGER)
                   else:
                      # a quick check here - is this the 1st element in the list
                      # with a trigger? if so, exception.
                      if len(self.runList) == 0:
                          ex = Exception("TRigger in 1st element of runlist " \
                                         + filename)
                          raise ex
                    
                      # otherwise pull the trigger out of the list
                      trig = self.ParseTrig(trig)

                   # now get the transmittable thingadealy
                   r = rle.text
                   if r == None or r == self.KEY_NONE:
                       # no error, so load up the tupe with a trigger value.
                       rt = (PDU.IscsiPdu.BAD_TRIGGER, PDU.IscsiPdu.BAD_TRIGGER)
                   else:
                       # check to make sure last element of runlist has nothing
                       # to send (just like 1st can't have a trigger)
                       if runlist.index(rle) == (len(runlist) - 1):
                           ex = Exception("Last element of Run List is not " + 
                                       "EMPTY (has to be None) in " + filename)
                           raise ex
                       # no error, so put the value in a tuple
                       rt = r.strip('()').split(',')
                       rt = tuple([int(i) for i in rt])
                   
                   # Pull in any connection-oriented stuff
                   # Tuple is as follows: connection, target
                   reinstate = (self.CONNECTION_ACT_NOACTION,
                                self.CONNECTION_TARGET_DUT) 

                   connect = rle.get("Connection")
                   if connect != None:
                       print(connect)
                   
                   
                   if connect != None and connect != \
                        self.CONNECTION_ACT_NOACTION:
                        # we actually will pay attention to it
                        connectAct = connect                        
                        reinstateTarget = rle.get("Target")
                        # oldConnAct = rle.get("OldConn")
                        # newConnAct = rle.get("NewConn")

                        reinstate = (connectAct,
                                     reinstateTarget) 
                        print(reinstate)

                   # append the trigger, list and reinstate tuple to the runlist
                   self.runList.append((trig, rt, reinstate))
                      
            else:
                ex = Exception("No Run List found in %s" % filename)
                raise ex

      else:
         ex = Exception("Bad filename %s" % filename)
         raise ex                
                       
   def ParseTrig(self, trig):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.ParseTrig
      ;
      ;   RESPONSIBILITY  Parse the trigger field.  The trigger could
      ;     be a delay or a tuple at this point.  Figure that out and return
      ;     the parsed trigger.
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I    The test description class instance 
      ;               trig          I    The trigger string to parse  
      ;
      ;   RETURNS     tuple - (n,n) if valid, (DELAY_TRIGGER,n) if valid,
      ;                raises exception if not valid.
      ;
      ************************************************************************
      """  
      # check first for a delay 
      if self.KEY_DELAY in trig:
          trig = trig.strip(self.KEY_DELAY)
          i = float(trig)
          trig = (PDU.IscsiPdu.DELAY_TRIGGER, i)
      else:
          trig = trig.strip('()').split(',')
          # me likey list comprehensions.  much nicer than map()
          trig = tuple([int(i) for i in trig])
      return trig

   def StepTest(self, testcase, logfile, currentComms, comms, proxyComms):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.StepTest
      ;
      ;   RESPONSIBILITY  Run the next step in the current test
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test description class instance
      ;               testcase      I/O  The 'test case' being used
      ;               logfile       I/O  The log file for printing stuff
      ;               currentComms  I/O  Current communications socket
      ;               comms         I/O  Socket pointed to the DUT
      ;               proxyComms    I/O  Socket pointed to the proxy
      ;
      ;   RETURNS     The current active comms object
      ;
      ;                         self.ErrOccurred is updated
      ;                         self.currentRunListEntry is updated
      ;
      ************************************************************************
      """   

      # get the current runlist element. Make sure the list isn't done.
      if self.currentRunlistEntry >= (len(self.runList) - 1):
         self.testDone = True
         return currentComms

      # set up the tcp connection reset flag 
      resetTcp = False      

      # Handle any connection reinstate for this entry
      rle = self.runList[self.currentRunlistEntry] 
      if(rle[2][0] != self.CONNECTION_ACT_NOACTION):
          print("Connection modification")
          if(rle[2][0] == self.CONNECTION_ACT_NEW):
              # We want to send a pauseall command if it is a proxy, then
              # kill the comms thread. Start a new comms thread on
              # the other comms object, set currentComms to it, and
              # then we can return.
              targetComms = rle[2][1]
              targetCommsObj = None
 
              if(targetComms == self.CONNECTION_TARGET_DUT):
                 # new connection target is the DUT
                 targetCommsObj = comms                            
                 print("New connection target is DUT")
              else:
                 # new connection target is the proxy
                 targetCommsObj = proxyComms
                 print("New connection target is Proxy")
 
              if(currentComms.commWithProxy):
                 currentComms.ProxyPause()
 
              # If the current comms is destined to be idle, don't kill it
              if(currentComms == proxyComms or currentComms == comms):
                  currentComms.Kill()

              targetCommsObj.Open(currentComms.testcase)
                  
              if(targetCommsObj.commWithProxy):
                 targetCommsObj.ProxyContinue()
 
              targetCommsObj.start()
              currentComms = targetCommsObj

      # Get the current rle to process.  We're guaranteed at this point that
      # the thread is not waiting for a trigger and that the element to send
      # is valid... so... send until a trigger is encountered.
      armed = False
        
      while not (armed or self.testDone):
         rle = self.runList[self.currentRunlistEntry]
         sendpdu = self.cmdSeqList.GetPduFromListElement(rle[1])
         # if this is the first pdu in the element, push it the element onto
         # the active sequence list queue.  
         # - remember RLE[1] is (CmdSeqId,PDUId)
         if rle[1][1] == 1:
             testcase.activeHandle = \
                       self.activeSeqList.PushCopy(\
                                   self.cmdSeqList.GetListElement(rle[1][0]))
         else:
             # this element is active, so find it based on the element's id.
             testcase.activeHandle = self.activeSeqList.FindEntryId(rle[1][0])
         
         # if pdu is supposed have cmdsn ignored, do that now
         if sendpdu is not None:
             testcase.ignoreCmdSn = sendpdu.ignoreCmdSn
             # now send the pdu out.
             logfile.write("\n--------------------------------------------------")
             logfile.write("\n----SENDING PDU (%d,%d) ..." % rle[1])
             logfile.write("\n--------------------------------------------------\n")
             print("sending (%d,%d)" % rle[1])
             currentComms.CookPDU(sendpdu)
             currentComms.ForwardPDUs()
             
         # bump current runlist entry
         self.currentRunlistEntry += 1
         if self.currentRunlistEntry >= len(self.runList):
             self.testDone = True
         else:
             # check if new entry has a trigger
             rle = self.runList[self.currentRunlistEntry]
             # trigger might be a delay or a PDU. Check for delay first
             if rle[0][0] == PDU.IscsiPdu.DELAY_TRIGGER:
                 print("Delaying for %f seconds" % rle[0][1])
                 for i in range(int(rle[0][1]), 0, -1):
                    time.sleep(1)
                    print(i)
                 print()
                 # sleep any fraction of a second
                 time.sleep(rle[0][1] - int(rle[0][1]))
                 armed = False  # don't look for a pdu from this trigger
             else:
                 triggerpdu = self.cmdSeqList.GetPduFromListElement(rle[0])
                 if triggerpdu:
                     armed = True
    
      # Got here.  Either the test is done (which would be an anomaly because
      # the last has to have a trigger, but okay, cosmic rays and all that) or
      # this case needs to wait for a trigger to come in.
      if armed:
         print("Reading PDUs... wait")
         logfile.write("\n--------------------------------------------------")
         logfile.write("\n----WAITING FOR PDUs FROM HOST...");
         logfile.write("\n--------------------------------------------------\n")
         rxpdulst = currentComms.ReadInPdus(self.READ_TIMEOUT)
         logfile.write ("%d pdus read from DUT \r\n" % len(rxpdulst))
         
         # reset comms after trigger if that's requested
         # if we got here and the TCP needs to be reset, do that.
         if rle[2][0] == self.CONNECTION_ACT_TCPRESET:
            currentComms.RestartComms()


         # now handle the trigger PDU
         # okay, so there's a quirk here:
         # - we may need to ignore one or more of the pdu's in the pdu list.  
         # So check to see if the trigger was received, but ignore other pdus 
         # preceeding the trigger.
         # - several triggers may occur without elements to send.  If the 
         # current entry is 'trigger only' AND the trigger is found, AND
         # there are more pdu's in the pdu list, compare with the next trigger.
         triggerfound = False
         i = 0
         for rxpdu in rxpdulst:
             # keep track of index for size check 
             i += 1
             # See if the trigger we're looking for was found.
             if triggerpdu.IsEqual(rxpdu, testcase, logfile):
                 logfile.write("Trigger PDU (%d,%d) compare successful \r\n" % \
                                                          (rle[0][0], rle[0][1]))
                 # trigger was found.  If rle is trigger only, step it and
                 # wait for the next trigger.
                 rle = self.runList[self.currentRunlistEntry]
                 if rle[1][0] == PDU.IscsiPdu.BAD_TRIGGER:
                    # bump current runlist entry
                    self.currentRunlistEntry += 1
                    if self.currentRunlistEntry >= len(self.runList):
                       # runlist exhausted.  The last one compared. status ok.
                       triggerfound = True
                       self.testDone = True
                       break
                    #  See if another pdu is available
                    if i >= len(rxpdulst):
                        # no more pdu's Rx'd. The last one compared.  status ok.
                        triggerfound = True
                        break
                    # another PDU is available, load it up for the comparision
                    triggerpdu = self.cmdSeqList.GetPduFromListElement(
                                    self.runList[self.currentRunlistEntry][0])
                    
                 else:
                    # rle is not trigger only, so mark it as found and return
                    # so that upper level class can step the test.
                    triggerfound = True
                    break
             
         if not triggerfound:
             logfile.write("ERROR PDU %s did not compare in test %d.\r\n" % 
                           (triggerpdu.name, self.currentRunlistEntry))
             logfile.write("ITD = %s trigger = (%d,%d) \r\n" % (self.name,rle[0][0],rle[0][1]))                          
             self.errorOccurred = True

      return currentComms
  
   def ErrOccurred(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.ErrOccurred
      ;
      ;   RESPONSIBILITY  Clear-on-read accessor for test case errors
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test description class instance
      ;               testcase      I/O  The 'test case' being used
      ;
      ;   RETURNS     False if an error occurred
      ;
      ************************************************************************
      """     
      if (self.errorOccurred):
         ret = True
      else:
         ret = False
      self.errorOccurred = False
      return(ret)    
   
   def TestDone(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.TestDone
      ;
      ;   RESPONSIBILITY  Returns true if the test is completed
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiItd class instance 
      ;
      ;   RETURNS     true if test is completed
      ;
      ************************************************************************
      """ 
      return self.testDone
           
                  
   def Print(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiItd.Print
      ;
      ;   RESPONSIBILITY  Prints an iscsi test descriptor class
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiItd class instance 
      ;
      ;   RETURNS     nothing.
      ;
      ************************************************************************
      """ 
      
      print("ITD: ", self.name)
      print("CmdSeqLIST::::::::::::::::::::::::::::::::::::::::::::::::::")
      self.cmdSeqList.Print()
      print("RunList ::::::::::::::::::::::::::::::::::::::::::::::::::::")
      print("Current runlist entry is ", self.currentRunlistEntry)
      for i in self.runList:
          print("Trig: ", i[0], " RLE: ", i[1])
      print("ActiveSeqList ::::::::::::::::::::::::::::::::::::::::::::::")
      self.activeSeqList.Print()
                
 
# ******************************* TEST CODE *************************
"""
    itd = IscsiItd()
    config = IscsiCfg()
    itd.LoadFromXMLFile("test.xml",config)
    itd.Print()
"""

