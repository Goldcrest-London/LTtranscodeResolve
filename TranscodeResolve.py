#!/usr/bin/env python

"""
Wait for a drive to be mounted on a predefined path and transcode all the labrolls one by one using a Resolve Render Preset.
See Usage for more details

"""

import os
import sys

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
	os.environ["RESOLVE_SCRIPT_LIB"]="/opt/resolve/libs/Fusion/fusionscript.so"
	os.environ["PYTHONPATH"]		="/home/ltreherne/Documents/Programming/Resolve_scripts/Modules/"

print('Environment variables set to:')
print(os.environ['RESOLVE_SCRIPT_API'])
print(os.environ['RESOLVE_SCRIPT_LIB'])
print(os.environ['PYTHONPATH'])
		
#print(os.environ)
#print("")
#print(sys.path)

from python_get_resolve import GetResolve
from os.path 			import exists
from pathlib 			import Path
from csv 				import reader
from csv 				import DictReader
from shutil 			import copytree, ignore_patterns

#import pathlib
import re
import datetime
#import difflib
import xml.etree.ElementTree as ET
import time

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
	elif str.startswith('INFO'):
		c=bcolors.GREEN
	else:
		c=bcolors.NORMAL
	print(c+str+bcolors.ENDC)
	now = datetime.datetime.now()
	date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
	logFile.write(date_time+" "+str+"\n")

# ----------------------------- #

def getListOfFiles(dirName,fileExt):
	baseName=os.path.basename(os.path.normpath(dirName))
	listOfFile = os.listdir(dirName)
	allFiles = list()
	for entry in listOfFile:
		fullPath = os.path.join(dirName, entry)
		#if os.path.isdir(fullPath) and baseName!="OCF" and baseName!="OSF":
		if os.path.isdir(fullPath) and baseName.find('OCF')==-1 and baseName.find('OSF')==-1:
			allFiles = allFiles + getListOfFiles(fullPath,fileExt)
		elif os.path.splitext(entry)[1] == fileExt and entry[0] != '.':
			allFiles.append(fullPath)
	return allFiles


# ----------------------------- #

def LTcheckArgs( argv ):
	#LTprint(len(argv))
	if len(argv)<4:
		print("")
		print("=================================================================================================================================================================")
		print("")
		print("Usage : python3 "+argv[0]+" [Lookup Path] [Transcoded Media Path] [Existing Resolve Project Name]")
		print("")
		print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
		print("")
		print("TranscodeResolve look at a specific path and if it sees new media then it will transcode each camroll")
		print("Resolve needs to be already running on the database where the predefine project already exist")
		print("It will automatically create the media bin structure as well as timelines and render transcoded media onto the defined path")
		print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
		print("PLEASE MAKE SURE THE CREATE THE RESOLVE PROJECT FIRST AND THE RENDER PRESET NAMES 'transcode'")
		print("THE RENDER PRESET NEENDS TO BE SETUP WITH THE FOLLOWING OPTIONS")
		print("- Filename : Source name ")
		print("- Location : The transcoded media folder")
		print("- Render Individual clips")
		print("- Render at source resolution")
		print("- Preserve directory levels set accordingly")
		print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
		print("")
		print("To run the script on Mac for the TranscodeResolve project and '/Volumes/NVME' lookup Path, Rendering in '/Volumes/SPARK/Transcoded'")
		print("- Start Resolve and select the Project database.")
		print("- Open a terminal windows and type.")
		print("  % cd /Library/Application\ Support/Blackmagic\ Design/DaVinci\ Resolve/Developer/Scripting/Examples/")
		print("  % python3 LTtranscodeResolve/transcodeResolve.py /Volume/NVME /Volumes/SPARK/Transcoded TranscodeResolve")
		print("")
		print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
		print("")
		print("The Shoot day folder structure needs to be as bellow:")
		print("> [Project Name]")
		print("     > [Shoot Day Name]")
		print("          > OCF (Original Camera Files)")
		print("          	> [Camera] (Original Camera Files organised by Camroll (i.e A131RO25)")
		print("          > OSF (Original Sound Files)")
		print("          > METADATA")
		print("")
		print("NOTE: PLEASE DO NOT USE ANY SPECIAL CHARCTERES INCLUDING SPACES ON FOLDERS OR FILE NAMES")
		print("=================================================================================================================================================================")
		print("")
		print("")
		print("")
		
		
		return 0
	elif len(argv)==3:
		return 1
	else:
		return 2

# ----------------------------- #

def LTcheckProjTmplExist( ProjTempl ):
	if exists(ProjTempl):
		return True
	else:
		LTprint("ERROR : Cannot open drp file "+ProjTempl)
		return False

# ----------------------------- #

def LTcreateNewProjectFromTemplate( ProjTempl ):
	ok = LTcheckProjTmplExist(ProjTempl)
	if ok != True:
		LTprint("Resolve .drp file doesn't exist")
		exit()
	# import template
	ok = projMgr.ImportProject(ProjTempl)
	if ok != True:
		LTprint("ERROR importing the template from file "+ProjTempl)
		LTprint("Please note you need to put the full path (not the relative path)")
		exit()
	ProjTemplName = Path(ProjTempl).stem
	proj = projMgr.LoadProject(ProjTemplName)
	proj.SetName(ProjName)

# ----------------------------- #

def LTisFolderExist( folderList,folderName ):
	resolveFolder="None"
	for folder in folderList:
		if (folder.GetName()==folderName):
			resolveFolder=folder
	return resolveFolder

# ----------------------------- #

def LTisTimelineExist(timelineName ):
	#print("LTisTimelineExist "+timelineName)
	resolveTimeline="None"
	timelineCount = proj.GetTimelineCount()
	for index in range (0, int(timelineCount)):
		timeline = proj.GetTimelineByIndex(index + 1)
		if timeline.GetName()==timelineName:
			resolveTimeline=timeline
	return resolveTimeline

# ----------------------------- #

def LTisLookupFolderValid(folder):
	global shootDay
	# check if the Lookup folder has a subfolder looking like BK01_MU01_20220517 with a num empyy OCF subfolde
	# a valid folder structure would be [lookupFolder]/[projectName]/[ShootDate]/OCF
	mypath=''
	if not os.path.exists(folder):
		return 0
	else:
		listDir=[os.path.join(LookupPath, o) for o in os.listdir(LookupPath) if (os.path.isdir(os.path.join(LookupPath,o)) and (os.path.basename(o)[0]!='.'))]
		#print(listDir)
		if listDir==[]:
			return 0
		else:
			if len(listDir)>1:
				LTprint("ERROR : The Lookup folder has more than one [Project] Folder")
				return -1
			else:
				# go to the project folder
				mypath=os.path.join(LookupPath,listDir[0])
				listDir=[os.path.join(mypath, o) for o in os.listdir(mypath) if os.path.isdir(os.path.join(mypath,o))]
				if len(listDir)>1:
					LTprint("ERROR : The Project folder has more than one [shootday] Folder")
					return -1		
				else:
					if not re.search("[a-zA-Z0-9]{4}_[a-zA-Z0-9]{4}_[0-9]{8}$", listDir[0]):
						LTprint("ERROR : The Shoot Day '"+listDir[0]+"'folder name is not correct. We are expecting something like BK01_MU01_20220517")
						return -1
					else:
						shootDay = os.path.basename(os.path.normpath(listDir[0]))
						mypath = os.path.join(mypath,listDir[0])
						listDir = os.listdir(mypath)
						findOCF = False
						for dir in listDir:
							if dir=="OCF":
								findOCF = True
								mypath = os.path.join(mypath,dir)
						if findOCF==True:
							return mypath
						else:
							return -1



def LTcreateNewShootDay():
	global dayBlock
	global dayUnit
	global dayBin
	
	LTprint("INFO : Create ShootDay Bins for block "+dayBlock+" / "+dayUnit)
	rootfolder=mediapool.GetRootFolder()
	# Create the Block Bin if not exit
	folderList = rootfolder.GetSubFolderList()
	tmpFolder = LTisFolderExist(folderList,dayBlock)
	if tmpFolder!="None":
		LTprint("INFO : "+dayBlock+" Bin already exist")
		blockfolder=tmpFolder
	else:
		blockfolder=mediapool.AddSubFolder(rootfolder,dayBlock)
	# Create the Unit Bin if not exit
	folderList = blockfolder.GetSubFolderList()
	tmpFolder = LTisFolderExist(folderList,dayUnit)
	if tmpFolder!="None":
		LTprint("INFO : "+dayUnit+" Bin already exist")
		dayBin=tmpFolder
	else:
		dayBin=mediapool.AddSubFolder(blockfolder,dayUnit)
	
# ----------------------------- #

def LTtranscode():
	global OCFfolder
	global dayBin
	global dayBlock
	global dayUnit
	global TranscodePath
	global logFile
	global proj
	global renderjob

	try:
		# create new timeline with the timelineName name if it doesn't exit
		# Create the Bin folders
		LTcreateNewShootDay()
		# create new timeline with the timelineName name if it doesn't exit
		mediapool.SetCurrentFolder(dayBin)
		try:
			LTprint("INFO : Load clips onto the mediapool...")
			myclips=mediastorage.AddItemListToMediaPool(OCFfolder)
			# add all the clips on a new timeline
			LTprint("INFO : Create Timeline...")
			mytimeline=mediapool.CreateTimelineFromClips('Timeline_'+dayBlock+'_'+dayUnit,myclips)
			# create render queue
			proj.DeleteAllRenderJobs()
			LTprint("INFO : Load Transcode render preset...")
			if not proj.LoadRenderPreset("transcode"):
				LTprint("ERROR  : Can't find any preset called 'transcode'. Please check your Resolve project...")
			try:
				# force path to preserve the 
				LTprint("INFO : Create Render job...")
				renderjob=proj.AddRenderJob()
				proj.StartRendering(renderjob)
				LTprint("INFO : Start rendering...")
			except:
				LTprint("ERROR  : Rendering failed...")
		except:
			LTprint("ERROR : Can't import clip from "+OCFfolder)
		# 

	except:
		LTprint("ERROR : Can't create the bins for "+dayBlock+" / "+dayUnit);		
	
# ----------------------------- #

def LTcopyNonOCFfiles():
	# this needs to be doe after the transcode is completed because the path for the transcode is set within the resolve reder preset
	# The script doesn't know the exact organisation of the folder structure
	global TranscodePath
	global OCFfolder
	#find the OCF transcoded folder
	OCFTfolder=''
	srcFolder, tail = os.path.split(OCFfolder)
	# r=root, d=directories, f = files
	for r, dirs, files in os.walk(TranscodePath):
		for dir in dirs:
			if 'OCF' in dir:
				OCFTfolder=os.path.join(r, dir)
	if (OCFTfolder==''):
		LTprint("ERROR: Can't find an OCF folder on the Transcoded media paths...")
		return
	else:
		dstFolder, tail = os.path.split(OCFTfolder)
		LTprint("INFO : Copy all non OCF files and folders from "+srcFolder+" to "+dstFolder)
		copytree(srcFolder, dstFolder, ignore=ignore_patterns('*OCF*'),dirs_exist_ok=True)

	


#*******************************************************************************************************
# Main 
#*******************************************************************************************************

version="1.0"
mountPoint="/Volumes/"

if sys.platform.startswith("darwin"):
	resolveRootPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve"
else:
	resolveRootPath = "/opt/resolve"

option = LTcheckArgs(sys.argv)
if option == 0:
	#print("Wrong arguments")
	exit()

# if shootday not finishing by '/' then add one
if sys.argv[1][-1] != '/':
	sys.argv[1]+='/'
rootPath = os.path.dirname(sys.argv[1])
LookupPath = sys.argv[1]
TranscodePath = sys.argv[2]
ProjName = sys.argv[3]
logPath = TranscodePath+"/Silverstack2Resolve.log"
logFile = open(logPath,"a")
shootDay = ''
dayBlock = ''
dayUnit = ''

LTprint(bcolors.BOLD+"----------------------------------------------------------------------------------------------"+bcolors.ENDC)
LTprint(bcolors.BOLD+"TranscodeResolve version "+version+" (c)2023 LT for Goldcrest"+bcolors.ENDC)
LTprint(bcolors.BOLD+"----------------------------------------------------------------------------------------------"+bcolors.ENDC)

try:
	LTprint("Connecting to Resolve...")
	resolve = GetResolve()
	#print(resolve)
	projMgr = resolve.GetProjectManager()
except:
	LTprint("ERROR : Not able to connect to the Resolve API. Please make sure the Resolve software is running...")
	exit()

#load the project
proj = projMgr.LoadProject(ProjName)
LTprint("")
if proj == None:
	LTprint("ERROR : The Resolve project "+ProjName+" Does not exist")
	exit()
else:
	LTprint("INFO : The resolve project "+ProjName+" is now selected...")

mediapool=proj.GetMediaPool()
mediastorage=resolve.GetMediaStorage()
dayfolder=mediapool.GetRootFolder()
timelinefolder=mediapool.GetRootFolder()
LTprint("")
LTprint("INFO : The Lookup path is defined as     : "+LookupPath)
LTprint("INFO : The Transcoded path is defined as : "+TranscodePath)
LTprint("")

# loop until new media is available on the lookup folder
starttime = time.time()
filesInLookup=False
LTprint("INFO : Checking lookup folder "+LookupPath+" for files...")
LTprint(bcolors.YELLOW+"       Process will start as soon as the media will be accessible"+bcolors.ENDC)
LTprint("")
while not filesInLookup:
	ret=LTisLookupFolderValid(LookupPath)
	if ret == -1:
		exit()
	else:
		if ret != 0:
			filesInLookup=True
			OCFfolder=ret
		else:
			time.sleep(10.0 - ((time.time() - starttime) % 10.0))

LTprint("INFO : Begining Transcoding the folder "+OCFfolder+" for shoot day "+shootDay)
dayBlock = shootDay[0:4]
dayUnit = shootDay[5:9]
#******************************************************************
LTtranscode()
# loop until the transcoding is completed
while proj.IsRenderingInProgress():
	stat=proj.GetRenderJobStatus(renderjob)
	# 'JobStatus': 'Rendering', 'CompletionPercentage': 86, 'EstimatedTimeRemainingInMs': 0}
	print("\r",bcolors.CYAN,stat['JobStatus'],"   ",stat['CompletionPercentage'],"%  ",bcolors.ENDC,end='')
	if "EstimatedTimeRemainingInMs" in stat:
		print(bcolors.CYAN,"Remaining : ",stat['EstimatedTimeRemainingInMs']/1000,"sec",bcolors.ENDC,end='')
print("\r",bcolors.CYAN,stat['JobStatus'],"   ",100,"%  ",bcolors.ENDC,end='')
print(bcolors.CYAN,"Remaining : ",0,"sec",bcolors.ENDC,end='')
print("")
LTprint("INFO : Transcoding completed...")
LTprint("INFO : Copy non OCF files...")
LTcopyNonOCFfiles()
#******************************************************************
LTprint("")
LTprint("INFO : Save Project "+ProjName+"...")
projMgr.SaveProject()
LTprint("INFO : Process completed...")
logFile.close()

