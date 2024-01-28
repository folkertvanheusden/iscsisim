#! /usr/bin/python3

"""
********************************************************************************
;
;   MODULE      iSCSISim.py      
;
;   DESCRIPTION  Source file for iSCSI Test tool
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

"""
********************************************************************************
;   iSCSISim Version 0.80 BETA
;   5-May-2018
********************************************************************************
"""

# import section

import time
import wx  
import TestToolFrame as TT       

class iSCSISim(wx.App):
   VERSION = "0.80 beta"
   """
   ****************************************************************************
   ;
   ;   FUNCTION      iSCSISim.MainLoop
   ;
   ;   RESPONSIBILITY  Main function for iscsi test tool
   ;
   ;   PARAMETERS  Name        I/O  Description            
   ;            argv        I   List of arguments (no args for now)
   ;
   ;   RETURNS    Nothing
   ;
   ****************************************************************************
   """
   def MainLoopbla(self):

      # Create an event loop and make it active.  If you are
      # only going to temporarily have a nested event loop then
      # you should get a reference to the old one and set it as
      # the active event loop when you are done with this one...
      evtloop = wx.EventLoop()
      old = wx.EventLoop.GetActive()
      wx.EventLoop.SetActive(evtloop)

      # This outer loop determines when to exit the application,
      # for this example we let the main frame reset this flag
      # when it closes.
      while self.keepGoing:
         # At this point in the outer loop you could do
         # whatever you implemented your own MainLoop for.  It
         # should be quick and non-blocking, otherwise your GUI
         # will freeze.  

         # This inner loop will process any GUI events
         # until there are no more waiting.
         while evtloop.Pending():
            evtloop.Dispatch()

         # Send idle events to idle handlers.  You may want to
         # throttle this back a bit somehow so there is not too
         # much CPU time spent in the idle handlers.  For this
         # example, I'll just snooze a little...
         time.sleep(0.10)
         self.ProcessIdle()
         # update any display counters, etc
         if self.frame:
            self.frame.UpdateControls()

      wx.EventLoop.SetActive(old)


   def OnInit(self):
      self.frame = TT.TestToolFrame(None ,self, -1, "iSCSISim", self.VERSION)
      self.frame.Show(True)
      self.SetTopWindow(self.frame)

      self.keepGoing = True
      return True


def main(argv):
   """
   ****************************************************************************
   ;
   ;   FUNCTION      main
   ;
   ;   RESPONSIBILITY  Main function
   ;
   ;   PARAMETERS  Name        I/O  Description            
   ;            argv        I   List of arguments
   ;
   ;   RETURNS    Nothing
   ;
   ****************************************************************************
   """
   # Create an instance of the iSCSISim application class
   app = iSCSISim(False)
   app.MainLoop()


# Boilerplate to call main
if __name__ == '__main__':
   import sys
   main(sys.argv)






