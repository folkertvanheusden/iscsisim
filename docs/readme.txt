                     ISCSI TEST TOOL - Gen II V 0.80 beta     5/4/2018
================================================================================

OVERVIEW:  iSCSISim a PC application which is simple to 
run and self-verifying.  It allows a suite of iSCSI tests to be created and
run to verify our iSCSI stack.  PDU's are sent into the DUT via a serial interface or over sockets using the address configured in the config.txt file. 


----------------------------------GETTING STARTED-------------------------------
Make sure that you have already installed python 2.7.5 or later.  Other packages
you'll need : wxPython (http://wxpython.org)  
	      xml.etree.ElementTree (should be loaded by default in python).
	      pySerial (http://pyserial.sourceforge.net)

Don't panic - the installation of python and the related packages is pretty much
painless - the respective developers have done a good job on installation.

Once you have all the packages, place the iSCSISim package into its own directory
and start the python file iSCSISim.py.  See below for more information.

---------------------------------------------------------------------------------


----------------------------------PLATFORMS-------------------------------------
As of 5/2018 iSCSI Sim is supported on both Linux and Windows. Specifically it
was tested using Windows 10 and CentOS 7.

-------------------------------------------------------------------------------- 

----------------------------------SOCKET----------------------------------------

RUNNING A TEST: First, connect a PC with this test tool with the device under
test using one of the data ports.  Change the ip address in confg.txt to match
the ip address of your datport.  (Try pinging it to make sure they can talk)
      Now verify that the PDU's you want to send and receive are all in 
the PDUs directory, one level below the dirctory containing test case(s) and the 
test suite file(s).  Run the iSCSISim python file.  Use the File-Open dialog to 
pick the test suite to run.  The start-stop button will start (or stop) the test 
running, and the display should show what's going on.
       A log file will be created in the 'log' directory directly below the 
directory holding the source files.  Log files are unique by date and time.
If the log file has any lines which say ERROR in them, there will be a 
description of the  particular failure which occurred.  Errors in the test 
files themselves will likely be thrown as exceptions as the file is encountered.  
      That's all there is to it!  Make sure that any new PDU's, test cases and
test suites are checked into the Iscsi test tool project in hg, so that 
everyone can benefit from your work.  

--------------------------------------------------------------------------------


-----------------------------------CONFIG FILE----------------------------------

There is a config file, named config.txt in the root directory.  It has the 
following format:
[PROJECT]
comms 
targetname
haltonerror 
[TCP]
IpAddress 
TcpPort 

comms        - can be either TCP or Serial.
targetname   - is optional, it's used to specify the target name for login (if the
$TGTNAME$ key is placed in the login data file).
haltonerror  - is optional. (True or False). If set to True the test suite will 
	       halt as soon as an error is logged.  If set to false errors will be 
	       logged but the test will continue (default behavior).
[TCP]        - only necessary if comms is set to tcp
IpAddress    - uses dotted-decimal notation (10.30.40.50)
TcpPort      - is the tcp port number to use for iscsi.
ProxyAddress - only necessary if you want to use the proxy script for connection
               reinstate testing

--------------------------------------------------------------------------------
------------------------CONSTRUCTION--------------------------------------------
The iSCSISim tool is written in python, for version 2.7.5.  It 
uses the following python packages:
   Win 32 : Python 2.5 pywin32-210
   serial : Python 2.5 pyserial-2.2
   wxwindows: Wxpython 2.8

Look for these on the internuts. 
   
The tool is broken into several modules.  Each different type of test file has
its own class, as well as classes for serial i/o, a container for the current
test case, the tool frame (window) and the overall test tool.  See each module
for specifics on the classes involved.  I tried to document as much as I could.
If there's something in there that's undocumented, it's probably because I, as
a novice Pythoneer, didn't know the answer myself.

One note about how the files are loaded (see below for file descriptions).  The 
test suite file has each test description filename stored in a list of names. 
Each test description is loaded and parsed, in its entirety (including data) 
prior to running the test.  If you seem to be running out of memory, that's 
because the test description is too long.  It's best to keep the test 
descriptions as succinct as possible.  Don't load up a steamy pile of test cases
in a single test description file and it should be okay.

--------------------------------------------------------------------------------
--------------------------FILE TYPES -------------------------------------------
There are three file types : Test Suites (ITS), Test Descriptions 
(ITD), and Protocol Data Units (PDU).  Each file type is, by convention, 
prefixed with the 3-letter descriptor above.  All of the files in a particular
test configuration should reside in the same directory as the test suite.  (You
could try different directories, but then you'd be on your own.  Not like I 
tested this thing thoroughly - sheesh.)  

  [Test Suite (ITS)]
      +:: [Test Description 1 (ITD)]
                  +:: [Input PDU 1] <> [Output PDU 1]
                  +:: [Input PDU n] <> [Output PDU n]
      +:: [Test Description n (ITD)]
                  +:: [Input PDU 1] <> [Output PDU 1]
                  +:: [Input PDU n] <> [Output PDU n]

   TEST SUITES:  Test suites contain a series of tests, including the login and
      the logout, intended to be iterated by the tool.  Field substitution 
      ($TTT, for example) is done on a test suite basis, per iteration. Test 
      cases will be run in the order that they appear in the test suite file.  
      Test suite files have a ITS prefix by convention, and describe a set of 
      iscsi test cases. Test suite files are the top file in the test framework. 
      
      XML:  
      
      ISCSITS iterations = "n" initconn = "conn" <!-- This is the base tag. 
                                     The iterations field is optional.
                                     The initconn field is also optional.
         FILENAME               <!-- Describes the name of a test description 
                                        file.

   TEST DESCRIPTIONS:  Test description files contain a set of PDU's to be 
      executed in order.  Test description files have an ITD prefix by 
      convention, and describe a single iscsi test case.  They are the middle 
      file in the test framework, and can be executed multiple times as part 
      of a test suite.
      
      XML:
      ISCSITD     <!-- the test descriptoin base tag.  Each file needs this.
         CmdSeqList       <!-- starts the list of command sequences 
            CmdSeq Id="n" <!-- starts a cmd sequence (group of pdus with the same ITT)
	       PDU i="m"  <!-- a single pdu, input or output

	 RunList          <!-- list of triggers and 'R' tuples
	   R Trig="(n,m)" <!-- A single trigger+output grouping.  Triggers and outputs
                          <!-- are described by a tuple (cmdseq id,pdu id) referring to
                          <!-- the CmdSeqList.  Triggers are optional (the first R entry
                          <!-- doesn't typically have a trigger).  Output specifiers are
                          <!-- also optional - the last R entry must NOT have an output
                          <!-- specified.
	   R Trig="Delayn"<!-- Instead of triggering on a pdu, wait n seconds n must
	                       b an int or a valid float, not hexadecimal.
         
           In addition to a trigger, a runlist item may contain connection/socket
           oriented commands. These commands are executed before the PDU specified in
           the runlist element is actually sent out.

           Connection="New"   Specify "New" to create a new connection. Any other value
                              keeps the existing socket. If "New" is specified here,
                              the Target attribute is also required. Otherwise,
                              both Connection and Target are optional.
	   Connection="TcpReset"   Specify "TcpReset" to force a TCP socket teardown and
			      reconnect after the trigger is received.  Syntax for reset
			      is <R Trig="(n,m)" Connection="TcpReset"/>
           Target="tgt"       Specify the target of the new socket. This can be "DUT"
                              to create a new socket to the DUT, or "Proxy" for
                              a new connection to the proxy script. If Connection
                              is not "New," this field is ignored.

   PROTOCOL DATA UNITS: PDU files contain a single iSCSI PDU, with or without 
      data and with or without digests.  There are a number of fields which can
      be filled in by the test tool. PDU files, if used as outputs from the DUT,
      can contain don't care fields which should not be checked.  Don't try to
      send a don't care field as an input file.  That's undefined.  PDU files 
      can be executed many, many times during the course of a test suite. 
      
      All values in the PDU files are in HEXADECIMAL.
      
      XML:
      
      ISCSIPDU IgnoreCmdSN="False" <!-- the pdu base tag.  Each file needs this.
	       <!-- The optional 'ignorecmdsn' is used if a test wants to send
               <!-- in illegal commandSN values, but wants iSCSISim to automatically
               <!-- generate the proper cmdsn on the 'next' pdu. Not needed for 
               <!-- immediate commands, since they're automatically ignored.
         BHS   <!-- Begins the basic header section of a pdu
            DWORD1                 <!-- first dword of the BHS
            AHSLEN                 <!-- one-byte field for ahs
            DATASEGLEN             <!-- three-byte field 
            LUN                    <!-- eight-byte field. you can specify tsih="current" to
                                   <!-- automatically insert the latest tsih into the last 2
                                   <!-- bytes, or (for receive PDUs) specify comparetsih="false"
			           <!-- to skip comparison of the TSIH field. Useful for login
                                   <!-- responses when you will not know the actual TSIH.
            ITT                    <!-- dword field.  Can be $ITT
            DW20           <!-- These are 'chameleon fields' meaning that they
            DW24                change with each different command type.  Fill   
            DW28                in with the proper data. Note that 0 is the 
            DW32                same as 00000000.
            DW36
            DW40
            DW44
        <!-- AHS is not represented -->
        HEADERDIGEST   <!-- header digest.  usually null.  If the test tool 
                            has to send a header digest, it'll expect one from
                            the DUT.   Use $DIGEST here to have it automagically
			    calculated by the test tool.
        DATA len="n" compare = "True" <!-- if data is empty, len is an optional 
                                           field.  Compare field is only needed 
                                           for output files. 
           FILE          <!-- filename of the data file
        DATADIGEST     <!-- data digest.  usually null.  If the test sends a data
			    digest in the request, it'll expect 
			    one from the DUT (as long as datalen != 0).  Use $DIGEST 
			    here to have it substituted by the tool.
                            
      SUBSTITUTIONS:                            
       $CMD_SN
       $EXP_STAT_SN
       $ITT
       $TTT
       $TSIH
       $DIGEST
       $TGTNAME$   (substitute in binary files which have the login="True" attribute)
       $X   (don't care - use on output files)
--------------------------------------------------------------------------------

--------------------------USING the DELAY TRIGGER-------------------------------
The Delay trigger is not obvious, so here's an example:
Here the tool sends a 64K read and verifies it.  Then waits for 5 seconds, to
enable a debug command on the target to facilitate task management testing.  The
tool then sends a read with a known ITT followed immediately by an abort task
command.  It then waits for and validates the Task Management response.

<ISCSITD>
   <CmdSeqList>
      <CmdSeq Id="1">
         <PDU i="1">PDUs\ScsiReadPDUs\PDUScsiRead64K.xml</PDU>
         <PDU i="2">PDUs\DataInPDUs\PDUDataIn64K.xml</PDU>
      </CmdSeq>
      <CmdSeq Id="2">
         <PDU i="1">PDUs\ScsiReadPDUs\PDUScsiRead64KITTFoo.xml</PDU>
         <PDU i="2">PDUs\TaskManagement\PDUAbortTask.xml</PDU> 
         <PDU i="3">PDUs\TaskManagement\PDUTMResponseOk.xml</PDU> 
      </CmdSeq>
   </CmdSeqList>
   
   <RunList>
      <R>(1,1)</R>
      <R Trig="(1,2)"/> 
      <R Trig="Delay5"/>
      <R>(2,1)</R>
      <R>(2,2)</R>
      <R Trig="(2,3)"/> 
   </RunList>
</ISCSITD>
-------------------------------------------------------------------------------
--------------------------TCP RESET -------------------------------------------
The TcpReset attribute can be added to the runlist after any trigger.  Once
the trigger has been received (regardless of match) the TCP connection will 
be closed and reopened.

<ISCSITD>
   <CmdSeqList>
       <CmdSeq Id = "1">
          <PDU i="1">PDUs\LoginPDUs\PDULogin1.xml</PDU>
          <PDU i="2">PDUs\LoginPDUs\PDULogin1rsp.xml</PDU>
       </CmdSeq>
       <CmdSeq Id = "2">
          <PDU i="1">PDUs\ScsiCommandPDUs\PDUTestUnitReady.xml</PDU>
          <PDU i="2">PDUs\ScsiResponsePDUs\PDUScsiUnitAttrsp.xml</PDU>
       </CmdSeq>
       <CmdSeq Id = "3">
          <PDU i="1">PDUs\LogoutPDUs\PDULogoutSession.xml</PDU>
          <PDU i="2">PDUs\LogoutPDUs\PDULogoutRspOK.xml</PDU>
      </CmdSeq>
       
   </CmdSeqList>
   <RunList>
      <R>(1,1)</R>
      <R Trig="(1,2)">(2,1)</R>
      <R Trig="(2,2)">(3,1)</R>
      <R Trig="(3,2)" Connection="TcpReset"/>
   </RunList>
</ISCSITD>
--------------------------------------------------------------------------------
--------------------------PROXY/CONNECTION REINSTATE----------------------------

This version of iSCSISim supports connection reinstate testing through a proxy
script. Conceptually, iSCSISim uses two sockets and switches between the two
when a test description tells it to do so. Only one socket is open at any given
time against the DUT.

When a test description commands iSCSISim to drop a connection, iSCSISim will
send special commands to the proxy script telling it to drop all packets on the
floor. iSCSISim will then open a new socket around the proxy connection and
testing can continue as usual. Shown below is a connection diagram illustrating
how this is set up:


               Proxy Control Socket    
           ---------------------------
          |                           |
          v                           v
      --------      Proxy Comms     -----
     |iSCSISim|<------------------>|Proxy|
      --------                      -----
          ^                           ^
          |                           |
          |                           v
          |        DUT Comms         ---
           ------------------------>|DUT|
                                     ---

When a test suite is loaded, iSCSISim will choose which connection to start
first based on the string attribute "initconn" in the root ISCSIITS node. If proxy, 
the Proxy Comms is the initial connection. If idle, a connection is created that
will go idle (rather than be closed) when a different socket is selected.
Otherwise, DUT Comms is the first.

The advantage of having a proxy for testing is that TCP traffic can be paused
and continued later with a simple command rather than pulling cables.

Remember that connection reinstate only works if a connection is still alive
after the logout of the failed one!

-----------------------------------BUGS-----------------------------------------

MB (1/28/2009): Any connection reinstate attribute in the last element of the
                runlist within an ITD is not processed.
DC (3/01/2018): If a new command sequence is referenced in the run list it must
 		start with index 1 otherwise an exception is raised. 
DC (4/30/2018): If an iSCSI Initiator Task Tag (ITT) is reused within a test 
		description (within the same ITD) the iSCSI Target Task Tag (TTT)
		will not be captured properly.
DC (5/4/2018):  The exit button, added in v 0.70, has been broken in most cases.
		Use CTRL-C to exit the script.

-----------------------------------TODO-----------------------------------------

TODO:  If there's something in the tool that doesn't work right, feel free to
dig in an fix it.  Contact David Cuddihy through sourceforge to be granted access
to the project.
     
TODO: Multiple Connections:  It would be very helpful to be able to spawn multiple
simultaneous connections that are somehow linked to each other. For multiple
initiator testing.

TODO: Command Line IFC: It would be useful to be able to initiate tests and read
results from a command line interface in order to integrate easier with Jenkins.


