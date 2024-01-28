"""
********************************************************************************
;
;   MODULE       IscsiCfg.py       
;
;   DESCRIPTION  Source file for the iscsi test tool configuraiton class
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
import time
import os
from IscsiSerial import IscsiSerial
from IscsiComms import IscsiComms
from IscsiSocket import IscsiSocket
import configparser as CP

class IscsiCfg:
          
   def __init__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.__init__
      ;
      ;   RESPONSIBILITY  Iscsi Configureation class initializer
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiCfg class instance to
      ;                                  initialize
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """

      # set up the log file for this run.
      if not os.access('LogFiles',os.F_OK):
        os.mkdir('LogFiles')
     
      tm = time.localtime()
      logfilenm = "%d%02d%02d_%02d%02d_%d.%s" % (tm[0],tm[1],tm[2],tm[3],tm[4],tm[5],"log")
      
      self.cwd = os.getcwd()
      
      # open up the logfile
      self.logFile =  open(os.path.join("LogFiles", logfilenm),'a')

      # set up the port and ip address
      self.ipAddress = ""
      self.tcpPort = 0
      self.commsType = ""
      self.proxyAddress = ""
      
      # clear up default targetname
      self.targetName = ''
      
      # set the global attributes
      self.haltOnError = ''
      
      # load up the config file parser
      configParser = CP.ConfigParser()
      filelist = configParser.read("config.txt")
      self.configParser = configParser
      if filelist[0] != "config.txt":
          print("File config.txt not found. Using Defaults.")
      else:
          self.GetConfigFileInfo(configParser)
          
          
      # now make our comms object
      self.CreateComms()
      
      
   def __del__(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.__del__
      ;
      ;   RESPONSIBILITY  Iscsi Test Suite class destructor
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The IscsiIts class instance to
      ;                                  initialize
      ;
      ;   RETURNS     Nothing
      ;
      ************************************************************************
      """
      self.logFile.flush()
      self.logFile.close()   
         
   def CreateComms(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.CreateComms
      ;
      ;   RESPONSIBILITY  Make our associated comms object.  
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The configuration class instance 
      ;
      ;   RETURNS     the new IscsiComms (communications) object
      ;
      ************************************************************************
      """
      if self.commsType == "TCP":
          self.tcpPort = int(self.tcpPort)
          self.comms = IscsiSocket(self.logFile,self.ipAddress,self.tcpPort,   \
                                   False)
          self.proxyComms = IscsiSocket(self.logFile,self.proxyAddress,        \
                                        self.tcpPort,True)
          self.logFile.write("Opening up Comms : Socket \n")          
      else:
          self.comms = IscsiSerial(self.logFile)
          self.logFile.write("Opening up Comms : Serial \n")
          
   def CreateIdleComm(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.CreateIdleComm
      ;
      ;   RESPONSIBILITY  Create a new Idle Comms object
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The configuration class instance 
      ;
      ;   RETURNS     the new IscsiComms (communications) object
      ;
      ************************************************************************
      """
      if self.commsType == "TCP":
          return IscsiSocket(self.logFile,self.ipAddress,self.tcpPort,   \
                             False)
      else:
          self.logFile.write("Can't do multiconn for serial \n")
          return None
           
   def GetConfigFileInfo(self,configparser):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.GetConfigFileInfo
      ;
      ;   RESPONSIBILITY  Load up self based on configuration file.
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The configuration class instance 
      ;               configparser  I    Config parser class (already loaded)
      ;
      ;   RETURNS   
      ;
      ************************************************************************

      Config File Format:
      
      [PROJECT]
      Comms = (TCP | SERIAL)
      TargetName = targetname (optional - use $TGTNAME$ in login data file)
      HaltOnError = (True | False)
      [TCP]  (optional - use if comms is TCP)
      IpAddress = n.n.n.n
      TcpPort = n
      ProxyAddress = n.n.n.n
      [SUITE]  (written by app to restore the last test suite)
      FileName = 'path'
      
      """  
      
      projectItems = {'comms':'commsType','targetname':'targetName',
                      'haltonerror':'haltOnError'}
      projectDefaults = [('comms','TCP'),('haltonerror','False')]
      tcpItems = {'ipaddress':'ipAddress','tcpport':'tcpPort',                 \
                  'proxyaddress':'proxyAddress'}
      tcpDefaults = [('ipaddress',"10.30.45.10"),('tcpport',"3260"),           \
                     ('proxyaddress',"0.0.0.0")]
      sections = [('PROJECT',projectItems,projectDefaults),                    \
                  ('TCP',tcpItems,tcpDefaults)]                              


      for section in sections:
         try:
             itemlist = configparser.items(section[0])
         except:
             itemlist = section[2]

         for it in itemlist:
            if it[0] in section[1]:
                self.__dict__[section[1][it[0]]] = it[1]


   def SaveSuite(self,fileName):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.SaveSuite
      ;
      ;   RESPONSIBILITY  Save off the suite filename for later use.  
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The configuration class instance 
      ;
      ;   RETURNS     nothing
      ;
      ************************************************************************
      """
      # check if the config has a Suite section      
      if ('SUITE' not in  self.configParser.sections()):
         self.configParser.add_section('SUITE')
         
      self.configParser.set('SUITE',"Filename",fileName)
      
      try:
        cfgfile = open(os.path.join(self.cwd,"config.txt"),'w')
        self.configParser.write(cfgfile)
      except:
        self.logFile.write("Could not save suite filename to config file")
        
   def ClearSuiteName(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.SaveSuite
      ;
      ;   RESPONSIBILITY  Clear the suite name  
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The configuration class instance 
      ;
      ;   RETURNS     nothing
      ;
      ************************************************************************
      """
      # check if the config has a Suite section      
      if ('SUITE' not in  self.configParser.sections()):
         self.configParser.add_section('SUITE')
         
      try:
          self.configParser.remove_option('SUITE',"Filename")
      except:
          self.logFile.write("Could not remove filename from suite")
    
      try:
        cfgfile = open(os.path.join(self.cwd,"config.txt"),'w')
        self.configParser.write(cfgfile)
      except:
        self.logFile.write("Could not save config file")
             
       
   def GetSuiteFilename(self):
      """
      ************************************************************************
      ;
      ;   FUNCTION        IscsiCfg.GetSSuiteFilename
      ;
      ;   RESPONSIBILITY  Make our associated comms object.  
      ;
      ;   PARAMETERS  Name          I/O  Description                
      ;               self          I/O  The configuration class instance 
      ;
      ;   RETURNS     the new IscsiComms (communications) object
      ;
      ************************************************************************
      """
      # check if the config has a Suite section     
      if ('SUITE' in  self.configParser.sections()):
         try:
             fname = self.configParser.get('SUITE','filename')
         except:
             fname = ''
      else:
         self.logFile.write("suite not in the sections")
         fname = ''
         
      return fname

                
                
# ******************************* TEST CODE *************************
"""
cfg = IscsiCfg() 
print cfg.__dict__
"""


