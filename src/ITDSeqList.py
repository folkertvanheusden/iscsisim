"""
********************************************************************************
;
;   MODULE       ITDSeqList.py       
;
;   DESCRIPTION  Source file for the iscsi test tool sequence list class
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
import ITDSeqEntry as ENTRY 
import copy

class ITDSeqList:
          
   def __init__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.__init__
      ;
      ;   RESPONSIBILITY  Iscsi Sequence list initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list class instance to
      ;                                  initialize
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      
      # A Sequence entry consists of a seqpdu, an itt, a TTT, a Lun and A CmdSeq
      # A seq pdu consists of a pdu, a rx flag, an id
      self.seq = []
      

   def __del__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.__del__
      ;
      ;   RESPONSIBILITY  Iscsi sequence list class destructor
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list cllass instance 
      ;                                to destruct
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """ 
      
   def PushEntry(self,id):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.PushEntry
      ;
      ;   RESPONSIBILITY  Pushes a new entry onto the sequence list.  The
      ;        Entry will be created with no pdus in the pdu list, and all
      ;        other values defaulted
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list class instance
      ;               id            I    Id of the new sequence entry
      ;
      ;   RETURNS     handle to the entry
      ;
      ************************************************************************
      """ 
      entry = ENTRY.ITDSeqEntry()
      entry.id = id
      self.seq.append(entry)
      return len(self.seq)-1
  
   def PushCopy(self,entry):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.PushCopy
      ;
      ;   RESPONSIBILITY  Pushes a copy of the given entrynew entry onto the 
      ;        sequence list.  A shallow copy will be used, since PDU's should
      ;        be passable by reference.
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list class instance
      ;               id            I    Id of the new sequence entry
      ;
      ;   RETURNS     handle to the entry
      ;
      ************************************************************************
      """ 
      entry = copy.copy(entry)
      self.seq.append(entry)
      return len(self.seq)-1
      
   def RemoveEntry(self,handle):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.REmoveEntry
      ;
      ;   RESPONSIBILITY  Removes the entry associated with handle
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence list class instance 
      ;               handle        I    handle of entry to remove
      ;
      ;   RETURNS     
      ;
      ************************************************************************
      """ 
      
      del self.seq[handle]
      
   def FindEntryItt(self,itt):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.FindEntryItt
      ;
      ;   RESPONSIBILITY  finds the entry based on itt
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence list class instance 
      ;               itt           I  The itt to look for 
      ;
      ;   RETURNS    index of the entry or none 
      ;
      ************************************************************************
      """ 
      for entry in self.seq:
          if entry.itt == int(itt,16):
              return self.seq.index(entry)
      return None
  
   def FindEntryId(self,id):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.FindEntryId
      ;
      ;   RESPONSIBILITY  finds the entry based on id
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence list class instance 
      ;               id            I  The id to look for 
      ;
      ;   RETURNS     handle to the entry or none
      ;
      ************************************************************************
      """ 
      for entry in self.seq:
          if entry.id == id:
              return self.seq.index(entry)
    
      return None
  
   def GetPduFromListElement(self,le):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.GetPduFromListElement
      ;
      ;   RESPONSIBILITY  finds the entry based on list element
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence list class instance 
      ;               le            I  a tuple desribing the id and pdu id
      ;
      ;   RETURNS     pdu or none
      ;
      ************************************************************************
      """ 
      pdu = None
      for entry in self.seq:
          if entry.id == le[0]:
              pdu = entry.GetPDU(le[1])
              
      return pdu
  
   def GetListElement(self,le):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.GetListElement
      ;
      ;   RESPONSIBILITY  finds the entry based on list element index
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence list class instance 
      ;               le            I  the Id to look for
      ;
      ;   RETURNS     entry specified
      ;
      ************************************************************************
      """ 
      for entry in self.seq:
          if entry.id == le:
              return entry
              
      return None
  
   def AddPdu(self,handle,pdu,id):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.AddPdu
      ;
      ;   RESPONSIBILITY  Add pdu to this sequence list
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence list class instance 
      ;               handle        I  handle of the current seqentry
      ;               pdu           I  IscsiPDU to load up
      ;               id            I   Id for the new pdu
      ;
      ;   RETURNS     handle to the entry or none
      ;
      ************************************************************************
      """ 
      self.seq[handle].AddPdu(pdu,id)
         
   def Print(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.Print
      ;
      ;   RESPONSIBILITY    Print out this sequence list
      ;        
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I  The sequence list class instance 
      ;
      ;   RETURNS     nothing
      ;
      ************************************************************************
      """ 
      for seqentry in self.seq:
          seqentry.Print()