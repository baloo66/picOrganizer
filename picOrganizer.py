# ----------------------
# picOrganizer
# ----------------------
# reads all jpg/jpeg files from on directory and copies/moves them into a target directory 
# structure created by file dates     <targetpath>/year/month/day/<filename>
# the date is extracted from EXIF file information (EXIF, GPS, Image) or at least
# the file creation date

#
# Python Standard Library
import argparse
import datetime
import time
import shutil
import os
import sys

#
# additional libraries from Python Package Index
import exifread # pip install ExifRead



#
# tag2timestamp - converts an EXIFs tag timestamp value to a timestamp
# --------------------------------------------------------------------
# tsString - the EXIFs tag timestamp value as string
# --------------------------------------------------------------------
# returns  - a timestamp with the converted value or None if ther 
#            is an error
# --------------------------------------------------------------------
def tag2timestamp(tsString):
    timestamp = None
    if len(tsString) == 19:
        try:
            timestamp = datetime.datetime.strptime(tsString, "%Y:%m:%d %H:%M:%S")
        except:
            try:
                timestamp = datetime.datetime.strptime(tsString, "%Y-%m-%d %H:%M:%S")
            except:
                timestemp = None
    elif len(tsString) == 25:
        timestamp = datetime.datetime.strptime(tsString, "%Y-%m-%dT%H:%M:%S%z")
    return timestamp



#
# do1file  - try to read EXIF information from file and retrieve timestamp of creation
# ------------------------------------------------------------------------------------
# f2w      - filename to get timestamp from
# ------------------------------------------------------------------------------------
# returns  - the filename and the timestamp
# ------------------------------------------------------------------------------------
def do1file(f2w):
    # open file, reade EXIF header and close file
    f2w_fd = open(f2w, 'rb')
    tags = exifread.process_file(f2w_fd)
    f2w_fd.close

    # get timestamp with fallbacks EXIF -> GPS -> Image
    timestamp = None
    if tags:
        tag = tags.get('EXIF DateTimeOriginal') # the master timestamp
        if tag:
            timestamp = tag2timestamp(str(tag))
        else:
            tag = tags.get('EXIF DateTimeDigitized') # the backup, if there is no master
            if tag:
                timestamp = tag2timestamp(str(tag))
            else:
                tag = tags.get('GPS GPSDate') # GPS both parts must be present
                if tag:
                    ts = str(tag).replace(':', '-', 2)
                    tag = tags.get('GPS GPSTimeStamp')
                    if tag:
                        ts = ts + f' {tag.values[0]}:{tag.values[1]}:{tag.values[2]}'
                        timestamp = tag2timestamp(ts)
                    else:
                        timestamp = None
                if timestamp is None: # ok, maybe from the image
                    tag = tags.get('Image DateTime')
                    if tag:
                        timestamp = tag2timestamp(str(tag))
    # last chance - filesystem
    if timestamp is None:
        fs = os.stat(f2w)
        if fs:
            timestamp = (datetime.datetime.fromtimestamp(fs.st_ctime)).replace(microsecond=0)
    return f2w, timestamp



#
# cvt2path - create the target path depending on the timestamp
# ------------------------------------------------------------
# tgtPath  - target path
# fName    - bare filename
# ts       - timestamp to use
# ------------------------------------------------------------
# returns  - the full qualified target filename with path
# ------------------------------------------------------------
def cvt2path(tgtPath, fName, ts):
    return f'{tgtPath}{os.path.sep}{ts.year:04}{os.path.sep}{ts.month:02}{os.path.sep}{ts.day:02}{os.path.sep}{os.path.basename(fName)}'



#
# uniquefy - assure a unique filename; maybe the filename has to be
#            extended with a running number
# -----------------------------------------------------------------
# dstFile  - file to assure uniqueness
# -----------------------------------------------------------------
# returns  - a unique filename
# -----------------------------------------------------------------
def uniquefy(dstFile):
    dstPath = os.path.dirname(dstFile)
    if os.path.isdir(dstPath) and not(os.path.islink(dstPath)):
        pp = os.path.dirname(dstFile)
        pf, pe = os.path.splitext(os.path.basename(dstFile))
        dstFile = os.path.join(pp, f'{pf}{pe}')
        cnt = 0
        while os.path.isfile(dstFile):
            dstFile = os.path.join(pp, f'{pf}-{cnt:04}{pe}')
            cnt = cnt + 1
    else:
        os.makedirs(dstPath)
    return dstFile



#
# handleFile - work on one file and copy/move it
# ----------------------------------------------
# tgtPath    - where to store the file
# fname      - the filename
# moveFile   - True is moving, False is copying
# ----------------------------------------------
# returns    - nothing
# ----------------------------------------------
def handleFile(tgtPath, fname, moveFile):
    srcFile, ts = do1file(fname)
    if not ts is None:
        dstFile = uniquefy(cvt2path(tgtPath, fname, ts))
        if not moveFile:
            print(f'copying {srcFile}\t->\t{dstFile}')
            shutil.copyfile(srcFile, dstFile)
        else:
            print(f'moving {srcFile}\t->\t{dstFile}')
            shutil.move(srcFile, dstFile)
    else:
        print("ERROR no timestamp for [" + fname + "]")





if __name__ == '__main__':

    # setup argument parser
    moveFile = False
    srcPath = ""
    dstPath = ""
    parser = argparse.ArgumentParser(description='picture re-organizer...')
    parser.add_argument('--src', action='store', dest='srcPath', required=True, help='source path - where all the images are located')
    parser.add_argument('--dst', action='store', dest='dstPath', required=True, help='destination path - where all the images are meant to be')
    parser.add_argument('--move', action='store_true', dest='moveFile', help='if provided, move files instead of copying them')
    args = parser.parse_args()

    # show arguments and request continuation
    print("\n\n\n-------------------------------")
    print("picOrganizer - 2020 - aeller")
    print("-------------------------------")
    print(f'source\t{args.srcPath}')
    print(f'target\t{args.dstPath}')
    print(f'files\tare {("moved" if args.moveFile else "copied")}')
    print("-------------------------------")
    choice = input('continue? [Y/n]').lower()
    if choice in { 'yes', 'y', 'ye', '' }:

        # go on - first check parameters
        error = False
        if not os.path.isdir(args.srcPath):
            print(f'\nERROR: {args.srcPath} is no existing directory')
            error = True
        if not os.path.isdir(args.dstPath):
            print(f'\nERROR: {args.dstPath} is no existing directory')
            error = True
        
        if not error:
            start = time.time()
            # everything ok, so start and collect all image files
            fnames = []
            for root,d_names,f_names in os.walk(args.srcPath):
                for f in f_names:
                    if ((f.lower().endswith('.jpg')) or (f.lower().endswith('.jpeg'))):
                        fnames.append(os.path.join(root, f))
            print(f'... {len(fnames)} to process ...')
            # work/act on each file
            for fname in fnames:
                handleFile(args.dstPath, fname, args.moveFile)
            end = time.time()
            print(f'... finished after {(end-start)} seconds')
    else:
        print('\nthen - so long and farewell ...')