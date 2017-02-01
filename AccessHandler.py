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
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# Import the necessary modules.
import sys
import os
import tempfile
import re
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
    fn_prefix = 'time_to_' # Assignment suggest that this is "travel_times_to_", but that doesn't seem to be the case.
    fn_suffix = '.txt'
    idlist_len = len(idlist)
    for key, gid in enumerate(idlist):
        fp = os.path.join(indir, fn_prefix + str(gid) + fn_suffix)
        print("Processing file \"" + fn_prefix + str(gid) + fn_suffix + "\"... Progress: " + str(key+1) + "/" + str(idlist_len))
        if not os.path.isfile(fp):
            if ignoremissing:
                print("WARNING: file \"" + fp + "\" does not exist!")
            else:
                print("ERROR: file \"" + fp + "\" does not exist!")
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


# Function implementing the requirement 2 of the assignment, ie. calculating
# travel time or distance between two travel types. Function accepts either
# existing shapefiles or GeoDataFrame objects. For the general logic behind
# it, see the description of createShapeFiles().
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
# * accept_modes by default include all the modes available in the MTTM files.
# 
# We're not returning anything. In theory we could still just return the
# GeoDataFrame objects for further post-processing, but that would be rapidly
# getting beyond the scope of this assignment. That might be the most sensible
# point for further development here, though.
# 
def timeDistCalc(indata, travelmodes, outdir=False, overwrite=True, accept_modes = ['Walk_time', 'Walk_dist', 'PT_total_time', 'PT_time', 'PT_dist', 'Car_time', 'Car_dist']):

    # Default modes. Same as the accept_modes, if nothing else was given.
    default_accept_modes = ['Walk_time', 'Walk_dist', 'PT_total_time', 'PT_time', 'PT_dist', 'Car_time', 'Car_dist']
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
        if not isinstance(accept_modes, list):
            raise Exception
        if not len(accept_modes) > 1:
            raise Exception
        for mode in accept_modes:
            if not isinstance(mode, str):
                raise Exception
            if not mode in default_accept_modes:
                raise Exception
    except Exception:
        print("ERROR: timeDistCalc() requires the fifth parameter to be a list including some "
              "or all of the following options:\n" + ', '.join(default_accept_modes)
              + "\nAt least two are required.")
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
        if not (
            (travelmodes[0].find('time') != -1 and travelmodes[1].find('time') != -1)
            or (travelmodes[0].find('dist') != -1 and travelmodes[1].find('dist') != -1)
            or (travelmodes[0] != travelmodes[1])
            ):
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
    if travelmodes[0].find('time') != -1:
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
        shp['Time_Dist'] = None
        # Set some filename-related vars.
        to_id = shp.ix[0, 'to_id'] # Iif we've no input files, we don't know this.
        fn_prefix = 'Accessibility_'
        # split() would be difficult here if we've multiple underscores, like in
        # PT_total_time. For once, regex greediness is useful. The following
        # should do exactly what we want, i.e. break the string from
        # the _last_ underscore:
        fn_suffix = '_' + re.search('^[\w]+_', travelmodes[0]).group().strip('_') + '_vs_' + re.search('^[\w]+_', travelmodes[1]).group().strip('_') + '.shp'
        # Print some process information. It's actually delayed, because we don't know the to_id before the first
        # iteration, but this is hardly noticeable
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
            shp.set_value(i, 'Time_Dist', result)
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

# Print the general usage message from a separate function. This
# eases up error control in the main program.
#
def usage(modes, progname = 'accesshandler.py', exitcode = 1):
    
    # Validate the input params.
    try:
        if not isinstance(modes, list):
            raise Exception
        for mode in modes:
            if not isinstance(mode, str):
                raise Exception
    except Exception:
        print("WARNING: No list of travel modes given, normal error reporting unavailable!")
        pass
    print("\nCreate shapefiles based on the MetropAccess Time Travel Matrix (MTTM).\n\n"
          "For details, see:\n"
          "http://blogs.helsinki.fi/accessibility/data/metropaccess-travel-time-matrix/\n\n"
          "Usage: " + progname + " gridnum1 [gridnum2] \\\n"
          "       ... [gridnumN] ([tmode1] [tmode2]) outdir [inshp] [indir]\n\n"
          "Where:\n"
          "    - gridnum1...gridnumN are YKR grid ID numbers as used in the MetropAccess\n"
          "      project. At least one is mandatory.\n"
          "    - tmode1 and tmode2 are travel mode field names as used in the MTTM\n"
          "      data files:\n"
          "          * If one is given, the other is mandatory.\n"
          "          * Both has to be the same \"type\", i.e. their names have to end\n"
          "            either \"time\" or \"dist\".\n"
          "          * If none are given, no travel mode comparisons are done.\n"
          "          * Calculation is done by subtracting the value of the second field\n"
          "            from the first. If either is empty, the result is -1. Results are\n"
          "            written to Time_Dist fields of the attribute tables of the created\n"
          "            shapefiles.\n"
          "          * Depending of the program version, available modes may vary.\n"
          "            They are:\n"
          "            " + ', '.join(modes) + "\n"
          "    - outdir is the directory where the shapefiles are written. This argument\n"
          "      is mandatory.\n"
          "    - inshp is the full path of the YKR grid visualisation input shapefile from\n"
          "      the MetropAccess project. If it's omitted, it is expected to be found from\n"
          "      %TMPDIR%" + os.sep + 'MetropAccess_YKR_grid' + os.sep + 'MetropAccess_YKR_grid_EurefFIN.shp' + ".\n"
          "    - indir is the full path of the directory containing the MTTM grid files.\n"
          "      The file names must be in the same format as when downloaded from the\n"
          "      project page (eg. time_to_0000000.txt).\n"
          "      If omitted, %TMPDIR%" + os.sep + "MTTM is used, but the path must exist!"
          "\n")
    sys.exit(exitcode)
            
# Main program. The assignment called for only three params, but we very
# obviously also want to ask the user for the location of the input
# shapefile and the input MTTM files. However, because only three params
# were requested, the input paths DO have default values; they're expected
# to be the following:
#
# Input shapefile: tempfile.gettempdir()/MetropAccess_YKR_grid/MetropAccess_YKR_grid_EurefFIN.shp
# Input MTTM files: tempfile.gettempdir()/MTTM
#
# Note that these do not necessarily make much sense, as eg. in my own setup
# on OS X gettempdir() returns "/var/folders/kj/8zwtv0g163725wk62p76g01c0000gp/T",
# which is definitely not a directory that a user would accidentially use.
#
# I made a futile attempt to use the argparse module, but it didn't really work,
# or I didn't have enough time to test it. Basically, the problem is that we've
# to loop through sys.argv and check that all the params in the beginning are
# integers... and if some of them are not, then we'll have to assume that they
# are travel modes or filenames.
# 
progname = sys.argv[0]
# The assignment asks for Car_time & Car_dist travel modes to be excluded; I see
# no sensible reason for this, so the default for timeDistCalc() includes them,
# but that default is overwritten here, so as to meet the requirements of the
# assignment. I will NOT enable overwriting it from the command line, though...
allow_modes = ['Walk_time', 'Walk_dist', 'PT_total_time', 'PT_time', 'PT_dist']
# If help is requested, give it!
if sys.argv[1] == 'help' or sys.argv[1] == '-help' or sys.argv[1] == '--help' or sys.argv[1] == '-h':
    usage(allow_modes, progname)
# Iterate over sys.argv and try to create sensible lists from the arguments.
gridnums = []
tmodes = []
paths = []
for key, value in enumerate(sys.argv):
    if key > 0:
        try:
            gridnum = int(value)
            gridnums.append(gridnum)
        except ValueError:
            pass
        try:
            if len(tmodes) == 0 and value in allow_modes:
                tmodes.append(value)
            if len(tmodes) == 1 and value in allow_modes and (
                (tmodes[0].find('time') != -1 and value.find('time') != -1) or
                (tmodes[0].find('dist') != -1 and value.find('dist') != -1)
                ) and value != tmodes[0]:
                tmodes.append(value)
        except Exception:
            pass
        try:
            if len(paths) < 3 and isinstance(value, str):
                # If the user forgets the output path but gives both input
                # filenames, we may be tricked to think that sys.argv[-1]
                # is our real output path. Check sys.argv[-2] and sys.argv[-3]
                # to be sure!
                if len(paths) == 0 and os.path.isdir(value) and (not os.path.isfile(sys.argv[-2]) or os.path.isdir(sys.argv[-3])):
                    paths.append(value)
                if len(paths) == 1 and os.path.isfile(value):
                    paths.append(value)
                if len(paths) > 0 and len(paths) < 3 and value != paths[0] and os.path.isdir(value):
                    paths.append(value)
        except Exception:
            pass
# Test the arguments. Print a usage message unless we pass.
#print(str(len(gridnums)) + str(len(tmodes)) + str(len(paths))) # DEBUG!!!
if len(gridnums) > 0 and (len(tmodes) == 0 or len(tmodes) == 2) and len(paths) > 0:
    outdir = paths[0]
    inshp = None
    indir = None
    if len(paths) == 2 and os.path.isdir(paths[1]):
        indir = paths[1]
    elif len(paths) == 2 and os.path.isfile(paths[1]):
        inshp = paths[1]
    elif len(paths) == 3:
        inshp = paths[1]
        indir = paths[2]
    if not (inshp and indir):
        tmpdir = tempfile.gettempdir()
        if not inshp:
            inshp = os.path.join(tmpdir, 'MetropAccess_YKR_grid', 'MetropAccess_YKR_grid_EurefFIN.shp')
        if not indir:
            indir = os.path.join(tmpdir, 'MTTM')
    try:
        if not os.path.isfile(inshp):
            raise FileNotFoundError
        if not os.path.isdir(indir):
            raise FileNotFoundError
    except FileNotFoundError:
        print("ERROR: an input file or directory is not found!")
        usage(allow_modes, progname)
    if len(tmodes) == 0:
        createShapeFiles(inshp, indir, gridnums, outdir, ignoremissing=True, overwriteexisting=True)
    else:
        gdfobjects = createShapeFiles(inshp, indir, gridnums, outdir=False, ignoremissing=True)
        timeDistCalc(gdfobjects, tmodes, outdir, accept_modes=allow_modes)
else:
    try:
        if len(paths) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print("ERROR: output directory is not found!")
        usage(allow_modes, progname)
    usage(allow_modes, progname)


        


