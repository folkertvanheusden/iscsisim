"""
********************************************************************************
;
;   MODULE      TestToolFrame.py      
;
;   DESCRIPTION  Source file to provide gui port functions to iscsi tester
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

import time
import wx        
import os
import IscsiITS as ITS
import IscsiPDU as PDU
import IscsiITD as ITD
import IscsiTestCase as ITC 
import IscsiCfg as ICFG
import IscsiComms as ISOT
import threading
import sys


class TestToolFrame(wx.Frame):
      
   """
   ****************************************************************************
   ;
   ;   FUNCTION      TestToolFrame.__init__
   ;
   ;   RESPONSIBILITY  initialize for iscsi test tool frame
   ;
   ;   PARAMETERS  Name      I/O  Description         
   ;              parent     I    parent window (probably NONE)
   ;              id         I    used in frame init
   ;              title      I    title of the Frame to create
   ;              app        I    the app calling this frame
   ;                                   (has a keepGoing flag)
   ;              vers       I    version of code executing (for about box)
   ;
   ;   RETURNS   Nothing
   ;
   ****************************************************************************
   """   
   def __init__(self, parent,app, id, title, vers):
      wx.Frame.__init__(self, parent, id, title,
                             (100, 100), (600, 280))
            
      # Create the menubar and a menu  : make this prior to making the panel
      menuBar = wx.MenuBar()
      menu = wx.Menu()
   
      # add an item to the menu, using \tKeyName automatically
      # creates an accelerator, the third param is some help text
      # that will show up in the statusbar
      menu.Append(wx.ID_OPEN, "O&pen\tAlt-O", "Open a test suite")
      menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit")
   
      # and put the menu on the menubar
      menuBar.Append(menu, "&File")
      
      # create the help menu (for copyright information)
      menu = wx.Menu()
      menu.Append(wx.ID_ABOUT, "About iSCSISim", "Shows Copyright info")
      menuBar.Append(menu, "&Help")
      menuBar.SetBackgroundColour((203,203,203,255))      
      self.SetMenuBar(menuBar)
   
      # bind the events to their handlers
      self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
      self.Bind(wx.EVT_IDLE, self.OnIdle)
      self.Bind(wx.EVT_MENU, self.OnCloseWindow, id=wx.ID_EXIT)
      self.Bind(wx.EVT_MENU, self.OnOpenFile, id=wx.ID_OPEN) 
      self.Bind(wx.EVT_MENU, self.OnHelpAbout, id=wx.ID_ABOUT)

      # init some local variables
      self.app = app
      self.testCase = ITC.IscsiTestCase()
      self.testSuite = ITS.IscsiIts()
      self.version = vers
      
      # create the configuration object
      self.config = ICFG.IscsiCfg()
      
      # initialize the panel
      panel = wx.Panel(self)
      sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
      
      # create the relevant controls
      self.testSuiteCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY, 
                                       size = (400,20))
      sizer.Add(wx.StaticText(panel, -1, "Test Suite:"))
      sizer.Add(self.testSuiteCtrl)

      # ************* Iteration Count Control *************
      self.iterationCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)
      sizer.Add(wx.StaticText(panel, -1, "Iteration:"))
      sizer.Add(self.iterationCtrl)
      # iteration count is store in the test suite class
      
      # ************* Failure Count Control ***************
      self.failureCountCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)
      sizer.Add(wx.StaticText(panel, -1, "Failure Count:"))
      sizer.Add(self.failureCountCtrl)
      self.failureCount = 0
      
      # ************* Current Test Running Control ********
      self.currentTestCtrl = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY,
                                       size = (400,20))
      sizer.Add(wx.StaticText(panel, -1, "Current Test Running:"))
      sizer.Add(self.currentTestCtrl)
      self.currentTestRunning = ITD.IscsiItd()
      self.testCase.LoadSeqList(self.currentTestRunning.activeSeqList)
      
      # ************ test stop start button ***************
      self.startStopButton  = wx.Button(panel, -1, "Start", (140,150))
      # sizer.Add(self.startStopButton)
      self.Bind(wx.EVT_BUTTON, self.OnStartStopTest, self.startStopButton)
      self.testState = "Stopped"
      
      
      # ************ Create the program Exit button ***************
      self.ExitButton  = wx.Button(panel, -1, "Exit", (380,150) )
      # sizer.Add(self.ExitButton)
      self.Bind(wx.EVT_BUTTON, self.OnExitButton, self.ExitButton)     
      self.exiting = False

      # put a line in 
      self.whiteLine = wx.StaticLine(panel, -1, (0,190), (600,3))
      self.whiteLine.SetBackgroundColour((249,249,249,255))
      self.whiteLine.SetForegroundColour((249,249,249,255))
      
      # ************ Add the logo ************************
      logo = wx.Image("pb_atto.gif", wx.BITMAP_TYPE_GIF).ConvertToBitmap()
      wx.StaticBitmap(panel, -1, logo, (265, 200), (logo.GetWidth(), logo.GetHeight()))
      
      
      border = wx.BoxSizer()
      border.Add(sizer, 0, wx.ALL, 20)
      panel.SetSizer(border)
      
      # Set up a list of idle target connections
      self.idleConnList = []
      
      #initialize the test suite
      suiteFilename = self.config.GetSuiteFilename()
      
      if (len(suiteFilename) > 0):
         try:
             os.chdir(os.path.split(suiteFilename)[0])
         except:
             self.config.ClearSuiteName()
             suiteFilename = ''
             
      if (len(suiteFilename) > 0) and (os.path.isfile(suiteFilename)):    
         fileOpened = self.testSuite.LoadFromXMLFile(
                            os.path.split(suiteFilename)[1],self.config.logFile)
      
   def RunTests(self):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.RunTests
      ;
      ;   RESPONSIBILITY  Wrapper for run tests thread
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """     
      
      # send start to kick off the tests
      # if Open returns non-zero start failed, so exit
      # NOTE:  sys.exit will not kill all threads (not sure why), so the
      # frame window still needs to be closed
      print("Sending start command...")
      if self.currentComms.Open(self.testCase) != ISOT.OUT_START_PASS:
         sys.exit()

      # comms opened ok, so start the thread.
      self.currentComms.start()

      #loop, stepping tests as necessary
      while self.testSuite.loaded and self.testState == "Started":
         self.StepCurrentTest()
         
      self.currentComms.Kill()
               
      # broke out of loop, stop the tests
      self.testState = "Stopped"
      self.startStopButton.SetLabel("Start")
      
      if self.exiting:
          self.Destroy()
      
   def UpdateControls(self):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.UpdateControls
      ;
      ;   RESPONSIBILITY  Update the controls fields after each iteration 
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      # there's an iteration count - update it
      self.iterationCtrl.SetValue(str(self.testSuite.GetIteration()))
      # update the current test running
      if self.testState == "Started":
         self.currentTestCtrl.SetValue(self.currentTestRunning.name)
      # update the failure count 
      self.failureCountCtrl.SetValue(str(self.failureCount))
      #update the test suite 
      self.testSuiteCtrl.SetValue(self.testSuite.fileName)
      
      
   def StepCurrentTest(self):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.StepCurrentTest
      ;
      ;   RESPONSIBILITY Runs the next step in the current test
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      
      # Did the last test finish?  if so, get the next test 
      print("Stepping test")
      if self.currentTestRunning.TestDone():
         if self.currentTestRunning.name:
            print("Test %s is Done" % self.currentTestRunning.name)
         else:
            print("Finished testing initial setup")
         self.config.logFile.write("Test %s complete\r\n" % self.currentTestRunning.name)
         # recreate the test running instance for safety's sake
         self.currentTestRunning = ITD.IscsiItd()
         self.testCase.LoadSeqList(self.currentTestRunning.activeSeqList)
         # load the current test running from the next xml file
         nextTest = self.testSuite.GetNextTest()
         testLoaded = 0
         
         # Get Next could have gone past the end of the list.
         # If the iteration count was bumped check status of test
         if self.testSuite.IterationCountChanged():
            # kill all connections
            self.currentComms.Kill()
            try:
                for conn in self.idleConnList:
                    conn.Kill()
            except wx.PyDeadObjectError:
                print("exiting")
                return
                
            self.idleConnList = []

            if self.testSuite.TestScriptDone():
               # end this test
               self.testState = "Stopped"
               self.currentTestCtrl.SetValue("Test Completed")
               print("Current Test Completed")
               return
            else:
               # Next iteration - start fresh
               self.currentTestRunning.LoadFromXMLFile(nextTest,self.config)
               testLoaded = 1
               print("starting next iteration of tests")
               self.config.CreateComms()

               # reset current comms object
               if self.testSuite.GetInitialConnProxied():
                   self.currentComms = self.config.proxyComms
               elif (not self.testSuite.initialConnProxied) and \
                    (not self.testSuite.initialConnIdle):
                   self.currentComms = self.config.comms
               else:
                   self.currentComms = self.config.CreateIdleComm()

               self.testCase = ITC.IscsiTestCase()
               if self.currentComms.Open(self.testCase) != ISOT.OUT_START_PASS:
                   return
               # comms opened ok, so start the thread.
               self.currentComms.start()
               # we have a new test case, load up the seq list
               self.testCase.LoadSeqList(self.currentTestRunning.activeSeqList)
               # Here's a quirk - ITS didn't update its curtest because
               # test could've ended and the user pressed 'start' again,
               # so bump curtest now.
               dummyNextTest = self.testSuite.GetNextTest()
               
             
         # Check to see if the test was loaded ...if not, load it
         if testLoaded == 0:
            self.currentTestRunning.LoadFromXMLFile(nextTest,self.config)
                      
      # have the test descriptor execute the next test
      self.currentComms = self.currentTestRunning.StepTest(self.testCase,
                                                    self.config.logFile,
                                                    self.currentComms,
                                                    self.config.comms,
                                                    self.config.proxyComms)
      # flush log for safety's sake
      self.config.logFile.flush()                                       
                                       
      # check if an error occurred
      if self.currentTestRunning.ErrOccurred():
         self.failureCount += 1  
         if ((self.config.haltOnError == 'True') or 
             (self.config.haltOnError == 'true')):
            self.testState = "Stopped"                 
            print("Error in test. Halt on Error is set, halting test.")
            print("Check Log File for error specifics.  <CTRL C> to quit.")

   def OnCloseWindow(self, event):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.OnCloseWindow
      ;
      ;   RESPONSIBILITY  What To do when close window hits
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """

      self.app.keepGoing = False

      self.Destroy()
      
   def OnIdle(self, event):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.OnIdle
      ;
      ;   RESPONSIBILITY  What To do when idle occurs 
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      # update all controls
      self.UpdateControls()
      
   def OnOpenFile(self, event):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.OnOpenFile
      ;
      ;   RESPONSIBILITY  What To do when Open File occurs 
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      if self.testState != "Stopped":
          return    # do nothing if a test is running.  Duh.
      
      filename = None
      
      # Create the dialog. In this case the current directory is forced as the starting
      # directory for the dialog, and no default file name is forced. This can easilly
      # be changed in your program. This is an 'open' dialog, and allows multitple
      # file selections as well.
      #
      # Finally, if the directory is changed in the process of getting files, this
      # dialog is set up to change the current working directory to the path chosen.
      dlg = wx.FileDialog(
            self, message="Choose a test suite",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard="ITS*.xml",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
            )
      
      # Show the dialog and retrieve the user response. If it is the OK response, 
      # process the data.
      if dlg.ShowModal() == wx.ID_OK:
          # This returns a Python list of files that were selected.
          filename = dlg.GetFilename()

      dlgPath = dlg.GetPath()

      # change the working dir to the path where we got the test suite.
      p = os.path.split(dlgPath)[0]
      os.chdir(p)
 
      # Destroy the dialog. Don't do this until you are done with it!
      # BAD things can happen otherwise!
      dlg.Destroy()
      
      # Open the file.  Make a new test suite for safety's sake.
      if filename:
         self.testSuite = ITS.IscsiIts()
         fileOpened = self.testSuite.LoadFromXMLFile(filename,self.config.logFile)
         
         # save off the path and test suite name to the config file
         if fileOpened:
            self.config.SaveSuite(dlgPath)
         
         
   def OnHelpAbout(self,event):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.OnHelpAbout
      ;
      ;   RESPONSIBILITY  Show help/about window
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      wx.MessageBox("iSCSISim Copyright 2009,2018 ATTO Technology Inc.\r\n"
                    "Version %s \r\n\r\n"
                    "This program comes with ABSOLUTELY NO WARRANTY.\r\n"
                    "This is free software, and you are welcome to redistribute it \r\n"
                    "under the terms of the BSD license. \r\n\r\n"
                    "See the source code for more details. \r\n"  % self.version,
                    "About iSCSISIM", wx.OK | wx.ICON_INFORMATION, self)
      
         
   def OnStartStopTest(self, event):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.OnStartStopTest
      ;
      ;   RESPONSIBILITY  What To do when Start/Stop hits 
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      if self.testState == "Stopped" and self.testSuite.loaded:
         print("Start button pressed...")
         # set up the state as test started
         self.currentTestCtrl.SetValue("Test Started")
         self.testState = "Started"
         self.startStopButton.SetLabel("Stop")
         # kick off a thread to run the tests
         print("Kicking off RunTests thread...")
         self.config.CreateComms()

         if self.testSuite.GetInitialConnProxied():
             print("Utilizing proxy service")
             self.currentComms = self.config.proxyComms
         elif (not self.testSuite.initialConnProxied) and \
                 (not self.testSuite.initialConnIdle):
             self.currentComms = self.config.comms
         else:
             print("Utilizing idle-bound connection")
             self.currentComms = self.config.CreateIdleComm()
             self.idleConnList.append(self.currentComms)

         threading.Thread(target=self.RunTests).start()
      elif not self.testSuite.loaded:
         self.currentTestCtrl.SetValue("NO TEST SUITE LOADED")
      else:
         self.currentTestCtrl.SetValue("Test Stopped")
         self.testState = "Stopped"
         self.startStopButton.SetLabel("Start")
         
   def OnExitButton(self, event):
      """
      ****************************************************************************
      ;
      ;   FUNCTION      TestToolFrame.OnExitButton
      ;
      ;   RESPONSIBILITY  What To do when Exit pressed.
      ;
      ;   PARAMETERS  Name      I/O  Description
      ;               self      instance of test tool frame
      ;               event     event to process
      ;
      ;   RETURNS   Nothing
      ;
      ****************************************************************************
      """
      if self.testState ==  "Started":
         self.testState = "Stopped"
         self.exiting = True          
      else:    
         self.currentComms.Kill()
         self.Destroy()
             
      

         
         
         
         
        
         
         
