# Create Shapefiles and Compare Travel Times Using MetropAccess Helsinki Travel Time Matrix

This is a Python tool that can be used to create shapefiles and compare travel times using the [Helsinki Region Travel Time Matrix](http://blogs.helsinki.fi/accessibility/helsinki-region-travel-time-matrix/) of the University of Helsinki MetropAccess project.

I originally created this as a final assignment of the course “Automating GIS Processes” in the autumn 2015, but realised later on that I might actually need to reuse this code or some parts of it in the future, so I decided to publish it in GitHub for the pleasure of everyone.

The most useful part of the code are the functions ```createShapeFiles()``` and ```timeDistCalc()```, but there is also a main program to use them from the command line. Virtually no part of the code any longer adheres to what were the original course requirements back then.

If you still need support for the orginal year [2013 MetropAccess Travel Time Matrix](http://blogs.helsinki.fi/accessibility/data/metropaccess-travel-time-matrix/) with the old column names, please checkout the [M2013_old-column-names](https://github.com/pinjaliina/accesshandler/tree/M2013_old-column-names) branch; the current version expects the new column and file name structure of the newer [2013](http://blogs.helsinki.fi/accessibility/helsinki-region-travel-time-matrix-2013/) and [2015](http://blogs.helsinki.fi/accessibility/helsinki-region-travel-time-matrix-2015/) versions of the matrices.

I've included the instructions of the assignment in the repository for clarity: see [AutoGIS15_FinalAssignment.html](AutoGIS15_FinalAssignment.html) ([or try rawgit to see it formatted](https://rawgit.com/pinjaliina/accesshandler/master/AutoGIS15_FinalAssignment.html)). However, if [@HTenkanen](https://github.com/htenkanen) wants me to take it off, he has but to tell me so! If you clone this repo, please delete that file from your clone!
