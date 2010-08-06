__version__ = '0.1.1~xml.4'
__author__ = 'John Paulett; Luke Leighton'
__email__ = 'john -at- 7oars.com; lkcl@lkcl.net'
__license__ = 'BSD'
__copyright__ = """Copyright 2009, John Paulett <john -at- 7oars.com>
Copyright (C) 2010, Luke Kenneth Casson Leighton <lkcl@lkcl.net>"""
# oops, has to be http://github.com/lkcl/hl7 for now until john merges/maintains
#__url__ = 'http://www.bitbucket.org/johnpaulett/python-hl7/wiki/Home'
__url__ = 'http://github.com/lkcl/hl7'

from hl7 import *
import segments21
import segments22
import segments23
import segments231
import segments24
import segments25
segment_revs = {'2.1': segments21,
                    '2.2': segments22,
                    '2.3': segments23,
                    '2.31': segments231,
                    '2.4': segments24,
                    '2.5': segments25,
                   }

