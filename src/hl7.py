# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 John Paulett (john -at- 7oars.com)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""Simple library for parsing messages of Health Level 7 (HL7)
version 2.x. 

HL7 is a communication protocol and message format for 
health care data. It is the de facto standard for transmitting data
between clinical information systems and between clinical devices.
The version 2.x series, which is often is a pipe delimited format
is currently the most widely accepted version of HL7 (version 3.0
is an XML-based format).

python-hl7 currently only parses HL7 version 2.x messages into
an easy to access data structure. The current implementation
does not completely follow the HL7 specification, but is good enough
to parse the most commonly seen HL7 messages. The library could 
potentially evolve into being fully complainant with the spec.
The library could eventually also contain the ability to create
HL7 v2.x messages.

python-hl7 parses HL7 into a series of wrapped hl7.Container objects.
The there are specific subclasses of hl7.Container depending on
the part of the HL7 message. The hl7.Container message itself
is a subclass of a Python list, thus we can easily access the
HL7 message as an n-dimensional list. Specically, the subclasses of
hl7.Container, in order, are hl7.Message, hl7.Segment, and hl7.Field.
Eventually additional containers will be added to fully support
the HL7 specification.

As an example, let's create a HL7 message:

>>> message = 'MSH|^~\&|GHH LAB|ELAB-3|GHH OE|BLDG4|200202150930||ORU^R01|CNTRL-3456|P|2.4\r'
>>> message += 'PID|||555-44-4444||EVERYWOMAN^EVE^E^^^^L|JONES|196203520|F|||153 FERNWOOD DR.^^STATESVILLE^OH^35292||(206)3345232|(206)752-121||||AC555444444||67-A4335^OH^20030520\r'
>>> message += 'OBR|1|845439^GHH OE|1045813^GHH LAB|1554-5^GLUCOSE|||200202150730||||||||555-55-5555^PRIMARY^PATRICIA P^^^^MD^^LEVEL SEVEN HEALTHCARE, INC.|||||||||F||||||444-44-4444^HIPPOCRATES^HOWARD H^^^^MD\r'
>>> message += 'OBX|1|SN|1554-5^GLUCOSE^POST 12H CFST:MCNC:PT:SER/PLAS:QN||^182|mg/dl|70_105|H|||F\r'

We call the `hl7.parse()` command with string message:

>>> h = parse(message)

We get a hl7.Message object, wrapping a series of hl7.Segment
objects.

>>> type(h)
<class 'hl7.Message'>

We can always get the HL7 message back.

>>> str(h) == message.strip()
True

Interestingly, this hl7.Message can be accessed as a list.

>>> isinstance(h, list)
True

There were 4 segments (MSH, PID, OBR, OBX):

>>> len(h)
4

We can extract the hl7.Segment from the hl7.Message instance.

>>> h[3]
[['OBX'], ['1'], ['SN'], ['1554-5', 'GLUCOSE', 'POST 12H CFST:MCNC:PT:SER/PLAS:QN'], [''], ['', '182'], ['mg/dl'], ['70_105'], ['H'], [''], [''], ['F']]

We can easily reconstitute this segment as HL7, using the
appopriate separators.

>>> str(h[3])
'OBX|1|SN|1554-5^GLUCOSE^POST 12H CFST:MCNC:PT:SER/PLAS:QN||^182|mg/dl|70_105|H|||F'

We can extract individual elements of the message:

>>> h[3][3][1]
'GLUCOSE'
>>> h[3][5][1]
'182'

We can look up segments by the segment identifer:

>>> pid = segment('PID', h)
>>> pid[3][0]
'555-44-4444'


Project site: http://www.bitbucket.org/johnpaulett/python-hl7/wiki/Home

HL7 References:
 * http://en.wikipedia.org/wiki/HL7
 * http://nule.org/wp/?page_id=99
 * http://www.hl7.org/
 * http://openmrs.org/wiki/HL7
 * http://comstock-software.com/blogs/ifaces/2007/01/hl7-message-wrappers.html 
"""

__version__ = '0.1.1~xml.1'
__author__ = 'John Paulett, Luke Leighton'
__email__ = 'john -at- 7oars.com, lkcl@lkcl.net'
__license__ = 'BSD'
__copyright__ = """Copyright 2009, John Paulett <john -at- 7oars.com>
Copyright (C) 2010, Luke Kenneth Casson Leighton <lkcl@lkcl.net>"""
__url__ = 'http://www.bitbucket.org/johnpaulett/python-hl7/wiki/Home'

from datetime import datetime
import sys, string
import pprint

from xml.sax import saxutils, handler, make_parser


def ishl7(line):
    """Determines whether a *line* looks like an HL7 message.
    This method only does a cursory check and does not fully 
    validate the message.
    """
    ## Prevent issues if the line is empty
    return line.strip().startswith('MSH') if line else False

def segment(segment_id, message):
    """Gets the first segment with the *segment_id* from the parsed *message*.

    >>> segment('OBX', [[['OBR'],['1']], [['OBX'], ['1']], [['OBX'], ['2']]])
    [['OBX'], ['1']]
    """
    ## Get the list of all the segments and pull out the first one if possible
    match = segments(segment_id, message)
    ## Make sure we won't get an IndexError
    return match[0] if match else None
    
def segments(segment_id, message):
    """Returns the requested segments from the parsed *message* that are identified
    by the *segment_id* (e.g. OBR, MSH, ORC, OBX).
    
    >>> segments('OBX', [[['OBR'], ['1']], [['OBX'], ['1']], [['OBX'], ['2']]])
    [[['OBX'], ['1']], [['OBX'], ['2']]]
    """
    ## Compare segment_id to the very first string in each segment, returning
    ## all segments that match
    return [segment for segment in message if segment[0][0] == segment_id]

def parse(line):
    """Returns a instance of the Message class that allows indexed access
    to the data elements. 

    >>> message = 'MSH|^~\&|GHH LAB|ELAB-3|'
    >>> h = parse(message)
    >>> str(h) == message
    True
    """
    ## Strip out unnecessary whitespace
    strmsg = line.strip()
    ## The method for parsing the message
    plan = create_parse_plan(strmsg)
    ## Start spliting the methods based upon the ParsePlan
    return _split(strmsg, plan)

def _split(text, plan):
    """Recursive function to split the *text* into an n-deep list,
    according to the :cls:`hl7._ParsePlan`. 
    """
    ## Base condition, if we have used up all the plans
    if not plan:
        return text
    
    ## Recurse so that the sub plans are used in order to split the data
    ## into the approriate type as defined by the current plan.
    data = [_split(x, plan.next()) for x in text.split(plan.separator)]
    ## Return the instance of the current message part according
    ## to the plan
    return plan.container(data)

class Container(list):
    """Abstract root class for the parts of the HL7 message."""
    def __init__(self, separator, sequence=[]):
        ## Initialize the list object, optionally passing in the
        ## sequence.  Since list([]) == [], using the default
        ## parameter will not cause any issues.
        super(Container, self).__init__(sequence)
        self.separator = separator            
    
    def __str__(self):
        ## Join a the child containers into a single string, separated
        ## by the self.separator.  This method acts recursively, calling
        ## the children's __str__ method.  Thus str() is the approriate
        ## method for turning the python-hl7 representation of HL7 into
        ## a standard string
        return self.separator.join((str(x) for x in self))
    
class Message(Container):
    """Representation of an HL7 message. It contains a list
    of :cls:`hl7.Segment` instances.
    """
    def __getitem__(self, key):
        res = []
        for i in self:
            #print type(i), type(i[0]), repr(i[0]), repr(key)
            if i[0][0] == unicode(key):
                res.append(i)
        if len(res) == 0:
            raise KeyError, "key %s not found in Message" % key
        return res

class Segment(Container):
    """Second level of an HL7 message, which represents an HL7 Segment.
    Traditionally this is a line of a message that ends with a carriage
    return and is separated by pipes. It contains a list of
    :cls:`hl7.Field` instances.
    """

class Field(Container):
    """Third level of an HL7 message, that traditionally is surrounded
    by pipes and separated by carets. It contains a list of strings.
    """
   
def create_parse_plan(strmsg):
    """Creates a plan on how to parse the HL7 message according to
    the details stored within the message.
    """
    ## We will always use a carriage return to separate segments
    separators = ['\n']
    ## Parse out the other separators from the characters following
    ## MSH.  Currently we only go two-levels deep and ignore some
    ## details.
    separators.extend(list(strmsg[3:5]))
    ## The ordered list of containers to create
    containers = [Message, Segment, Field]
    return _ParsePlan(separators, containers)
    
class _ParsePlan(object):
    """Details on how to parse an HL7 message. Typically this object
    should be created via :func:`hl7.create_parse_plan`
    """
    # field, component, repetition, escape, subcomponent
    # TODO implement escape, and subcomponent

    def __init__(self, separators, containers):
        # TODO test to see performance implications of the assertion
        # since we generate the ParsePlan, this should never be in
        # invalid state
        assert len(containers) == len(separators)
        self.separators = separators
        self.containers = containers
        
    @property
    def separator(self):
        """Return the current separator to use based on the plan."""
        return self.separators[0]

    def container(self, data):
        """Return an instance of the approriate container for the *data*
        as specified by the current plan.
        """
        return self.containers[0](self.separator, data)
    
    def next(self):
        """Generate the next level of the plan (essentially generates
        a copy of this plan with the level of the container and the
        seperator starting at the next index.
        """
        if len(self.containers) > 1:
            ## Return a new instance of this class using the tails of
            ## the separators and containers lists. Use self.__class__()
            ## in case :cls:`hl7.ParsePlan` is subclassed
            return  self.__class__(self.separators[1:], self.containers[1:])
        ## When we have no separators and containers left, return None,
        ## which indicates that we have nothing further.
        return None


def datetransform(obj, data, dt):
    args = [dt[:4], dt[4:6], dt[6:8]]
    if len(dt) > 8:
        args.append(dt[8:10])
    if len(dt) > 10:
        args.append(dt[10:12])
    if len(dt) > 12:
        args.append(dt[12:14])
    args = tuple(map(int, args))
    return datetime(*args)


class TIter:
    def __init__(self, d):
        self.cls = d.__class__
        self.i = d.data.__iter__()
    def __iter__(self):
        return self
    def next(self):
        data = self.i.next()
        return self.cls(data)


class Transform:
    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return TIter(self).__iter__()

    def __getitem__(self, key):
        if isinstance(key, int):
            if key > len(self.data):
                return None
            return self.fieldcheck(self.data[key])
        return self.__class__(self.data[key])

    def __getattr__(self, key):
        if isinstance(key, int):
            if key > len(self.data):
                return None
            return self.fieldcheck(self.data[key])
        tf = self.transform[key]
        idx = tf[0]
        typ = tf[1]
        if idx >= len(self.data):
            return None
        val = self.fieldcheck(self.data[idx])
        if typ and val is not None:
            val = typ(self, self.data, val)
        return val

    def fieldcheck(self, val):
        if len(val) == 0:
            return None
        if len(val) == 1:
            if val[0] == u'':
                return None
            return val[0]
        return val
    

class cPID(Transform):
    """
   PID 002 (External patient ID / BC Personal Health Number [PHN] if known)
       -> other_info
   PID 003 ( Addn Patient ID / Additional Patient Identifier; MRN nonunique)
       -> ? concatenate into other_info using internal delimiter ^ ?
   PID 004 (Alternate External Patient ID / e.g. Chart number)
   PID 005 (Patient Name / Last^First^Middle (as supplied))
       -> substring1 into lastnames
       -> concatenate substrings2,3 into firstnames (space-delimited)
   PID 007 (Date of Birth YYYYMMDD (null if unknown))
       -> dob
   PID 013 (Home Phone / May be partial and irregularly formatted)
       -> ? concatenate into other_info using internal delimiter ^ ?
   PID 008 (Sex / Gender of patient F/M/U-unknown) -> gender

    """
    transform = {'idx': (1, None),
                 'ext_id': (2, None),
                 'id': (3, None),
                 'dob': (7, datetransform),
                 'name': (5, None),
                 'address': (11, None),
                 'alt_id': (4, None),
                 'gender': (8, None),
                 'tel': (13, None),
                }


class cORC(Transform):
    """ ORC 004      Placer Group Number / External Order ID     request_id
        ORC 003 (Filler Order Number / Order Number ID) of
                lab performing tests / Accession number-test code-tiebreaker
    """
    transform = {'request_id': (4, None),
                 'order_id': (3, None),
                 'provider': (12, None),
                }


def typetrans(obj, data, val):
    if val == u'NM':
        return float
    elif val == u'DT' or val == u'TM': # date
        return lambda x: datetransform(None, None, x)
    elif val == u'TX': # text
        return unicode
    elif val == u'ST': # same as string (geez)
        return unicode
    elif val == u'FT': # formatted text: TODO - format it.  duh.
        return unicode
    elif val == u'CE': # coded element
        return lambda x:x
    raise KeyError, "OBX 002 unrecognised value type '%s' on %s" % \
                (val, repr(data))


def obxrestrans(obj, data, val):
    return obj.valuetype(val)


class cOBX(Transform):
    """
    integer?    OBX 001 index?
                OBX 004 (Observation Sub ID)
    val_num      HL7 OBX 005 (Result)    if OBX 002 (Value Type) == NM
    val_alpha   HL7 OBX 005 (Result)    if OBX 002 (Value Type) == FT
    val_unit    HL7 OBX 006 "Units"      
    val_normal_range    OBX 007 (Reference Range)    
    abnormality_indicator   OBX 008 (Abnormal Flags)     
    note_provider   OBX NTE 003 (Comment)   to be renamed note_test_org
    """
    transform = {'result': (5, obxrestrans),
                 'valuetype': (2, typetrans),
                 'sub_id': (4, None),
                 'idx': (1, None),
                 'units': (6, None),
                 'range': (7, None),
                 'abnormal': (8, None),
                 'comment': (3, None),
                }


class cOBR(Transform):
    """
    OBR 001 index?
    OBR 007 (Observation Date-Time)
    OBR 014 (Specimen received Date timestamp),
    OBR 022 (Report Status Change timestamp),
    028 (Result Copies To),
    OBR 025 (Result Status), 
    OBR 024 "Diagnostic Service Section" 
    """
    transform = {'specimen_recv': (14, datetransform),
                 'results_reported_when': (22, datetransform),
                 'observation_when': (7, datetransform),
                 'copies_to': (28, None),
                 'idx': (1, None),
                 'status': (25, None),
                 'diagnostic': (24, None),
                }
    

class cMessage:
    def __init__(self, hl7):
        self.hl7 = hl7
    def get_pid(self):
        return cPID(self.hl7['PID'][0])
    def get_orc(self):
        return cORC(self.hl7['ORC'])
    def get_obr(self):
        return cOBR(self.hl7['OBR'])
    def get_obx(self):
        return cOBX(self.hl7['OBX'])
    PID = property(get_pid)
    ORC = property(get_orc)
    OBR = property(get_obr)
    OBX = property(get_obx)


# --- The ContentHandler

class ContentGenerator(handler.ContentHandler):

    def __init__(self):
        handler.ContentHandler.__init__(self)
        self.hl7s = {}
        self.format = None
        self.chars = ''

    # ContentHandler methods
        
    def startElement(self, name, attrs):
        if name == 'HL7Messages':
            self.format = attrs['MessageFormat']
            #print "format", self.format
        elif self.format == 'ORUR01' and name == 'Message':
            self.msgid = attrs['MsgID']
            #print "msgid", self.msgid

    def endElement(self, name):
        if self.format == 'ORUR01' and name == 'Message':
            self.chars = self.chars.replace("\r\n", "\n")
            self.chars = self.chars.replace("\r", "\n")
            self.hl7 = cMessage(parse(self.chars))
            self.chars = ''
            self.hl7s[self.msgid] = self.hl7

    def characters(self, content):
        self.chars += content

# --- The main program

if __name__ == '__main__':
    parser = make_parser()
    cg = ContentGenerator()
    parser.setContentHandler(cg)
    parser.parse(sys.argv[1])
    #print pprint.pprint(cg.hl7s)
    #pprint.pprint(cg.hl7s['2']['OBX'])
    keys = cg.hl7s.keys()
    keys.sort()
    for k in keys:
        print "message", k

        hl7 = cg.hl7s[k]

        p = hl7.PID
        print "patient", p.id, p.name, p.ext_id, p.alt_id, p.gender, p.dob, p.address, p.tel

        for (i, o) in enumerate(hl7.ORC):
            print "ORC", i, o.request_id, o.order_id, o.provider

        for (i, b) in enumerate(hl7.OBR):
            print "OBR", i, b.idx, b.specimen_recv, b.results_reported_when, \
                        b.copies_to, b.status, b.diagnostic

        for (i, b) in enumerate(hl7.OBX):
            print "OBX", i, b.idx, b[2], repr(b.result), b.units, \
                        b.range, b.abnormal, b.comment, b.sub_id

        print
        print

