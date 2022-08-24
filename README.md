# NASA-LVIS-data
This code can process a single LVIS flight line to a DEM of any resolution and merge them after processing.

## LVIS_DEM.py 

Read data from a single LVIS.h5 file and output a DEM.tif file with changeable resolution.

Includes a class to process and read LVIS data. It is inherts from lvisGround in processLVIS. In order to avoid the program be killed because of take too much RAM, this code divide the flight line route into small ares and output small .tif files and merge them after all areas are processed.

The default arguments are set as follows:
      
      --input Default= '.../lvis/2009/ILVIS1B_AQ2009_1020_R1408_052195.h5'
      --outres Default=30
      --output Default= Output filename

Example: python3 LVIS_DEM.py --outres 40
