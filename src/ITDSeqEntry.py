"""
********************************************************************************
;
;   MODULE       ITDSeqEntry.py       
;
;   DESCRIPTION  Source file for the iscsi test tool sequence entry container.
;    
;        a sequence entry contains a list of pdu's with associated 
;        id number, plus it's associated Itt, ttt & lun, along twith the
;        sequence id.
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
import ITDSeqPDU as PDU
import IscsiPDU as iPDU

class ITDSeqEntry:
          
   def __init__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqEntry.__init__
      ;
      ;   RESPONSIBILITY  Iscsi Sequence Entry initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence entry class instance to
      ;                                  initialize
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      
      # A Sequence entry consists of a seqpdu, an itt, a TTT, a Lun and A CmdSeq
      # A seq pdu consists of a pdu, a rx flag, and an id
      self.seq = []
      self.itt = iPDU.IscsiPdu.BAD_ITT
      self.ttt = 0
      self.lun = 0
      self.id = 0
      

   def __del__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.__del__
      ;
      ;   RESPONSIBILITY  Iscsi sequence list class destructor
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence entry class instance 
      ;                                to destruct
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """ 
      
   def AddPdu(self,pdu,id):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.AddPdu
      ;
      ;   RESPONSIBILITY  Add a PDU to the current sequence entry
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list cllass instance 
      ;                                to update
      ;               pdu           I    The ISCSIPDU to add
      ;               id            I    The id to go along with it
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """ 
      pdu = PDU.ITDSeqPDU(pdu,id)
      self.seq.append(pdu)
      
   def GetPDU(self,id):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.GetSeqPDU
      ;
      ;   RESPONSIBILITY  Get the seqPDU indexed by 'id' from the list
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list cllass instance 
      ;                                to destruct
      ;
      ;   RETURNS     pdu or none
      ;
      ************************************************************************
      """ 
      for pdu in self.seq:
          if pdu.id == id:
              return pdu.pdu
    
      return None,False
          
   def Print(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqEntry.Print
      ;
      ;   RESPONSIBILITY    Print out this sequence entry
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence entry class instance 
      ;
      ;   RETURNS     nothing
      ;
      ************************************************************************
      """ 
      print("**************** SeqEntry ************")
      print("id : %d  itt : %d ttt : %d  lun : %d" % (self.id,self.itt,
                                                      self.ttt,self.lun))
      for pdu in self.seq:
          pdu.Print()