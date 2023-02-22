#!/usr/bin/env python

"""
Monitor a predefined folder and copy any files onto another another one
See Usage for more details

"""

import os
import sys
from python_get_resolve 	import GetResolve
from os.path 				import exists
from pathlib 				import Path
from csv 					import reader
from csv 					import DictReader
from shutil 				import copytree, ignore_patterns
from email.mime.text 		import MIMEText
from email.mime.multipart 	import MIMEMultipart

import re
import datetime
import xml.etree.ElementTree as ET
import time
import smtplib
import shutil


#********************************************************
version="1.1"
emailReceivers = ['ltreherne@goldcrestfilms.com']
#********************************************************

os.system('clear')
print("")
if sys.platform.startswith("darwin"):
	print("OSX platform detected...")
	print("")
	# if OSX
	os.environ["RESOLVE_SCRIPT_API"]="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
	os.environ["RESOLVE_SCRIPT_LIB"]="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
	os.environ["PYTHONPATH"]		="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
	#os.environ["PYTHONPATH"]		="/Library/Application\ Support/Blackmagic\ Design/DaVinci\ Resolve/Developer/Scripting/Modules/"
elif sys.platform.startswith("linux"):
	print("Linux platform detected...")
	print("")
	#if Linux
	os.environ["RESOLVE_SCRIPT_API"]="/home/ltreherne/Documents/Programming/Resolve_scripts"
	os.environ["RESOLVE_SCRIPT_LIB"]="/opt/resolve/versions/studio_18.1.2/libs/Fusion/fusionscript.so"
	os.environ["PYTHONPATH"]		="/home/ltreherne/Documents/Programming/Resolve_scripts/Modules/"

print('Environment variables set to:')
print(os.environ['RESOLVE_SCRIPT_API'])
print(os.environ['RESOLVE_SCRIPT_LIB'])
print(os.environ['PYTHONPATH'])
		
#print(os.environ)
#print("")
#print(sys.path)

class bcolors:
	NORMAL	=	'\033[37m'
	BLUE 	= 	'\033[34m'
	GREEN 	= 	'\033[32m'
	CYAN 	= 	'\033[36m'
	RED 	= 	'\033[31m'
	YELLOW 	= 	'\033[93m'
	MAGENTA = 	'\033[35m'
	BOLD 	= 	'\033[1m'
	UNDER 	= 	'\033[4m'
	ENDC 	= 	'\033[0m'
	

# ----------------------------- #

def LTprint(str):

	if str.startswith('WARNING'):
		c=bcolors.MAGENTA
	elif str.startswith('ERROR'):
		c=bcolors.RED
		# also send email
		#LTsendEmail('TranscodeResolve Process ERROR...','<h2 style="color:red;">'+str+'</h2>')
	elif str.startswith('INFO'):
		c=bcolors.GREEN
	else:
		c=bcolors.NORMAL
	print(c+str+bcolors.ENDC)
	now = datetime.datetime.now()
	date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
	logFile.write(date_time+" "+str+"\n")

# ----------------------------- #

def LTsendEmail(subject,message):
	sender = 'TranscodeResolve'
	global emailReceivers

	msg = MIMEMultipart('alternative')
	msg['Subject'] = 'TranscodeResolve ( '+ProjName+' / '+shootDay+' )'
	msg['From'] = 'TranscodeResolve@goldcrestfilms.com'
	msg['To'] = 'undisclosed recipients'
	msg.attach(MIMEText(message, 'html'))
	server = smtplib.SMTP("10.71.3.251")
	try:
		server.sendmail(sender, emailReceivers,  msg.as_string())
		LTprint('INFO  : sending email')
	except Exception as e:
		LTprint('ERROR : sending email')
	finally:
		server.quit()

# ----------------------------- #

def LTcheckArgs( argv ):
	#LTprint(len(argv))
    if len(argv)<3:
        print("")
        print("=================================================================================================================================================================")
        print("")
        print("Usage : python3 "+argv[0]+" [Lookup Path] [Copy Path]")
        print("")
        print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print("")
        print("LookupFilesPull look at a specific path and if it sees new files then it will copy each them on a Copy Path")
        print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print("")
        print("NOTE: PLEASE DO NOT USE ANY SPECIAL CHARACTERES INCLUDING SPACES ON FOLDERS OR FILE NAMES")
        print("      THE SCRIPT WILL NOT REMOVE ANY FILE FROM THE DESTINATION PATH EVEN IF YOU REMOVE THEN FROM THE SOURCE PATH")
        print("      RESTART THE SCRIPT EVERY TIME YOU WANT TO INITIATE A NEW TRANSFER")
        print("=================================================================================================================================================================")
        print("")
        print("")
        print("")
        return 0
    else:
        return 1

# ----------------------------- #

def LTbuildFileList(path):
    global fileList

    #print('build')
    for path, currentDirectory, files in os.walk(path):
        for file in files:
            filePath=os.path.join(path, file)
            if filePath in fileList:
                # check if the file has already been transfered and locked
                # if not locked then update the value in the dict
                if (fileList[filePath]!=-1):
                    fileList[filePath]=os.stat(filePath).st_size
            else:
                # create a new entry on the array for the file
                fileList[filePath]=os.stat(filePath).st_size

# ----------------------------- #

def LTcopyFileIfNeeded(LookupPath,CopyPath):
    global fileList

    #print('copy')
    if bool(fileList) and bool(fileListPrev):
        for keys,values in fileList.items():
            #print(keys,values)
            if keys in fileListPrev:
                if fileListPrev[keys]==values and fileList[keys]!=-1:
                    if LookupPath in keys:
                        srcPath=keys
                        folder=keys.replace(LookupPath+'/','')
                        dstPath=os.path.join(CopyPath,folder)
                        fileList[keys]=-1
                        try:
                            LTprint("INFO  : copy file "+srcPath+" to "+dstPath)
                            if not os.path.isdir(os.path.dirname(dstPath)):
                                os.makedirs(os.path.dirname(dstPath))
                            shutil.copy(srcPath,dstPath)
                        except Exception as e:
                            LTprint("ERROR : copy file "+srcPath+" to "+dstPath)
                            LTprint(e)

# ----------------------------- #


#*******************************************************************************************************
# Main 
#*******************************************************************************************************

option = LTcheckArgs(sys.argv)
if option == 0:
	#print("Wrong arguments")
	exit()

fileList = {}
fileListPrev = {}
LookupPath=sys.argv[1]
CopyPath=sys.argv[2]


logPath = CopyPath+"/LookupFilesPull.log"
logFile = open(logPath,"a")

LTprint(bcolors.BOLD+"----------------------------------------------------------------------------------------------"+bcolors.ENDC)
LTprint(bcolors.BOLD+"LookupFilesPull version "+version+" (c)2023 LT for Goldcrest"+bcolors.ENDC)
LTprint(bcolors.BOLD+"----------------------------------------------------------------------------------------------"+bcolors.ENDC)

#******************************************************************
# loop to check for new files
LTprint(bcolors.YELLOW+"Monitoring "+LookupPath+bcolors.ENDC)
LTprint(bcolors.YELLOW+"Copy to "+CopyPath+" will start as soon as the media will be accessible"+bcolors.ENDC)
LTprint(bcolors.YELLOW+"Press Ctrl-C to stop"+bcolors.ENDC)
try:
    while True:
        try:
            LTbuildFileList(LookupPath)
            #print('FileList    ',fileList)
            #print('FileListPrev',fileListPrev)
            #print('------------------------')
            LTcopyFileIfNeeded(LookupPath,CopyPath)
            fileListPrev=fileList.copy()
        except:
            LTprint("ERROR : building the list of files from the Lookup folder ")
        time.sleep(2)
except KeyboardInterrupt:
    pass

logFile.close()