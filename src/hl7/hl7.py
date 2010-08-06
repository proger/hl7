# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 John Paulett (john -at- 7oars.com)
# Copyright (C) 2010 Luke Kenneth Casson Leighton <lkcl@lkcl.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""Simple library for parsing messages of Health Level 7 (HL7)
version 2.x (and version 3.x XML format)

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

import datetime
import sys, string
import pprint

from xml.sax import saxutils, handler
from xml import sax

from segments import segment_revs
from hl7util import *

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
        for (i, seg) in enumerate(self):
            #print type(i), type(i[0]), repr(i[0]), repr(key)
            if seg[0][0] == unicode(key):
                seg._idx = i
                res.append(seg)
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


class TIter(object):
    def __init__(self, d):
        self.cls = d.__class__
        self._message = d._message
        self.i = d.data.__iter__()
    def __iter__(self):
        return self
    def next(self):
        data = self.i.next()
        return self.cls(self._message, data)


class Transform(object):
    def __init__(self, message, data):
        self.data = data
        self._message = message
        segname = str(self.data[0][0])
        self._transform = segment_revs[message.version].transforms[segname]

    def __iter__(self):
        return TIter(self).__iter__()

    def __getitem__(self, key):
        if isinstance(key, int):
            if key > len(self.data):
                return None
            return self.fieldcheck(self.data[key])
        return self.__class__(self.data[key])

    def __getattr__(self, key):
        if key == 'NTE':
            idx = self.data._idx
            for (i, seg) in enumerate(self._message._hl7):
                seg._idx = i
                if i == idx+1:
                    return cNTE(self._message, seg)
            return None
        elif key in [ 'OBR', 'ORC']:
            sn = str(self.data[0])
            if sn == 'ORC' and key == 'OBR':
                return self._message.get_obr_by_order_id(self.order_id)
            elif sn == 'OBR' and key == 'ORC':
                return self._message.get_orc_by_order_id(self.order_id)
            idx = self.data._idx
            l = list(getattr(self._message, key))
            l.reverse()
            kls = {'OBR': cOBR, 'ORC': cORC}[key]
            for seg in l:
                if seg.data._idx <= idx and seg[0] == key:
                    return seg #kls(self._message, seg)
            return None
        elif key == 'OBX':
            idx = self.data._idx
            res = []
            for (i, seg) in enumerate(self._message._hl7):
                seg._idx = i
                if i <= idx:
                    continue
                sn = str(seg[0])
                if sn not in ['OBX', 'NTE']:
                    break
                if sn == 'OBX':
                    res.append(cOBX(self._message, seg))
            return res
        if isinstance(key, int):
            if key > len(self.data):
                return None
            return self.fieldcheck(self.data[key])
        tf = self.get_transform(key)
        idx = tf[0]
        typ = tf[1]
        if idx >= len(self.data):
            return None
        val = self.data[idx]
        if typ is None:
            val = self.fieldcheck(val)
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
    
    def get_transform(self, key):
        if self.transform.has_key(key):
            return self.transform[key]
        return self._transform[key]

class cNTE(Transform):
    """
    """
    transform = { 'comment': (3, None),
                }

class cMSH(Transform):
    """
    """
    transform = {'sendingapp': (2, None),
                 'lab': (3, None),
                 'receivingapp': (4, None),
                 'timestamp': (6, datetransform),
                 'ctrl_id': (9, None),
                }


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
    clin_when       OBX 014 Date/Time of observation
    """
    transform = {'result': (5, obxrestrans),
                 'valuetype': (2, typetrans),
                 'sub_id': (4, None),
                 'idx': (1, None),
                 'units': (6, None),
                 'range': (7, None),
                 'abnormal': (8, None),
                 'identifier': (3, None),
                 'clin_when': (14, datetransform),
                }


class cOBR(Transform):
    """
    OBR 001 index?
    OBR 003 filler order number
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
                 'order_id': (3, None),
                 'copies_to': (28, None),
                 'idx': (1, None),
                 'status': (25, None),
                 'diagnostic': (24, None),
                }
    

class cMessage(object):
    def __init__(self, hl7, version):
        self._hl7 = hl7
        self.version = version
    def get_msh(self):
        return cMSH(self, self._hl7['MSH'][0])
    def get_pid(self):
        return cPID(self, self._hl7['PID'][0])
    def get_orc(self):
        return cORC(self, self._hl7['ORC'])
    def get_obr(self):
        return cOBR(self, self._hl7['OBR'])
    def get_obx(self):
        return cOBX(self, self._hl7['OBX'])
    MSH = property(get_msh)
    PID = property(get_pid)
    ORC = property(get_orc)
    OBR = property(get_obr)
    OBX = property(get_obx)
    def get_orc_by_order_id(self, order_id):
        for orc in self.ORC:
            if orc.order_id == order_id:
                return orc
        return None

    def get_obr_by_order_id(self, order_id):
        for obr in self.OBR:
            if obr.order_id == order_id:
                return obr
        return None


# --- The ContentHandler

class HL7Handler(handler.ContentHandler):

    def __init__(self, handler_class=None):
        """ NOTE: this class must be passed a handler_class to trigger
            parsing of the individual HL7 messages.  otherwise it stores
            the raw HL7 data, after parsing the XML wrapping.
        """
        handler.ContentHandler.__init__(self)
        self.hl7s = {}
        self.format = None
        self.handler_class = handler_class
        self.chars = ''

    # ContentHandler methods
        
    def startElement(self, name, attrs):
        if name == 'HL7Messages':
            self.format = attrs['MessageFormat']
            self.version = attrs['Version']
            #print "format", self.format
        elif (self.format == 'ORUR01' \
              or self.format == 'ZLIL10') \
            and name == 'Message':
            self.msgid = attrs['MsgID']
            #print "msgid", self.msgid

    def endElement(self, name):
        if (self.format == 'ORUR01' \
              or self.format == 'ZLIL10') \
            and name == 'Message':
            self.chars = self.chars.replace("\r\n", "\n")
            self.chars = self.chars.replace("\r", "\n")
            msg = self.chars
            self.chars = ''
            if self.handler_class:
                msg = self.handler_class(parse(msg), self.version)
            self.hl7s[self.msgid] = msg

    def characters(self, content):
        self.chars += content

def parse_hl7v3(fname, handler_class=None):
    cg = HL7Handler(handler_class=handler_class)
    sax.parse(fname, cg)
    return cg.hl7s

def parse_hl7v3_string(string, handler_class=None):
    cg = HL7Handler(handler_class=handler_class)
    sax.parseString(string, cg)
    return cg.hl7s

# --- The main program

if __name__ == '__main__':
    hl7s = parse_hl7v3(sys.argv[1], cMessage)
    keys = hl7s.keys()
    keys.sort()
    for k in keys:
        print "-------"
        print "message", k

        hl7 = hl7s[k]

        m = hl7.MSH
        print "msg", m.ctrl_id, m.timestamp, m.lab, m.sendingapp, m.receivingapp

        p = hl7.PID
        print "patient", p.id, map(str, p.name), p.ext_id, p.alt_id, p.gender, p.dob, p.address, p.tel

        for (i, o) in enumerate(hl7.ORC):
            print "ORC", i, o.request_id, o.filler_order_number, \
                            o.ordering_provider
            b = o.OBR
            print "OBR", i, b.set_id, b.order_id, \
                        b.specimen_recv, b.results_reported_when, \
                        b.copies_to, b.status, b.diagnostic, \
                            b.NTE and b.NTE.comment, \
                            "ORC order id", b.ORC and b.ORC.order_id

            for (i, x) in enumerate(b.OBX):
                print "\tOBX", i, x.idx, repr(x.result), x.units, \
                            x.range, x.abnormal, x.identifier, x.sub_id, \
                            x.clin_when, \
                            x.NTE and x.NTE.comment, \
                            "OBR idx", x.OBR and x.OBR.idx, \
                            "ORC order id", x.ORC and x.ORC.order_id

            print
            print

