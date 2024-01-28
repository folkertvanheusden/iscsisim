"""
********************************************************************************
;
;   MODULE       IscsiIts.py       
;
;   DESCRIPTION  Source file for the iscsi Test suite class.
;
;   This file is part of iSCSISim.
;
;   Copyright (c) 2009, 2018 ATTO Technology, inc.
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
import IscsiITD as ITD
import time
import os

class IscsiIts:
          
   def __init__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiIts.__init__
      ;
      ;   RESPONSIBILITY  Iscsi Test Suite class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiIts class instance to
      ;                                  initialize
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      # filename is the file name of this test suite.  That's important because
      # we need to display it AND make an error log
      self.fileName = "None Selected"
      
      # testList is a list of filenames to ITD's
      self.testList = []
      
      # curTest is some sort of iterator
      self.curTest = 0
      self.iteration = 0
      self.numIterations = 0
      # this hasn't been loaded up yet.
      self.loaded = False
      self.iterationChanged = False
      self.initialConnProxied = False
      self.initialConnIdle = False

   def LoadFromXMLFile(self,filename,logfile):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiIts.LoadFromXMLFile
      ;
      ;   RESPONSIBILITY  Read a test suite from an XML file.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test suite class instance 
      ;               filename       I   Filename to parse from
      ;               logfile        I   log file to use for test run
      ;
      ;   RETURNS     False if an error occurred
      ;
      ************************************************************************
      """  
      if filename:

         print("")
         print("----------------------------------------------")
         print("LOADING TEST SUITE: ", filename)
         print("----------------------------------------------")
         
         self.fileName = filename      
         tree = ET.parse(filename)
         tselem = tree.getroot()
         if tselem.tag != "ISCSITS":
            exep = Exception("File "+filename+" did not contain ISCSITS tag")
            raise exep
         else:
            # get the iteration count
            numiters = tselem.get("iterations")
            try:
               self.numIterations = int(numiters)
            except:
               self.numIterations = 1

            # get the initial connection type (idle, proxy or not)
            initconn = tselem.get("initconn")
            if initconn == "proxy":
                self.initialConnProxied = True
                self.initialConnIdle = False
            elif initconn == "idle":
                self.initialConnProxied = False
                self.initialConnIdle = True
            else:
                self.initialConnProxied = False
                self.initialConnIdle = False

            # Load the filenames into the list
            fnlist = tselem.findall("FILENAME")
            for fnelem in fnlist:
               # get the name 
               fn_path = fnelem.text
               fn_path_parts = fn_path.rsplit(os.sep)
               fn = os.path.join(*fn_path_parts)
               # make sure the file exists
               if not os.access(fn,os.R_OK):
                  exep = Exception("File "+fn+" not found (reference from "+
                                       self.fileName + ")")
                  raise exep
               
               # append the file name to the file list
               self.testList.append(fn)

         # that all worked nicely, so open up the logfile
         tm = time.localtime()
         logfile.write("*********************************************\n")
         logfile.write("\n%d/%d/%d : Opened suite %s \n" % 
                                 (tm[1],tm[2],tm[0],filename))
         logfile.write("\n*********************************************\n")


         # refresh the counters we're startin' over
         self.curTest = 0
         self.numIters = 1 
         self.iteration = 0    
         self.iterationChanged = False
         self.loaded = True     
         return True
               
   def GetNextTest(self):   
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiIts.GetNextTest
      ;
      ;   RESPONSIBILITY  return the next test in the list. wraps if necessry
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test suite class instance 
      ;
      ;   RETURNS     the next test in the list
      ;
      ************************************************************************
      """  
      if self.curTest == len(self.testList): 
         self.iteration += 1
         self.curTest = 0
         self.iterationChanged = True
         retval = self.testList[self.curTest]
      else:
         retval = self.testList[self.curTest]
         self.curTest += 1
         
      return retval
    
   def GetIteration(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiIts.GetIteration
      ;
      ;   RESPONSIBILITY  return the iteration count
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test suite class instance 
      ;
      ;   RETURNS     value of the iteration count
      ;
      ************************************************************************
      """  
      return self.iteration
    
   def TestScriptDone(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiIts.TestScriptDone
      ;
      ;   RESPONSIBILITY  return true if iteration count reached
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test suite class instance 
      ;
      ;   RETURNS     true if reached, false otherwise
      ;
      ************************************************************************
      """  
      return self.iteration >= self.numIterations
   
    
   def IterationCountChanged(self): 
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiIts.IterationCountChanged
      ;
      ;   RESPONSIBILITY  clear-on-read accessor of iteration cnt flag
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The test suite class instance 
      ;
      ;   RETURNS     value of the iteration count chg
      ;
      ************************************************************************
      """     
      if ( self.iterationChanged ):
         ret = True
      else:
         ret = False
      self.iterationChanged = False
      return ret    
 
   def GetInitialConnProxied(self):
        """
        ************************************************************************
        ;
        ;   FUNCTION        IscsiIts.GetInitialConnProxied
        ;
        ;   RESPONSIBILITY  Determine if the initial connection should be a
        ;                   proxy.
        ;
        ;   PARAMETERS  Name          I/O  Description                
        ;               self          I/O  The test suite class instance 
        ;
        ;   RETURNS     True if the initial connection is proxied, false
        ;               otherwise.
        ;
        ************************************************************************
        """
        return self.initialConnProxied

# ******************************* TEST CODE *************************
"""
its = IscsiIts()
import os
os.chdir("TestCases")
its.LoadFromXMLFile("ITSTestSuite1.xml")
"""
