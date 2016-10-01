# Create Shapefiles and Compare Travel Times Using MetropAccess Helsinki Travel Time Matrix

This is a Python tool that can be used to create shapefiles and compare travel times using the [Helsinki Region Travel Time Matrix](http://blogs.helsinki.fi/accessibility/helsinki-region-travel-time-matrix/) of the University of Helsinki MetropAccess project.

I created this as a final assignment of the course “Automating GIS Processes” in the autumn 2015, but realised later on that I might actually need this code or some parts of it in the future, so I decided to publish it in GitHub.

The most useful part of the code are the functions ```createShapeFiles()``` and ```timeDistCalc()```; the main program is quite idiotic due to some really silly command line argument requirements (that thwarted any attempts to use ```argparse```. The main program is really in need of serious rewriting…

I've included the instructions of the assignment in the repository for clarity: see AutoGIS15_FinalAssignment.html. However, if [@HTenkanen](https://github.com/htenkanen) wants me to take it off, he has to only tell me so!

For known bugs, see issues.
