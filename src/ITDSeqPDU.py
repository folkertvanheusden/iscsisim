"""
********************************************************************************
;
;   MODULE       ITDSeqPdu.py       
;
;   DESCRIPTION  Source file for the iscsi test tool sequence pdu container.
;    
;        a sequence pdu contains a pdu with its associated Rx Flag and id
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
********************************************************************************
"""

# import section
import IscsiPDU as iPDU

class ITDSeqPDU:
          
   def __init__(self,pdu,id):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqEntry.__init__
      ;
      ;   RESPONSIBILITY  Iscsi Sequence Entry initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence pdu class instance to
      ;                                  initialize
      ;               pdu           I    The PDU to be wrapped
      ;               id            I    The id of the pdu from the ITD file
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      
      # A Sequence entry consists of a seqpdu, an itt, a TTT, a Lun and A CmdSeq
      # A seq pdu consists of a pdu, a rx flag, and an id
      self.pdu = pdu
      self.id = id

   def __del__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.__del__
      ;
      ;   RESPONSIBILITY  Iscsi sequence pdu class destructor
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence pdu class instance 
      ;                                to destruct
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """ 
      
   def Print(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        ITDSeqList.print
      ;
      ;   RESPONSIBILITY  Iscsi sequence pdu print method
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The sequence pdu class instance 
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """ 
      self.pdu.Print()
