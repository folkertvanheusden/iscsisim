                     ISCSI TEST TOOL - Gen II V 0.80 beta     5/4/2018
================================================================================

OVERVIEW:  iSCSISim a PC application which is simple to
run and self-verifying.  It allows a suite of iSCSI tests to be created and
run to verify our iSCSI stack.  PDU's are sent into the DUT via a socket interface.
More information, including setup instructions, can be found in the file 
docs/readme.txt 

Release Information:
0.70 beta : Added rule and exit button to GUI, retain the previously loaded ITS
 on startup.
0.80 beta : Added Halt on Error capability to config.txt
            Added Tcp Reset to ITD files
	    Fixed ITS sequencing to better handle large data in and data out.



-----------------------------

Python 2.x -> 3.x conversion by Folkert van Heusden
