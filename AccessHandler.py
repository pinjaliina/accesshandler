# -*- coding: utf-8 -*-
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                               #
#  AccessHandler; process MetropAccess Helsinki Travel Time Matrix (MTTM) Files #
#                                                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# NOTE: this file is UTF-8 w/ UNIX line endings!                                #
# Written for Python 3.                                                         #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                             #
# This script is originally based on the final assignment                     #
# of the UH geography course 56279 "Automating GIS-processes" [sic].          #
# However, it no longer meets the original requirements of that course.       #
# (Also, the requirements might have changed on later course iterations.)     #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# Import the necessary modules.
import sys
import os
import tempfile
import re
import argparse
import pandas as pd
import geopandas as gpd

# Function implementing the requirement 1 of the assignment, ie. creating
# shapefiles corresponding to the given YKR_ID list. For the purporses of the
# assignment it can be instructed not to write out anything directly but return
# a list of GeoDataFrame objects instead. Note that this is not very memory
# efficient, but it would also be possible to write out the files and let
# timeDistCalc() to read them in again one by one. I've done it this way,
# because, as long as memory is no constraint, it's much faster than dumping
# shapefiles to disk and re-reading them, and it still preserves the
# two functions' independent usability.
# 
# About the params:
#
# * inshp is the MetropAccess project YKR grid visualisation shapefile.
# * indir is the directory containing the MTTM text files.
# * If outdir is false, the created shapefile objects are returned as a list
#   and the rest of the params are ignored.
# * If outdir is not false and ignoremissing is true, processing is continued
#   even if the idlist includes references to MTTM files that are not found.
#   The user is warned about this.
# * If outdir is not false and overwriteexisting is true, any existing
#   shapefiles are overwritten. The user is warned about this.
# * If outdir is not false and overwriteexisting is false, any existing
#   shapefiles are not overwritten, but the newly created data is discarded
#   instead. The user is warned about this.
# 
def createShapeFiles(inshp, indir, idlist, outdir=False, ignoremissing=True, overwriteexisting=True):

    # Validate the input params.
    try:
        if not isinstance(inshp, str):
            raise Exception
        if not os.path.isfile(inshp):
            raise Exception
    except Exception:
        print("ERROR: invalid createShapeFiles() input shapefile path!")
        sys.exit(1)
    try:
        if not isinstance(indir, str):
            raise Exception
        if not os.path.isdir(indir):
            raise Exception
    except Exception:
        print("ERROR: invalid createShapeFiles() input travel time matrix directory path!")
        sys.exit(1)
    try:
        if outdir and not isinstance(outdir, str):
            raise Exception
        if outdir and not os.path.isdir(outdir):
            raise Exception
    except Exception:
        print("ERROR: invalid createShapeFiles() output path!")
        sys.exit(1)
    try:
        if not isinstance(idlist, list):
            raise Exception
        for i in idlist:
            if not isinstance(i, int):
                raise Exception
    except Exception:
        print("ERROR: createShapeFiles() requires the fourth parameter to be a list of\ninteger values!")
        sys.exit(1)
    try:
        if not isinstance(ignoremissing, bool):
            raise Exception
    except Exception:
        print("ERROR: createShapeFiles() requires the fifth parameter to be boolean!")
        sys.exit(1)
    try:
        if not isinstance(overwriteexisting, bool):
            raise Exception
    except Exception:
        print("ERROR: createShapeFiles() requires the sixth parameter to be boolean!")
        sys.exit(1)

    # Create the shapefiles or GeoDataFrame objects.
    ykr = gpd.read_file(inshp)
    output = []
    fn_prefix = 'travel_times_to_'
    fn_suffix = '.txt'
    idlist_len = len(idlist)
    for key, gid in enumerate(idlist):
        print("Processing file \"" + fn_prefix + ' ' + str(gid) + fn_suffix + "\"... Progress: " + str(key+1) + "/" + str(idlist_len))
        # Try to find the file from the filesystem under the input directory:
        fn = fn_prefix + ' ' + str(gid) + fn_suffix
        fp = ''
        for root, dirs, files in os.walk(indir):
            for f in files:
                if f == fn:
                    fp = os.path.join(root, f)
        if len(fp) == 0 or not os.path.isfile(fp):
            if ignoremissing:
                print("WARNING: file \"" + fn + "\" not found from the input directory!")
            else:
                print("ERROR: file \"" + fp + "\" not found from the input directory!")
                sys.exit(1)
        else:
            ttmdata = pd.read_csv(fp, sep=';')
            # Join YKR_ID from the inshp attr table with the matrix file from_id.
            # Note that according to experience GeoDataFrame.to_file() often
            # fails, unless we explicitly create a new GeoDataFrame object from
            # the merged data.
            join = gpd.GeoDataFrame(ykr.merge(ttmdata, how='inner', left_on='YKR_ID', right_on='from_id'), geometry='geometry', crs=ykr.crs)
            # Drop unnecessary columns.
            join = join.drop(labels=['YKR_ID', 'x', 'y'], axis=1)
            # Save the data and note the filepath, if any outdir was given.
            ofp = ''
            if outdir:
                ofp = os.path.join(outdir,  fn_prefix + str(gid) + ".shp")
                isfile = os.path.isfile(ofp)
                if isfile:
                    if overwriteexisting:
                        print("WARNING: overwriting an existing file \"" + ofp + "\"!")
                    else:
                        print("WARNING: file \"" + ofp + "\" already exists! Failed to save the new file!")
                if overwriteexisting or not isfile:
                    join.to_file(ofp)
                    output.append(ofp)
            else:
                output.append(join)

    if outdir:
        print(str(len(output)) + " shapefile(s) written succesfully!")
    else:
        print(str(len(output)) + " input file(s) processed successfully!")
    # Return a list of the created filenames or objects.
    return(output)


# Function originally implementing the requirement 2 of the assignment,
# ie. calculating travel time or distance between two travel types, although
# no longer fully meeting its requirements. Function accepts either existing
# shapefiles or GeoDataFrame objects. For the general logic behind it, see
# the description of createShapeFiles().
#
# About the params:
# 
# * If indata is list of filenames and overwrite is true, the existing indata
#   shapefiles are overwritten.
# * If indata is a list of objects and overwrite is true, any existing output
#   files are overwritten.
# * If indata is a list of filenames and overwrite is false, new shapefiles are
#   created, if they don't exist. If they do, file is omitted.
# * If indata is a list of objects and overwrite is false, any existing files are
#   skipped.
# 
# We're not returning anything. In theory we could still just return the
# GeoDataFrame objects for further post-processing, but that would be rapidly
# getting beyond the scope of this assignment. That might be the most sensible
# point for further development here, though.
# 
def timeDistCalc(indata, travelmodes, outdir=False, overwrite=True):

    # Accept the following travel modes.
    accept_modes = ('walk_t','walk_d','pt_r_tt','pt_r_t','pt_r_d','pt_m_tt','pt_m_t','pt_m_d','car_r_t','car_r_d','car_m_t','car_m_d')
    # Validate the input params.
    try:
        if not isinstance(indata, list):
            raise Exception
        for i in indata:
            if not (isinstance(i, gpd.geodataframe.GeoDataFrame) or (isinstance(i, str) and os.path.isfile(i))):
                raise Exception
    except Exception:
        print("ERROR: timeDistCalc() requires the first parameter to be a list of existing\n"
              "shapefile paths or GeoDataFrame objects!")
        sys.exit(1)
    try:
        if not isinstance(travelmodes, list):
            raise Exception
        if not len(travelmodes) == 2:
            raise Exception
        for mode in travelmodes:
            if not isinstance(mode, str):
                raise Exception
            if not mode in accept_modes:
                raise Exception
        # Check that the modes are of the same type.
        mode0_suffix = re.search('[dt]{1}$', travelmodes[0]).group(0)
        mode1_suffix = re.search('[dt]{1}$', travelmodes[1]).group(0)
        if not ((mode0_suffix == 't' or mode0_suffix == 'd') and mode0_suffix == mode1_suffix):
            raise Exception
    except Exception:
        print("ERROR: timeDistCalc() requires the second parameter to be a list of the "
              "following options with length of two:\n" + ', '.join(accept_modes)
              + "\nBoth list values must be either of the time type or dist type."
              + "Both values cannot be the same.")
        sys.exit(1)
    try:
        if not outdir and not (overwrite and isinstance(indata[0], str) and os.path.isfile(indata[0])):
            raise Exception
    except Exception:
        print("ERROR: timeDistCalc() either requires the first parameter to be a list of existing\n"
              "shapefile names and overwrite to be true, or the outdir parameter to be set!")
        sys.exit(1)
    try:
        if not isinstance(overwrite, bool):
            raise Exception
    except Exception:
        print("ERROR: timeDistCalc() requires the fourth parameter to be boolean!")
        sys.exit(1)

    # Test, whether we're calculating times or distances.
    time = False
    if re.search('[dt]{1}$', travelmodes[0]).group(0) == 't':
        time = True
    # Save indata length.
    indata_len = len(indata)
    # Collect output filenames.
    output = []
    # Process through the input data.
    for key, value in enumerate(indata):
        # Find out, whether our input data are objects of filenames.
        shp = None
        if isinstance(value, gpd.geodataframe.GeoDataFrame):
            shp = value
        else:
            shp = gpd.read_file(value)
        # Create a new column to the shapefile attr table.
        shp['c_result'] = None
        # Set some filename-related vars.
        to_id = shp.ix[0, 'to_id'] # If we've no input files, we don't know this.
        fn_prefix = 'Accessibility_'
        fn_suffix = '_' + travelmodes[0] + '_vs_' + travelmodes[1] + '.shp'
        # Print some process information. It's actually delayed, because we don't know the to_id before the first
        # iteration, but this is hardly noticeable.
        if time:
            print("Calculating travel times to grid ID " + str(to_id) + "... Progress: " + str(key+1) + "/" + str(indata_len))
        else:
            print("Calculating distances to grid ID " + str(to_id) + "... Progress: " + str(key+1) + "/" + str(indata_len))
        # Iterate over attr table rows. This has to be done, because we have to
        # take the missing values (-1s) into account.
        for i, row in enumerate(shp.iterrows()): # I tried pd.itertuples, but couldn't get it to index the values as it should.
            # Assume that the result is -1 unless proven otherwise.
            result = -1
            # Calculate the result.
            if row[1][travelmodes[0]] != -1 and row[1][travelmodes[1]] != -1:
                result = row[1][travelmodes[0]]-row[1][travelmodes[1]]
            # Update the attr table cell.
            shp.set_value(i, 'c_result', result)
        # Write out the result according to the prefs given in our input vars.
        if overwrite and isinstance(value, str) and os.path.isfile(value):
            shp.to_file(value)
            output.append(value)
        elif overwrite and isinstance(value, gpd.geodataframe.GeoDataFrame):
            ofp = os.path.join(outdir, fn_prefix + str(to_id) + fn_suffix)
            if os.path.isfile(ofp):
                print("WARNING: overwriting an existing file \"" + ofp + "\"!")
            shp.to_file(ofp)
            output.append(ofp)
        elif not os.path.isfile(ofp):
            shp.to_file(ofp)
            output.append(ofp)
        else:
            print("WARNING: file \"" + ofp + "\" exists, not saving!")
    print(str(len(output)) + " shapefile(s) written succesfully!")

# Main program.
# 
# Positional arguments:
#  – input directory
#  – output directory
# Mandatory “optional” arguments:
#  – arbitrary number of YKR grid numbers.
# Truly optional arguments:
#  – input shapefile. Defaults to ./MetropAccess_YKR_grid/MetropAccess_YKR_grid_EurefFIN.shp
#  – travel modes

# Define a custom argparse action for checking for the valid travel types.
class valid_modes(argparse.Action):
    def __call__(self, parser, namespace, modes, option_string=None):
        # Define an exception handler to enable suppressing traceback:
        def exceptionHandler(exception_type, exception, traceback):
            print("{}: {}".format(exception_type.__name__, exception))
        
        modelist = ('walk_t','walk_d','pt_r_tt','pt_r_t','pt_r_d','pt_m_tt','pt_m_t','pt_m_d','car_r_t','car_r_d','car_m_t','car_m_d')
        
        # Check for valid mode types.
        for m in modes:
            if not m in modelist:
                parser.print_usage()
                sys.excepthook = exceptionHandler # Suppress traceback.
                raise argparse.ArgumentTypeError('Travel modes are of different types or of an invalid type!')
        
        # Check that the modes are of the same type.
        mode0_suffix = re.search('[dt]{1}$', modes[0]).group(0)
        mode1_suffix = re.search('[dt]{1}$', modes[1]).group(0)
        if ((mode0_suffix == 't' or mode0_suffix == 'd') and mode0_suffix == mode1_suffix):
            setattr(namespace, self.dest, modes)
        else:
            parser.print_usage()
            sys.excepthook = exceptionHandler # Suppress traceback.
            raise argparse.ArgumentTypeError('Travel modes are of different types or of an invalid type!')

# Define a custom argparse action for checking if the I/O directories exist.
class valid_dir(argparse.Action):
    def __call__(self, parser, namespace, dirname, option_string=None):
        # Define an exception handler to enable suppressing traceback:
        def exceptionHandler(exception_type, exception, traceback):
            print("{}: {}".format(exception_type.__name__, exception))
        
        if (os.path.isdir(dirname)):
            setattr(namespace, self.dest, dirname)
        else:
            parser.print_usage()
            sys.excepthook = exceptionHandler # Suppress traceback.
            raise argparse.ArgumentTypeError('Path ' + dirname + ' does not exist or is not a directory!')

# Create an argument parser and add arguments.
parser = argparse.ArgumentParser(description='Create shapefiles based on the MetropAccess Time Travel Matrix (MTTM).')
parser.add_argument('-g', '--gridnum', nargs='+', required=True, type=int, help='YKR grid ID numbers as used in the MetropAccess\nproject. At least one is mandatory.')
# NOTE: The following needs to change when this script will be converted to the 2015 version of the MTTM!
parser.add_argument('-m', '--mode', nargs=2, action=valid_modes, default=argparse.SUPPRESS, help='Travel modes, whose difference is to be calculated. They must be of the same type, thus, end with either "t" or "_d".')
parser.add_argument('-s', '--inshp', nargs=1, type=argparse.FileType('r'), default=os.getcwd() + os.sep + 'YKRGrid' + os.sep + 'MetropAccess_YKR_grid_EurefFIN.shp', help='Path of the YKR grid visualisation input shapefile from the MetropAccess project.\nDefault is current working directory + YKRGrid' + os.sep + 'MetropAccess_YKR_grid_EurefFIN.shp')
parser.add_argument('indir', action=valid_dir, help='Full path of the MTTM files input directory')
parser.add_argument('outdir', action=valid_dir, help='Full path of the directory where the created shapefiles are written to')
args = parser.parse_args()

# DEBUG:
#print(args.gridnum)
#if hasattr(args, 'mode'):
#   print(args.mode)
# args.inshp is a one-item list, if given, but an _io.TextIOWrapper object,
# if the default.
#if(isinstance(args.inshp, list)):
    #print(args.inshp[0].name)
#else:
    #print(args.inshp.name)
#print(args.indir)
#print(args.outdir)

# Assign some vars.
gridnums = args.gridnum
inshp = ''
if(isinstance(args.inshp, list)):
    inshp = args.inshp[0].name
else:
    inshp = args.inshp.name
indir = args.indir
outdir = args.outdir

# Do the real work.
if not hasattr(args, 'mode'):
    # FIXME: convert the last two arguments to this function to optional command line arguments.
    createShapeFiles(inshp, indir, gridnums, outdir, ignoremissing=True, overwriteexisting=True)
else:
    gdfobjects = createShapeFiles(inshp, indir, gridnums, outdir=False, ignoremissing=True)
    timeDistCalc(gdfobjects, args.mode, outdir)
