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

def write_composites(ref, segments, fieldtransforms):
    f = open("hl7/composites%s.py" % ref, "w")
    f.write("from hl7trans import *\n")
    f.write("import compositetrans\n")
    f.write("transforms = {\\\n")
    for seg in segments:
        txt = "    '%s': {\\\n" % seg.name.upper()
        for field in seg.fields:
            idx = int(field['name'].split(".")[1])
            fieldname = ''
            prev_space = False
            for c in field['description'].lower().strip():
                if c.isalnum():
                    fieldname += c
                    prev_space = False
                elif c == '#':
                    fieldname += 'num'
                    prev_space = False
                elif c == '-' and not prev_space:
                    fieldname += '_'
                    prev_space = True
                elif c == ' ' and not prev_space:
                    fieldname += "_"
                    prev_space = True

            datatype = str(field['datatype'])
            if datatype in ['DT', 'TM', 'TS']:
                datatype = 'datetransform'
            elif datatype in ['ID', 'TN', 'TX', 'ST', 'FT', 'IS', 'SI',
                                'String', 'Date', 'Time']:
                datatype = 'None'
            elif datatype in ['NM', 'Double']:
                datatype = 'numtransform'
            else:
                fieldtransforms.add(datatype)
                datatype = 'compositetrans.fieldtransform%s' % datatype

            txt += "        '%s': (%d, %s),\n" % (fieldname, idx, datatype)
        txt += "},\n"
        f.write(txt)
    f.write("}\n\n")

    f.close()

def write_segments(ref, segments, fieldtransforms):
    f = open("hl7/segments%s.py" % ref, "w")
    f.write("from hl7trans import *\n")
    f.write("import compositetrans\n")
    f.write("transforms = {\\\n")
    for seg in segments:
        txt = "    '%s': {\\\n" % seg.name.upper()
        for field in seg.fields:
            idx = int(field['name'].split(".")[1])
            if seg.name == 'MSH': # due to implementation enc chars are skipped
                idx -= 1
            fieldname = ''
            prev_space = False
            for c in field['description'].lower().strip():
                if c.isalnum():
                    fieldname += c
                    prev_space = False
                elif c == '#':
                    fieldname += 'num'
                    prev_space = False
                elif c == '-' and not prev_space:
                    fieldname += '_'
                    prev_space = True
                elif c == ' ' and not prev_space:
                    fieldname += "_"
                    prev_space = True

            datatype = field['datatype']
            if datatype in ['DT', 'TM', 'TS']:
                datatype = 'datetransform'
            elif datatype in ['ID', 'TN', 'TX', 'ST', 'FT', 'IS', 'SI']:
                datatype = 'None'
            elif datatype == 'NM':
                datatype = 'numtransform'
            else:
                fieldtransforms.add(datatype)
                datatype = 'compositetrans.fieldtransform%s' % datatype
            txt += "        '%s': (%d, %s),\n" % (fieldname, idx, datatype)
        txt += "},\n"
        f.write(txt)
    f.write("}\n")
    f.close()

def parse_reference(ref, fieldtransforms):
    segments = []
    composites = []
    refpath = os.path.join("./reference/", ref)
    for fname in os.listdir(refpath):
        if fname.startswith("segment"):
            fname = os.path.join(refpath, fname)
            segments.append(parse_segment(fname))
        elif fname.startswith("composite"):
            fname = os.path.join(refpath, fname)
            composites.append(parse_segment(fname))

    write_segments(ref, segments, fieldtransforms)
    write_composites(ref, composites, fieldtransforms)

if __name__ == '__main__':
    fieldtransforms = set()
    for d in os.listdir("./reference"):
        if d.isdigit():
            parse_reference(d, fieldtransforms)

    f = open("hl7/compositetrans.py", "w")

    for datatype in fieldtransforms:
        f.write("""\
def fieldtransform%s(obj, data, val):
    return fieldtransform(obj, data, val, '%s')

""" % (datatype, datatype))

    f.close()

