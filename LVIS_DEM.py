import numpy as np
import gdal, ogr, os, osr
import argparse
from processLVIS import lvisGround
import time
from pyproj import Proj, transform
import psutil
import os
import glob
from osgeo import gdal
import subprocess

def readCommands():
  '''
  Read commandline arguments
  '''
  p = argparse.ArgumentParser(description=("Convert one LVIS file to raster"))
  p.add_argument("--input", dest ="inName", type=str, default='/geos/netdata/oosa/assignment/lvis/2009/ILVIS1B_AQ2009_1020_R1408_052195.h5', help=("Input filename"))
  p.add_argument("--outres", dest ="outRes", type=int, default=30, help=("Output resolution (m)"))
  p.add_argument("--output", dest ="outName", type=str, default='output.tif', help=("Output filename"))
  p.add_argument("--inEPSG", dest ="inEPSG", type=int,default=4326)
  p.add_argument("--outEPSG", dest="outEPSG", type=int, default=3031)
  cmdargs = p.parse_args()
  return cmdargs

class singlelvis(lvisGround):

  def CofG(self):
    '''
    Find centre of gravity of denoised waveforms
    sets this to an array of ground elevation
    estimates, zG
    '''

    # allocate space and put no data flags
    self.zG=np.full((self.nWaves),np.nan)

    # loop over waveforms
    for i in range(0,self.nWaves):
      if(np.sum(self.denoised[i])>0.0):   # avoid empty waveforms (clouds etc)
        self.zG[i]=np.average(self.z[i],weights=self.denoised[i])

  def writeSingleTiff(self,res,filename):
      '''
      Make a geotiff from an array of points
      '''

      # determine bounds
      minX=np.min(self.lon)
      maxX=np.max(self.lon)
      minY=np.min(self.lat)
      maxY=np.max(self.lat)

      # determine image size
      self.nX=int((maxX-minX)/res+1)
      self.nY=int((maxY-minY)/res+1)

      # pack in to array
      self.imageArr=np.full((self.nY,self.nX),np.nan)        # make an array of missing data flags

      xInds=np.array((self.lon-minX)/res,dtype=int)  # determine which pixels the data lies in
      yInds=np.array((maxY-self.lat)/res,dtype=int)  # determine which pixels the data lies in

      # this is a simple pack which will assign a single footprint to each pixel
      self.imageArr[yInds,xInds]=self.zG

      self.imageArr=np.where(self.imageArr == -999.0, np.nan, self.imageArr)

      # set geolocation information (note geotiffs count down from top edge in Y)
      geotransform = (minX, res, 0, maxY, 0, -res)

      # load data in to geotiff object
      dst_ds = gdal.GetDriverByName('GTiff').Create(filename,self.nX,self.nY, 1, gdal.GDT_Float32)

      dst_ds.SetGeoTransform(geotransform)    # specify coords
      srs = osr.SpatialReference()            # establish encoding
      srs.ImportFromEPSG(3031)                # WGS84 lat/long
      dst_ds.SetProjection(srs.ExportToWkt()) # export coords to file
      dst_ds.GetRasterBand(1).WriteArray(self.imageArr)  # write image to the raster
      dst_ds.GetRasterBand(1).SetNoDataValue(np.nan)  # set no data value
      dst_ds.FlushCache()                     # write to disk
      dst_ds = None

      print("Image written to",filename)
      return


if __name__=="__main__":
    com = readCommands()

    start_time = time.time()
    #set time
    bd = singlelvis(filename=com.inName,onlyBounds=True)

    # set bounds (entire set in this example - but useful for subsetting in other cases)

    x0 = bd.bounds[0]
    y0 = bd.bounds[1]
    xlength = (bd.bounds[2]-bd.bounds[0])/20 #set steplength of x
    ylength = (bd.bounds[3]-bd.bounds[1])/20 #set steplength of y

    i=0 #set timer

    #use nest loop to print each part has data
    for x0 in np.arange(bd.bounds[0],bd.bounds[2],xlength):
        x1=x0+xlength


        for y0 in np.arange(bd.bounds[1],bd.bounds[3],ylength):
            y1=y0+ylength
            i+=1


            lvis = singlelvis(filename=com.inName,minX=x0,minY=y0,maxX=x1,maxY=y1)

            if lvis.region == 1:
                # finding the ground
                lvis.setElevations()
                lvis.estimateGround()
                lvis.CofG()
                lvis.reproject(inEPSG=com.inEPSG,outEPSG=com.outEPSG)

                # write out the elevation to a .tif
                lvis.writeSingleTiff(filename=str(i)+str(j)+com.outName,res=com.outRes)
                print("- %s seconds -" % (time.time() - start_time))
    #read all tif file
    demList = glob.glob("*.tif")
    #fitname = com.output.tif
    g = gdal.Warp("output.tif", demList, format="GTiff")
    g = None
