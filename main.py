#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is a program designed to take Candy Crush boards as input and 
    output a list of possible moves in order of effectiveness."""

# The boilerplate code for this project found here:
# https://gist.github.com/ssokolow/151572

__appname__ = "Candy Crush Solver"
__author__  = "Edward Williamson (nedw on Github)"
__version__ = "0.0pre0"
__license__ = "GNU GPL 3.0 or later"

import logging
log = logging.getLogger(__name__)

from CandyBoard import *

def main():
    board = CandyBoard("score",False) #second parameter runs tests
    board.autoInput() #DFS solving algorithm
    #board.liveInput() #testing individual swaps

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(description=__doc__,
        version="%%prog v%s" % __version__)
    parser.add_option('-v', '--verbose', action="count", dest="verbose",
        default=2,
        help="Increase the verbosity. Can be used twice for extra effect.")
    parser.add_option('-q', '--quiet', action="count", dest="quiet",
        default=0,
        help="Decrease the verbosity. Can be used twice for extra effect.")

    opts, args  = parser.parse_args()

    # Set up clean logging to stderr
    log_levels = [logging.CRITICAL, logging.ERROR, logging.WARNING,
                  logging.INFO, logging.DEBUG]
    opts.verbose = min(opts.verbose - opts.quiet, len(log_levels) - 1)
    opts.verbose = max(opts.verbose, 0)
    logging.basicConfig(level=log_levels[opts.verbose],
                        format='%(levelname)s: %(message)s')
    main()
