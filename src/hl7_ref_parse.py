#!/usr/bin/env python
""" module for reading mirth hl7 specs and outputting python code parsers
"""

import os
from xml.sax import saxutils, handler
from xml import sax


class SegmentHandler(handler.ContentHandler):

    def __init__(self, handler_class=None):
        """ NOTE: this class must be passed a handler_class to trigger
            parsing of the individual HL7 messages.  otherwise it stores
            the raw HL7 data, after parsing the XML wrapping.
        """
        handler.ContentHandler.__init__(self)
        self.fields = []
        self.name = None
        self.description = None

    # ContentHandler methods

    def startElement(self, name, attrs):
        self.chars = ''
        if name == 'field':
            self.field_attrs = dict(attrs)

    def endElement(self, name):
        if name == 'name':
            if self.name is None:
                self.name = self.chars
            else:
                self.current_fieldname = self.chars
        elif name == 'description':
            if self.description is None:
                self.description = self.chars
            else:
                self.current_description = self.chars
        elif name == 'datatype':
            self.current_datatype = self.chars
        elif name == 'field':
            field = {'attrs': self.field_attrs,
                     'name': self.current_fieldname,
                     'description': self.current_description,
                     'datatype': self.current_datatype
                    }
            self.fields.append(field)

        self.chars = ''

    def characters(self, content):
        self.chars += content

def parse_segment(fname):
    cg = SegmentHandler()
    sax.parse(fname, cg)
    return cg

def write_segments(ref, segments):
    f = open("hl7/segments%s.py" % ref, "w")
    for seg in segments:
        txt = "%s_transform = {\\\n" % seg.name.lower()
        for field in seg.fields:
            idx = int(field['name'].split(".")[1])
            fieldname = ''
            prev_space = False
            for c in field['description'].lower().strip():
                if c.isalnum():
                    fieldname += c
                    prev_space = False
                elif c == ' ' and not prev_space:
                    fieldname += "_"
                    prev_space = True
                else:
                    prev_space = False
            datatype = field['datatype']
            if datatype in ['DT', 'TM']:
                datatype = 'datetransform'
            else:
                datatype = 'None'
            txt += "         '%s': (%d, %s),\n" % (fieldname, idx, datatype)
        txt += "               }\n\n"
        f.write(txt)
    f.close()

def parse_reference(ref):
    segments = []
    refpath = os.path.join("./reference/", ref)
    for fname in os.listdir(refpath):
        if fname.startswith("segment"):
            fname = os.path.join(refpath, fname)
            segments.append(parse_segment(fname))

    write_segments(ref, segments)

if __name__ == '__main__':
    for d in os.listdir("./reference"):
        if d.isdigit():
            parse_reference(d)