##---------------------------------------------------------------------
## ImportARGOS.py
##
## Description: Read in ARGOS formatted tracking data and create a line
##    feature class from the [filtered] tracking points
##
## Usage: ImportArgos <ARGOS folder> <Output feature class> 
##
## Created: Fall 2024
## Author: brian.mulu@duke.edu (for ENV859)
##---------------------------------------------------------------------

# Import modules
import sys, os, arcpy

#Allow outputs to be overwritten
arcpy.env.overwriteOutput = True

# Set input variables (Hard-wired)
#inputFolder = 'V:/ARGOSTracking/Data/ARGOSData'
#outputSR = arcpy.SpatialReference(54002)
#outputFC = "V:/ARGOSTracking/Scratch/ARGOStrack.shp"

# Set input variables (user input)
inputFolder = arcpy.GetParameterAsText(0)
outputSR = arcpy.GetParameterAsText(1)
outputFC = arcpy.GetParameterAsText(2)

# Create a list of files in the user provided input folder
inputFiles = os.listdir(inputFolder)

## Prepare a new feature class to which we'll add tracking points
# Create an empty feature class; requires the path and name as separate parameters
outPath,outName = os.path.split(outputFC)
arcpy.CreateFeatureclass_management(outPath, outName,"POINT","","","",outputSR)

# Add TagID, LC, IQ, and Date fields to the output feature class
arcpy.AddField_management(outputFC,"TagID","LONG")
arcpy.AddField_management(outputFC,"LC","TEXT")
arcpy.AddField_management(outputFC,"Date","DATE")

# Create the insert cursor
cur = arcpy.da.InsertCursor(outputFC,['Shape@','TagID','LC','Date'])

#Iterate through each input file
for inputFile in inputFiles:
    #Skip the README.txt file
    if inputFile == 'README.txt': continue

    #Give the user some status
    arcpy.AddMessage(f'Working on file {inputFile}')
    
    #Prepend inputfile with path
    inputFile = os.path.join(inputFolder,inputFile)
    
    #%% Construct a while loop and iterate through all lines in the data file
    # Open the ARGOS data file
    inputFileObj = open(inputFile,'r')
    
    # Get the first line of data, so we can use the while loop
    lineString = inputFileObj.readline()

    # Start the while loop
    while lineString:
        
        # Set code to run only if the line contains the string "Date: "
        if ("Date :" in lineString):
            
            # Parse the line into a list
            lineData = lineString.split()
            
            # Extract attributes from the datum header line
            tagID = lineData[0]
            obsDate = lineData[3]
            obsTime = lineData[4]
            obsLC = lineData[7]
            
            # Extract location info from the next line
            line2String = inputFileObj.readline()
            
            # Parse the line into a list
            line2Data = line2String.split()
            
            # Extract the data we need to variables
            obsLat = line2Data[2]
            obsLon= line2Data[5]
            
            
            # Print results to see how we're doing
            #print (tagID,obsDate,obsTime,obsLC,"Lat:"+obsLat,"Long:"+obsLon)

            #Try to convert the coordinates to numbers
            try:
                # Convert raw coordinate strings to numbers
                if obsLat[-1] == 'N':
                    obsLat = float(obsLat[:-1])
                else:
                    obsLat = float(obsLat[:-1]) * -1
                if obsLon[-1] == 'E':
                    obsLon = float(obsLon[:-1])
                else:
                    obsLon = float(obsLon[:-1]) * -1

                # Construct a point object from the feature class
                obsPoint = arcpy.Point()
                obsPoint.X = obsLon
                obsPoint.Y = obsLat

                # Convert the point to a point geometry object with spatial reference
                inputSR = arcpy.SpatialReference(4326)
                obsPointGeom = arcpy.PointGeometry(obsPoint,inputSR)

                # Create a feature object
                cur.insertRow((obsPointGeom,tagID,obsLC,obsDate.replace(".","/") + " " + obsTime))
            
            #Handle any error
            except Exception as e:
                arcpy.AddWarning(f"Error adding record {tagID} to the output: {e}") 

        # Move to the next line so the while loop progresses
        lineString = inputFileObj.readline()
        
    #Close the file object
    inputFileObj.close()

#Delete the cursor object
del cur

