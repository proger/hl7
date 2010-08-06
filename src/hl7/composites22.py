from hl7trans import *
import compositetrans
transforms = {\
    'SI': {\
        'value': (0, None),
},
    'ST': {\
        'value': (0, None),
},
    'UN': {\
        'value': (0, None),
},
    'NM': {\
        'value': (0, numtransform),
},
    'TN': {\
        'value': (0, None),
},
    'DT': {\
        'value': (0, None),
},
    'TS': {\
        'value': (0, None),
},
    'TX': {\
        'value': (0, None),
},
    'AD': {\
        'street_address': (0, None),
        'other_designation': (1, None),
        'city': (2, None),
        'state_or_province': (3, None),
        'zip_or_postal_code': (4, None),
        'country': (5, None),
},
    'ID': {\
        'value': (0, None),
},
    'PN': {\
        'family_name': (0, None),
        'given_name': (1, None),
        'middle_initial': (2, None),
        'suffix': (3, None),
        'prefix': (4, None),
        'degree': (5, None),
},
    'CM': {\
        'field1': (0, None),
        'field2': (1, None),
        'field3': (2, None),
        'field4': (3, None),
        'field5': (4, None),
        'field6': (5, None),
},
    'CQ': {\
        'quantity': (0, numtransform),
        'units': (1, compositetrans.fieldtransformCE),
},
    'CN': {\
        'id_number': (0, None),
        'family_name': (1, None),
        'given_name': (2, None),
        'middle_initial': (3, None),
        'suffix': (4, None),
        'prefix': (5, None),
},
    'CE': {\
        'identifier': (0, None),
        'text': (1, None),
        'name_of_coding_system': (2, None),
},
    'CK': {\
        'id_number': (0, numtransform),
        'check_digit': (1, numtransform),
},
    'FT': {\
        'value': (0, None),
},
}

