"""
********************************************************************************
;
;   MODULE       IscsiTestCase.py       
;
;   DESCRIPTION  Source file for the iscsi test case helper class used in the 
;        iscsi test tool
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
import IscsiPDU as PDU


class IscsiTestCase:
    
   def __init__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiTestCase.__init__
      ;
      ;   RESPONSIBILITY  IscsiTest Case class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance to 
      ;                                 initialize
      ;         
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # initialize the variables
      self.cmdSn = 1
      self.ignoreCmdSn = False
      self.expStatSn = 0
      self.itt = 0x1000face
      self.tsih = 0
      self.headerDigest = False
      self.dataDigest = False
      self.seqList = None
      self.activeHandle = None
      
   def LoadSeqList(self,seqlist):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiTestCase.LoadSeqList
      ;
      ;   RESPONSIBILITY  Load up the sequence list for this test case.  This
      ;        is done after init time because a new seqlist is loaded for
      ;        every new ITD that's loaded.  The seq list stores copies of 
      ;        itt & tt for a given test descriptor, and is held as a reference
      ;        to the current itd.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance 
      ;               seqList       I    The seqList to store
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      self.seqList = seqlist 
       
       
   def UpdateSendVars(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.UpdateSendVars
      ;
      ;   RESPONSIBILITY  Update variables on transmission of a PDU.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I/O  The SERIALIZED PDU to check for update        
      ;         
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      
      #  Update CmdSn, if necessary
      if self.ignoreCmdSn:
          self.ignoreCmdSn = False   # clear it for next time
      else:
          ret = self.GetCmdSn(pdu)
          if ret[0] :
             self.cmdSn = ret[1] + 1
                       
      #  Update itt, if necessary
      ret = self.GetItt(pdu)

      if ret[0] :
         self.seqList.seq[self.activeHandle].itt = ret[1]


   def UpdateReceiveVars(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.UpdateReceiveVars
      ;
      ;   RESPONSIBILITY  Update variables on reception of a PDU.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I/O  The SERIALIZED PDU to check for update        
      ;         
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
          
      #  Update expStatSn, if necessary
      ret = self.GetStatSn(pdu) 
      if ret[0]:
         self.expStatSn = ret[1] + 1
      
      #  Update ttt, if necessary
      ret = self.GetTtt(pdu)
      if ret[0]:
         itt = "%x" % self.GetItt(pdu)[1]
         self.seqList.seq[self.seqList.FindEntryItt(itt)].ttt = ret[1]
             
      #  Update tsih, if necessary
      ret = self.GetTsih(pdu)
      if ret[0]:
         self.tsih = ret[1]
         
   def GetCmdSn(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetCmdSn
      ;
      ;   RESPONSIBILITY  returns cmdsn from a serialize stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I The SERIALIZED PDU to check for update        
      ;         
      ;
      ;   RETURNS     tuple [0] : True if cmdsn found, False otherwise
      ;                     [1] : the integer value of cmdsn
      ;        SPECIAL CASE - - returns False if command is immediate (don't
      ;        update cmdsn)
      ;
      ************************************************************************
      """

      # command and immediate bits are in 1st byte of serial stream
      cmdByte = pdu[0]
      # commands which carry a command sn are: ScsiCommand (01) ,TaskMgmt (02)
      # Text Req(04),LoginReq(03), LogoutReq(06), NOPOut(00)  
      cmdSnSearchList = [0x00,0x01,0x02,0x03,0x04,0x06]  
      
      # check for immediate
      if (cmdByte & 0x40):
         return (False,0)
      
      # check for in the list
      if (cmdByte & 0x3F) not in cmdSnSearchList:
         return (False,0)
         
      # make sure the CMD_SN field was not detected
               
         
      # pull the cmd sn. That's at bytes 24-27 in the serialized pdu
      cmdsn = self.SerialToDword(pdu[24:28])
      
      return (True,cmdsn)
      
   def GetItt(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetItt
      ;
      ;   RESPONSIBILITY  returns itt from a serialize stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I The SERIALIZED PDU to check for update 
      ;         
      ;
      ;   RETURNS     tuple [0]: True if itt found, False otherwise
      ;                    [1]: the itt found
      ;        special note, data out returns False, cuz even though it has 
      ;        an itt, the itt is per task - doesn't get incremented by data
      ;        an itt of 0xffffffff returns False - reserved value doesn;t
      ;        cause an incremnet
      ;
      ************************************************************************
      """

      # command is in 1st byte of serial stream
      cmdByte = pdu[0]

      
      # commands which carry an itt are: ScsiCommand (01) ,TaskMgmt (02)
      # Text Req(04),LoginReq(03), LogoutReq(06), NOPOut(00), R2T (31) 
      ittSearchList = [0x00,0x01,0x02,0x03,0x04,0x06,0x31] 
      
      # check for in the list
      if (cmdByte & 0x3F) not in ittSearchList:
         return (False,0)
      
      # pull the itt. That's at bytes 16-19 in the serialized pdu
      itt = self.SerialToDword(pdu[16:20])
      if itt == 0xffffffff:
         return (False,0)
         
      return (True,itt)     
             
   def GetStatSn(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetStatSn
      ;
      ;   RESPONSIBILITY  returns STatSn from a serialize stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I The SERIALIZED PDU to check for update 
      ;         
      ;
      ;   RETURNS     tuple [0]:  True if statsn found, False otherwise
      ;                     [1]: the stat sn read
      ************************************************************************
      """

      # command is in 1st byte of serial stream
      cmdByte = pdu[0] & 0x3F
      
      # commands which carry a statsn are: ScsiRsp(21),TmRsp(22), DataIn(25)
      # R2T(31) [don't increment], Async(32), TextRsp(24), 
      # LoginRsp(23) [only if status class is 0], LogoutRsp(26) 
      searchList = [0x21,0x22,0x23,0x24,0x25,0x26,0x31,0x32]  
      
      # check for in the list
      if cmdByte not in searchList:
         return (False,0)
         
      # special Case, login rsp, datain with no status 
      if cmdByte == 0x23:
         statusclass = pdu[36]
         if statusclass != 0:
            return (False,0)
      
      if cmdByte == 0x25:
         sbit = pdu[1] & 0x01
         if sbit == 0:
            return (False,0)   
                                            
      # pull the statsn. That's at bytes 24-27 in the serialized pdu
      statsn = self.SerialToDword(pdu[24:28])
      if statsn == 0xffffffff:
         return (False,0)
         
      # special case, if r2t, don't increment statsn 
      if cmdByte == 0x31:
         statsn -= 1
      
      return (True,statsn)     
   
   def GetTtt(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetTtt
      ;
      ;   RESPONSIBILITY  returns ttt from a serialize stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I The SERIALIZED PDU to check for update 
      ;
      ;   RETURNS    tuple [0]:  True if ttt found, False otherwise
      ;                    [1]:  The TTT read
      ************************************************************************
      """
      # command is in 1st byte of serial stream
      cmdByte = pdu[0] & 0x3F
      
      # commands which carry a ttt are: Datain(25),R2T(31),TextRsp(24)
      searchList = (0x25,0x24,0x31)
      
      # check for in the list
      if cmdByte not in searchList:
         return (False,0)
         
      # pull the ttt. That's at bytes 20-23 in the serialized pdu
      ttt = self.SerialToDword(pdu[20:24])
      # ignore special value of ttt
      if ttt == 0xffffffff:
         return (False,0)
      
      return (True,ttt)      
   

   def GetTsih(self,pdu):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetTsih
      ;
      ;   RESPONSIBILITY  returns tsih from a serialize stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               pdu           I The SERIALIZED PDU to check for update 
      ;               tsih           O filled in with the tsih read       
      ;         
      ;
      ;   RETURNS    tuple [0]:  True if tsih found, False otherwise
      ;                    [1]:  The tsih read
      ************************************************************************
      """
      # command is in 1st byte of serial stream
      cmdByte = pdu[0] & 0x3F
      
      # commands which carry a tsih are: LoginRsp(23)
      # tsih is carried on send, but we don't care so much about that
      searchList = (0x23)
      
      # check for in the list
      if cmdByte != searchList:
         return (False,0)
         
      # pull the tsih. That's at byte 14-15 in the serialized pdu
      tsih = (pdu[14] << 8) + pdu[15]
      
      return (True,tsih)      
   
      
   def SerialToDword(self,serial):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.SerialToDword
      ;
      ;   RESPONSIBILITY  returns a dword form of the serial stream
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               serial        I  The SERIALIZED PDU to check for update        
      ;         
      ;
      ;   RETURNS     dword
      ;
      ************************************************************************
      """
      dw = (serial[0] << 24) + (serial[1] << 16) + (serial[2] << 8) + serial[3]
      return dw
      
   def FieldSubst(self,field,itt):  
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.FieldSubst
      ;
      ;   RESPONSIBILITY  either returns the field as-is, or returns the 
      ;           field substitution for the field.  This is used for 
      ;           COMPARISON OF PDU's NOT FOR CREATING OUTPUT PDU's!
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;               field         I    The field to subsitute
      ;               itt           I    The itt of the pdu to compare to.
      ;
      ;   RETURNS     the proper type of field value
      ;
      ************************************************************************
      """    
      # I know I could associate a dictionary here, but I've done too much 
      # thinking already today... just be stupid about it for now.
      
      if field == PDU.IscsiPdu.KEY_CMDSN:
         return "%x" % self.cmdSn
      
      if field == PDU.IscsiPdu.KEY_EXPSTSN:
         return "%x" % self.expStatSn

      # in the case of the itt, if this command doensn't have one yet, use
      # the next in the sequence of ITT's.
      # Otherwise give it the ITT from its seqlist.
      if field == PDU.IscsiPdu.KEY_ITT:
         entry = self.seqList.FindEntryItt(itt)
         if entry != None:
             return itt
         else:
             return "%x" % PDU.IscsiPdu.BAD_ITT
         
      # for the ttt, if this command doesn't have one yet (it's the first R2T)
      # just return all f's.
      if field == PDU.IscsiPdu.KEY_TTT:
         entry = self.seqList.FindEntryItt(itt)
         if entry:
             return "%x" % self.seqList.seq[entry].ttt
         else:
             return "%x" % 0xFFFFFFFF
       
      if field == PDU.IscsiPdu.KEY_TSIH:
         return "%x" % self.tsih

      return "%s" % field      
  
   def GetIttToSend(self):  
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetIttToSend
      ;
      ;   RESPONSIBILITY  Get the itt to send with the current active PDU.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;
      ;   RETURNS     the itt
      ;
      ************************************************************************
      """    

      # If this command doensn't have one yet, use the next in the sequence of 
      # ITT's. Otherwise give it the ITT from it's seqlist.
      if self.seqList.seq[self.activeHandle].itt == PDU.IscsiPdu.BAD_ITT:
             self.seqList.seq[self.activeHandle].itt = self.itt
      
      return self.seqList.seq[self.activeHandle].itt       
         
   def GetTttToSend(self):  
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiPdu.GetTttToSend
      ;
      ;   RESPONSIBILITY  Get the ttt to send with the current active PDU.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiTestCase class instance  
      ;
      ;   RETURNS     the ttt
      ;
      ************************************************************************
      """    
      return self.seqList.seq[self.activeHandle].ttt       
