"""
********************************************************************************
;
;   MODULE       IscsiPdu.py       
;
;   DESCRIPTION  Source file for the QuickNAV wizard web server link page
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

# import section
import xml.etree.ElementTree as ET
from crc32c import Crc32c,ishexstring
import os
import string
import IscsiComms
import struct


class IscsiPdu:
   BAD_TRIGGER = 9999
   DELAY_TRIGGER = "DELAY"
   BAD_ITT = 0xFFFFFFFF
   KEY_CMDSN = "$CMD_SN"
   KEY_EXPSTSN = "$EXP_STAT_SN"
   KEY_ITT = "$ITT"
   KEY_TTT = "$TTT"
   KEY_TSIH = "$TSIH"
   KEY_DONTCARE = "$X"
   KEY_DIGEST = "$DIGEST"
   KEY_CID = "$CID"
   KEY_TGTNAME = "$TGTNAME$"
   PDU_KEY_TUPLE = (KEY_CMDSN, KEY_EXPSTSN, KEY_ITT, KEY_TSIH, KEY_DONTCARE)
    
   def __init__(self):
        """
        ************************************************************************
        ;
        ;   FUNCTION        IscsiPdu.__init__
        ;
        ;   RESPONSIBILITY  IscsiPdu class initializer
        ;
        ;   PARAMETERS  Name          I/O  Description                
        ;               self          I/O  The IscsiPdu class instance to
        ;                                  initialize
        ;
        ;   Valid Keywords for PDU fields:
        ;     $CMD_SN : gets the current value of command sn
        ;     $EXP_STAT_SN : gets the current value of expected stat sn
        ;     $ITT : gets the current (last sent) value of initator task tag
        ;     $TTT : gets the current (last received) value of target task tag
        ;     $TSIH : whatever the heck that stands for 
        ;           
        ;
        ;   RETURNS     Nothing
        ;
        ************************************************************************
        """
        # set up the PDU class.  I probably don't have to do this but, hey,
        # I'm a 'c' programmer.
        self.name = ""        
        # Note that these are mostly STRINGS to allow for keyword substitution
        # later.
        self.dword1 = "0"
        self.ahsLen = "0"
        self.dataSegLen = "0"
        self.lun = "0"
        self.itt = "0"
        # Dwords at offset 24 through 44 are chameleon fields, so they're not
        # named.  They could still get keywords.
        self.dw20 = "0"
        self.dw24 = "0"
        self.dw28 = "0"
        self.dw32 = "0"
        self.dw36 = "0"
        self.dw40 = "0"
        self.dw44 = "0"
        self.headerDigest = "0"
        self.dataDigest = "0"

        # Update tsih in LUN (boolean flag)
        self.updateTsih = False
        # Compare the tsih when receiving data from target (boolean flag)
        # This defaults to true because most PDUs should compare the entire
        # field.
        self.compareTsih = True
        
        self.dataLen = 0
        self.data = [ ]
        self.config = ''
        
        # compare field tells us whether to compare on a output test
        self.compareData = True
        # keep track of ignore cmdsn flag for testcase's use later.
        self.ignoreCmdSn = False
        
   def LoadFromXMLFile(self,filename,config):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.LoadFromXMLFile
         ;
         ;   RESPONSIBILITY  Read a PDU from an XML file.
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance 
         ;               filename       I   Filename to parse from
         ;               config         I   iscsi configuration object
         ;
         ;   RETURNS     nothing
         ;
         ************************************************************************
         """  
         if filename:
         
            print("Loading PDU from file: ", filename)
            self.name = filename
            Tree = ET.parse(filename)
            pduElem = Tree.getroot()
            if pduElem.tag != "ISCSIPDU":
               ex = Exception("File "+filename+" did not contain ISCSIPDU tag")
               raise ex
            else:
               # look for ignore cmdsn flag
               ignore = pduElem.get("IgnoreCmdSN")
               if ignore:
                   if ignore == "True":
                       self.ignoreCmdSn = True

               # start loading the BHS
               BhsElem = pduElem.find("BHS")
               if BhsElem is not None:
                  # found a BHS in a PDU.  Start filling in fields
                  
                  self.dword1 = BhsElem.findtext("DWORD1")
                  self.ahsLen = BhsElem.findtext("AHSLEN")
                  self.dataSegLen = BhsElem.findtext("DATASEGLEN")
                  self.lun = BhsElem.findtext("LUN")
                  self.itt = BhsElem.findtext("ITT")
                  self.dw20 = BhsElem.findtext("DW20")
                  self.dw24 = BhsElem.findtext("DW24")
                  self.dw28 = BhsElem.findtext("DW28")
                  self.dw32 = BhsElem.findtext("DW32")
                  self.dw36 = BhsElem.findtext("DW36")
                  self.dw40 = BhsElem.findtext("DW40")
                  self.dw44 = BhsElem.findtext("DW44")
                  if pduElem.findtext("HEADERDIGEST"):
                     self.headerDigest = pduElem.findtext("HEADERDIGEST")
                  if pduElem.findtext("DATADIGEST"):
                     self.dataDigest = pduElem.findtext("DATADIGEST")
        
                  # Check for the TSIH attribute in the LUN element.
                  # If it is set to "current," fill in the LUN field
                  # with the current TSIH. Also load whether or not TSIH
                  # should be compared.
                  LunElem = BhsElem.find("LUN")
                  tsihAttrib = LunElem.get("tsih")
                  if tsihAttrib == "current":
                     self.updateTsih = True
                  tsihCompare = LunElem.get("comparetsih")
                  if tsihCompare == "false":
                     self.compareTsih = False

                  DataElem = pduElem.find("DATA")
                  if DataElem is not None:
                     lenAttrib = DataElem.get("len")
                     if lenAttrib is not None:
                        self.dataLen = int(lenAttrib,16)
                        data_filename = DataElem.findtext("FILE")
                     else:
                        self.dataLen = 0
                        
                     compareAttrib = DataElem.get("compare")
                     if compareAttrib:
                        if compareAttrib == "True":
                           self.compareData = True
                        elif compareAttrib == "False":
                           self.compareData = False
                        else:
                           ex = Exception("File "+filename+" data compare is "+
                                           "not 'True' or 'False' (check case)")
                           raise ex                                           
                        
                        
                     if self.dataLen != 0 and data_filename:
                        try:
                           data_filepath_parts = data_filename.rsplit(os.sep)
                           datafilename = os.path.join(*data_filepath_parts)
                           f = open(datafilename,"rb")
                           # read data from the binary file
                           self.data = f.read(self.dataLen)
                           
                           # might have to fill in target name
                           self.config = config
                           if DataElem.get("login") and self.config.targetName:
                               self.FixUpTargetName()
                           
                        except IOError:
                           ex = Exception("File "+filename+ 
                                          " had problem opening " + data_filename)
                           raise ex
                     else:
                        if lenAttrib is not None and self.dataLen != 0:
                           ex = Exception("File "+filename+  
                                        " has misformed len attribute")
                           raise ex
                  
               else: 
                  ex = Exception("File "+filename+" did not contain BHS tag")
                  raise ex
               
         else:
            ex = Exception( "Bad Filename:"+filename+" in PDU load")
            raise ex   
    
   def Print(self):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.Print
         ;
         ;   RESPONSIBILITY  Prints an iscsi PDU
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance 
         ;
         ;   RETURNS     nothing.
         ;
         ************************************************************************
         """ 
         print("dword1     : "+self.dword1)
         print("ahslen     : "+self.ahsLen)
         print("dataseglen : "+self.dataSegLen)
         print("lun        : "+self.lun)
         print("itt        : "+self.itt)
         print("dw20       : "+self.dw20)
         print("dw24       : "+self.dw24)
         print("dw28       : "+self.dw28)
         print("dw32       : "+self.dw32)
         print("dw36       : "+self.dw36)
         print("dw40       : "+self.dw40)
         print("dw44       : "+self.dw44)
         print("headerdigst: "+self.headerDigest)
         print("datadigest : "+self.dataDigest)
         print("datalen    : %x" % self.dataLen)
         print("data       : ")
         for i in range(0,min(self.dataLen,15)):
            print(self.data[i], end=' ')
         print()

   def FixUpTargetName(self):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.FixUpTargetName
         ;
         ;   RESPONSIBILITY  places target name from config file into the 
         ;            data file.  Adjusts overall length.
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance 
         ;
         ;   RETURNS     nothing.
         ;
         ;   NOTE: LENGTH ADJUSTMENT - if the data file has a $TGTNAME$ token in
         ;    it, then the BHS' data length is adjusted by: 
         ;        dataseglen += strlen(cfg file string) - strlen("$TGTNAME$)
         ;
         ************************************************************************
         """
         # self.data has the whole string, replace it
         replCnt = 0
         print(type(self.KEY_TGTNAME), self.KEY_TGTNAME)
         print(type(self.data), self.data)
         print(type(self.config.targetName), self.config.targetName)
         while self.KEY_TGTNAME.encode('ascii') in self.data:
            self.data = self.data.replace(self.KEY_TGTNAME.encode('ascii'),                    \
                                          self.config.targetName.encode('ascii'),1)
            replCnt += 1
         
         print("replaced %s with %s %d times" %                                \
               (self.KEY_TGTNAME,self.config.targetName,replCnt))
         print("old dataseglen: %s" % self.dataSegLen)
            
         # adjust data segment length 
         lenAdjust = (len(self.config.targetName) - len(self.KEY_TGTNAME))     \
                    * replCnt
         self.dataSegLen = hex(int(self.dataSegLen,16) + lenAdjust)[2:]
                           
         print("new dataseglen: %s" % self.dataSegLen)
         
         # adjust data length
         self.dataLen += lenAdjust

   def Serialize(self,testcase):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.Serialize
         ;
         ;   RESPONSIBILITY  Creates a list of two-char strings representing the 
         ;           PDU
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance 
         ;               testcase      I/O  The test case to use when serializing
         ;
         ;   RETURNS     nothing.
         ;
         ************************************************************************
         """ 
         # create the list to return to caller
         retlist = []
         # add the command and flags dword
         self.AppendDwordToList(retlist,self.dword1)
         retlist.append(int(self.ahsLen,16))
         # add the 3-byte data len
         dw = int(self.dataSegLen,16)
         retlist.append((dw & 0xFF0000) >> 16)
         retlist.append((dw & 0xFF00) >> 8)
         retlist.append((dw & 0xFF))
         # add the 8-byte lun
         # self.AppendQwordToList(retlist,self.lun)
         self.AppendLUNToList(testcase,retlist)
         #add the itt
         self.AppendTagOrValue(testcase,retlist,self.itt)
         # add dwords 20 through 44
         self.AppendTagOrValue(testcase,retlist,self.dw20)
         self.AppendTagOrValue(testcase,retlist,self.dw24)
         self.AppendTagOrValue(testcase,retlist,self.dw28)
         self.AppendTagOrValue(testcase,retlist,self.dw32)
         self.AppendTagOrValue(testcase,retlist,self.dw36)
         self.AppendTagOrValue(testcase,retlist,self.dw40)
         self.AppendTagOrValue(testcase,retlist,self.dw44)
         # add header digest
         if self.headerDigest != "0":
            if (self.headerDigest == self.KEY_DIGEST):
                self.headerDigest = self.ComputeHeaderDigest(retlist)
             
            self.AppendDwordToList(retlist,self.headerDigest)
            testcase.headerDigest = True
         else:
            testcase.headerDigest = False
            
         # add data, padding for 4 byte boundary
         padstr = ""
         if (self.dataLen != 0):
            print(self.data)
            for c in self.data:
               # print('\t', type(c), c)
               retlist.append(c)
            if self.dataLen % 4:
               padlen = (4 - self.dataLen % 4)

               for i in range(0,padlen):
                  retlist.append(0)
                  padstr += '\x00'
               self.dataLen += padlen
        
         # add data digest
         if self.dataDigest != "0":
            if self.dataLen != 0:
               if (self.dataDigest == self.KEY_DIGEST):
                   self.dataDigest = self.DwordToString(Crc32c(self.data + padstr))
               self.AppendDwordToList(retlist,self.dataDigest)
            testcase.dataDigest = True
         else:
            testcase.dataDigest = False

         return(retlist)         
  
   def DeSerialize(self,stream,testcase):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.DeSerialize
         ;
         ;   RESPONSIBILITY  Fills in the PDU 
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance
         ;               stream        I/O  String containing the read-in stream 
         ;               testcase       O  The test case may be altered
         ;
         ;   RETURNS     nothing
         ;
         ************************************************************************
         """ 
         
         # Before we start pulling from the stream, handle any recieve vars 
         # that might be pulled form the PDU.
         lst = []
         for i in range(IscsiComms.IscsiComms.ISCSI_BHS_SIZE):
             lst.append(stream[i])
         testcase.UpdateReceiveVars(lst)
               
         # pull the BHS from the stream
         offset = 0
         self.dword1 = "%x" % struct.unpack(">L",stream[offset:offset+4])[0]
         offset += 4 
         self.ahsLen = "%x" % stream[offset]
         offset += 1
         self.dataSegLen = self.GetThreeBytesFromString(stream,offset)
         offset += 3
         
         tupleof9 = struct.unpack(">Q8L",stream[offset:offset+40])
         self.lun = "%x" % tupleof9[0]
         self.itt = "%x" % tupleof9[1]
         self.dw20 = "%x" % tupleof9[2]
         self.dw24 = "%x" % tupleof9[3]
         self.dw28 = "%x" % tupleof9[4]
         self.dw32 = "%x" % tupleof9[5]
         self.dw36 = "%x" % tupleof9[6]
         self.dw40 = "%x" % tupleof9[7]
         self.dw44 = "%x" % tupleof9[8]
         offset += 40
        
         # read in header digest if testcase has one
         if testcase.headerDigest:
            self.headerDigest = "%x" % struct.unpack(">L",stream[offset:offset+4])[0]
            offset += 4
            
         # read in data segment
         self.data = []
         localdataseglen = int(self.dataSegLen,16)
         self.dataLen = localdataseglen
         stopcondition = localdataseglen
         if localdataseglen > len(stream):
            stopcondition = len(stream) 
         for i in range(offset,stopcondition+offset):
            self.data.append(stream[i])
         offset += stopcondition 
            
         #  discard pad
         if localdataseglen % 4 != 0:
            padlen = 4 - localdataseglen % 4
            offset += padlen
                        
         # read in data digest if necessary
         if testcase.dataDigest and self.dataLen != 0:
            self.dataDigest = "%x" % struct.unpack(">L",stream[offset:offset+4])[0] 
            offset += 4
            
  
   def ComputeHeaderDigest(self,hdrlist):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.ComputeHeaderDigest
         ;
         ;   RESPONSIBILITY  Compute the header digest of the current outgoing
         ;            (serialized) data
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance 
         ;
         ;   RETURNS     nothing
         ;
         ************************************************************************
         """  
         digest = 0
         hdrstring = string.join(("%c" % el for el in hdrlist),'')
         digest = Crc32c(hdrstring)
                 
         return  self.DwordToString(digest)
    
    
   def IncomingHeaderDigest(self,pdu):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.IncomingHeaderDigest
         ;
         ;   RESPONSIBILITY  Compute the header digest of a 'check' PDU
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I    The IscsiPdu class instance 
         ;               pdu           I    The PDU recieved on the link
         ;
         ;   RETURNS     the digest
         ;
         ************************************************************************
         """  
         # make a new pdu - assign fields across except for data
         temppdu = IscsiPdu()
         
         # elements in the PDU to work on
         keeplist = ("dword1","ahsLen","dataSegLen","lun",
                     "itt","dw20","dw24","dw28","dw32","dw36","dw40","dw44")
         
         # serialize 'self'
         hdrlist = []
         
         for el in self.__dict__:
             
             # only worry about our keep list
             if not el in keeplist:
                 continue
             
             # if the source is a key, substitute.
             if not ishexstring(self.__dict__[el]):
                temppdu.__dict__[el] = pdu.__dict__[el]
             else:
                temppdu.__dict__[el] = self.__dict__[el]
         
         
         # made the new pdu, now create a serialized header
         # add the command and flags dword
         self.AppendDwordToList(hdrlist,temppdu.dword1)
         hdrlist.append(int(temppdu.ahsLen,16))
         # add the 3-byte data len
         dw = int(temppdu.dataSegLen,16)
         hdrlist.append((dw & 0xFF0000) >> 16)
         hdrlist.append((dw & 0xFF00) >> 8)
         hdrlist.append((dw & 0xFF))
         # add the 8-byte lun
         self.AppendQwordToList(hdrlist,temppdu.lun)
         #add the itt
         self.AppendDwordToList(hdrlist,temppdu.itt)
         # add dwords 20 through 44
         self.AppendDwordToList(hdrlist,temppdu.dw20)
         self.AppendDwordToList(hdrlist,temppdu.dw24)
         self.AppendDwordToList(hdrlist,temppdu.dw28)
         self.AppendDwordToList(hdrlist,temppdu.dw32)
         self.AppendDwordToList(hdrlist,temppdu.dw36)
         self.AppendDwordToList(hdrlist,temppdu.dw40)
         self.AppendDwordToList(hdrlist,temppdu.dw44) 
          
         hdrdigest = self.ComputeHeaderDigest(hdrlist)
         
         return hdrdigest
   
   
   def IncomingDataDigest(self,pdu):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.IncomingDataDigest
         ;
         ;   RESPONSIBILITY  Compute the data digest of a 'check' PDU
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I    The IscsiPdu class instance 
         ;               pdu           I    The PDU recieved on the link
         ;
         ;   RETURNS     the digest
         ;
         ************************************************************************
         """  
         
         # if there's no data, data digest should be "0"
         if self.dataLen == 0:
            return("0")
                    
         # create a pad string
         padstring = ""
         if self.dataLen %4:
            for i in range(4 - self.dataLen % 4):
               padstring += '\x00'
        
         datadigest = self.DwordToString(Crc32c(self.data + padstring))
         return(datadigest)
             
  
   def AppendDwordToList(self,list,dword):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.AppendDwordToList
         ;
         ;   RESPONSIBILITY  Adds the dword to the list as 4 bytes
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance
         ;               list          O  The list to append
         ;               dword         I  The dword to add 
         ;
         ;   RETURNS     nothing.
         ;
         ************************************************************************
         """ 
         dword = int(dword,16)
         list.append(dword >> 24)
         list.append((dword & 0xFF0000) >> 16)
         list.append((dword & 0xFF00) >> 8)
         list.append((dword & 0xFF))
         
         
         
   def AppendQwordToList(self,list,qword):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.AppendQwordToList
         ;
         ;   RESPONSIBILITY  Adds the qword to the list as 8 bytes
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance
         ;               list          O  The list to append
         ;               dword         I  The qword to add 
         ;
         ;   RETURNS     nothing.
         ;
         ************************************************************************
         """ 
         qword = int(qword,16)
         list.append((qword & 0xFF00000000000000) >> 56)
         list.append((qword & 0xFF000000000000) >> 48)
         list.append((qword & 0xFF0000000000) >> 40)
         list.append((qword & 0xFF00000000) >> 32)
         list.append((qword & 0xFF000000) >> 24)
         list.append((qword & 0xFF0000) >> 16)
         list.append((qword & 0xFF00) >> 8)
         list.append((qword & 0xFF))
           
   def AppendLUNToList(self,testcase,list):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.AppendQwordToList
         ;
         ;   RESPONSIBILITY  Adds the qword to the list as 8 bytes
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance
         ;               testcase      I  The testcase to use
         ;               list          O  The list to append
         ;
         ;   RETURNS     nothing.
         ;
         ************************************************************************
         """ 
         qword = int(self.lun,16)

         if self.updateTsih != False:
            qword &= 0xFFFFFFFFFFFF0000
            qword |= testcase.tsih 

         list.append((qword & 0xFF00000000000000) >> 56)
         list.append((qword & 0xFF000000000000) >> 48)
         list.append((qword & 0xFF0000000000) >> 40)
         list.append((qword & 0xFF00000000) >> 32)
         list.append((qword & 0xFF000000) >> 24)
         list.append((qword & 0xFF0000) >> 16)
         list.append((qword & 0xFF00) >> 8)
         list.append((qword & 0xFF))
  
   def AppendTagOrValue(self,testcase,bytelist,dwfield):
         """
         ************************************************************************
         ;
         ;   FUNCTION        IscsiPdu.AppendTagOrValue
         ;
         ;   RESPONSIBILITY  
         ;
         ;   PARAMETERS  Name          I/O  Description                
         ;               self          I/O  The IscsiPdu class instance
         ;               bytelist      O    Gets 4 values appended to it
         ;               dwfield       I    The string field to translate.   
         ;
         ;   RETURNS     nothing.
         ;
         ************************************************************************
         """ 
         newlst = [0,0,0,0]
         
         if dwfield == self.KEY_CMDSN:
            newlst[0]= testcase.cmdSn >> 24
            newlst[1]= (testcase.cmdSn & 0xFF0000) >> 16
            newlst[2]= (testcase.cmdSn & 0xFF00) >> 8
            newlst[3]= (testcase.cmdSn & 0xFF)
         elif dwfield == self.KEY_EXPSTSN:
            newlst[0]= testcase.expStatSn >> 24
            newlst[1]= (testcase.expStatSn & 0xFF0000) >> 16
            newlst[2]= (testcase.expStatSn & 0xFF00) >> 8
            newlst[3]= (testcase.expStatSn & 0xFF)
         elif dwfield == self.KEY_ITT:
            itt = testcase.GetIttToSend()
            newlst[0]= itt >> 24
            newlst[1]= (itt & 0xFF0000) >> 16
            newlst[2]= (itt & 0xFF00) >> 8
            newlst[3]= (itt & 0xFF)
         elif dwfield == self.KEY_TTT:
            ttt = testcase.GetTttToSend()
            newlst[0]= ttt >> 24
            newlst[1]= (ttt & 0xFF0000) >> 16
            newlst[2]= (ttt & 0xFF00) >> 8
            newlst[3]= (ttt & 0xFF)
         elif dwfield == "TSIH":
            newlst[0]= testcase.tsih >> 24
            newlst[1]= (testcase.tsih & 0xFF0000) >> 16
            newlst[2]= (testcase.tsih & 0xFF00) >> 8
            newlst[3]= (testcase.tsih & 0xFF)
         else:
            # translate the numerical value 
            try:
               dw = int(dwfield,16)
            except:
               print("WARNING: Invalid field in file %s" % (self.name), end=' ')
               print("- expected and integer, got %s" %  (dwfield))
               dw = 0xFFFFFFFF
               
            newlst[0]= dw >> 24
            newlst[1]= (dw & 0xFF0000) >> 16
            newlst[2]= (dw & 0xFF00) >> 8
            newlst[3]= (dw & 0xFF)
         
         bytelist.extend(newlst)

   def GetDwordFromList(self,serial):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetDwordFromList
      ;
      ;   RESPONSIBILITY  returns a dword from a serial stream   
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               serial        I  The SERIALIZED PDU to pull the dword
      ;
      ;   RETURNS     dword
      ;
      ************************************************************************
      """
      dw = (serial[0] << 24) + (serial[1] << 16) + (serial[2] << 8) + serial[3]
      #remove the dword from the front of the list
      for i in range(4):
         serial.pop(0)
      return "%x" % dw
      
   def GetThreeBytesFromList(self,serial):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetThreeBytesFomList
      ;
      ;   RESPONSIBILITY  returns a 3-byte integer from a serial stream   
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               serial        I  The SERIALIZED PDU to pull the dword
      ;
      ;   RETURNS     dword
      ;
      ************************************************************************
      """
      dw = (serial[0] << 16) + (serial[1] << 8) + serial[2]
      #remove the dword from the front of the list
      for i in range(3):
         serial.pop(0)
      return "%x" % dw
    
   def GetQwordFromList(self,serial):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetQwordFromList
      ;
      ;   RESPONSIBILITY  returns a 8-byte integer from a serial stream   
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               serial        I  The SERIALIZED PDU to pull the dword
      ;
      ;   RETURNS     qword
      ;
      ************************************************************************
      """
      qw = serial.pop(0) << 56
      qw += serial.pop(0) << 48
      qw += serial.pop(0) << 40
      qw += serial.pop(0) << 32
      qw += serial.pop(0) << 24
      qw += serial.pop(0) << 16
      qw += serial.pop(0) << 8
      qw += serial.pop(0) 
        
      return "%x" % qw



   def GetThreeBytesFromString(self,serial,offset):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetThreeBytesFromString
      ;
      ;   RESPONSIBILITY  returns a 3-byte integer from a serial stream 
      ;            Used cuz I can't figure out how to get struct to do it.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               serial        I    The string containing the 3 bytes
      ;               offset        I     Offset into the string  
      ;   RETURNS     dword
      ;
      ************************************************************************
      """
      dw = (serial[offset+0] << 16) + \
           (serial[offset+1] << 8) + \
           (serial[offset +2])

      return "%x" % dw
    

   def DwordToString(self,dw):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.DwordToSTring
      ;
      ;   RESPONSIBILITY  Converts a dword (unsigned long hex value)
      ;                to a string useable by other conversion functions.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiPdu class instance  
      ;               dw            I    The dword to convert
      ;
      ;   RETURNS     string
      ;
      ************************************************************************
      """       
      return hex(dw).split('x')[1].rstrip('L')
      
      
   def IsEqual(self,pdu,testcase,logfile):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.IsEqual
      ;
      ;   RESPONSIBILITY  checks to see if pdus are equal
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiPdu class instance  
      ;               pdu           I    The pdu read from the comms object
      ;               testcase      I    The current test case (used in 
      ;                                   the compare)
      ;
      ;   RETURNS     boolean
      ;
      ************************************************************************
      """ 
      # okay, so there's a cool python way to iterate through the objects
      # and  __dict__ seems to be a good start
      
      # elements in the pdu to ignore
      ignorelist = \
      ("name","dataLen","compareData","ahsLen","config","ignoreCmdSn",
       "updateTsih","compareTsih")
      
      for el in self.__dict__:
         valsrc = self.__dict__[el]
         valdst = pdu.__dict__[el]
             
         # check for dontcares    
         if el in ignorelist:
            continue               

         if valsrc == self.KEY_DONTCARE:
            continue
        
         # handle header digests.  We may need to compute the digest 
         # of the source pdu
         if el == "headerDigest" and valsrc == self.KEY_DIGEST:
            valsrc = self.IncomingHeaderDigest(pdu)
            
         # handle data digests.  We may need to compute the digest of 
         # the source pdu
         if el == "dataDigest" and valsrc == self.KEY_DIGEST:
            valsrc = self.IncomingDataDigest(pdu)
         
         # check the fields
         
         # the data field is a special comparison
         if el == "data":
           if self.compareData:
               datacompared = True
               minlen = min(len(self.data),len(pdu.data))
               for i in range(minlen):
                  if ord(self.data[i]) != pdu.data[i]:
                     logfile.write("Data did not compare at offset %d"%i)
                     logfile.write(" exp : %x got %x\r\n"%              \
                                    (ord(self.data[i]), pdu.data[i]))
                     datacompared = False
               if not datacompared:     
                  return False

           else: 
               continue
         elif (el == "lun") and (not self.compareTsih):
            logfile.write("Not caring about TSIH in lun field\r\n")
            #use the test case to do a special field substitution 
            cmpa = int(testcase.FieldSubst(valsrc,pdu.itt),16)
            # pdu does not need a field subst - it was read from host
            cmpb = int(valdst,16)
            #Compare the lun field with don't cares set up for tsih
            cmpa = cmpa & 0xffffffffffff0000
            cmpb = cmpb & 0xffffffffffff0000
            if cmpa != cmpb:
               logfile.write("Field %s did not compare: " % el)
               logfile.write(" expected %s got %s \r\n" % \
                      (testcase.FieldSubst(valsrc,pdu.itt),valdst))
               return False
         else:                    
            #use the test case to do a special field substitution 
            cmpa = int(testcase.FieldSubst(valsrc,pdu.itt),16)
            # pdu does not need a field subst - it was read from host
            cmpb = int(valdst,16)
            if cmpa != cmpb:
               logfile.write("Field %s did not compare: " % el)
               logfile.write(" expected %s got %s \r\n" % \
                      (testcase.FieldSubst(valsrc,pdu.itt),valdst))
               return False
          
      # if we got here, out of the loop, the compare worked
      return True
       
                           
     
