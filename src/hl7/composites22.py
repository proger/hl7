from hl7trans import *
import compositetrans
transforms = {\
    'SI': {\
        'value': (1, None),
},
    'ST': {\
        'value': (1, None),
},
    'UN': {\
        'value': (1, None),
},
    'NM': {\
        'value': (1, numtransform),
},
    'TN': {\
        'value': (1, None),
},
    'DT': {\
        'value': (1, None),
},
    'TS': {\
        'value': (1, None),
},
    'TX': {\
        'value': (1, None),
},
    'AD': {\
        'street_address': (1, None),
        'other_designation': (2, None),
        'city': (3, None),
        'state_or_province': (4, None),
        'zip_or_postal_code': (5, None),
        'country': (6, None),
},
    'ID': {\
        'value': (1, None),
},
    'PN': {\
        'family_name': (1, None),
        'given_name': (2, None),
        'middle_initial': (3, None),
        'suffix': (4, None),
        'prefix': (5, None),
        'degree': (6, None),
},
    'CM': {\
        'field1': (1, None),
        'field2': (2, None),
        'field3': (3, None),
        'field4': (4, None),
        'field5': (5, None),
        'field6': (6, None),
},
    'CQ': {\
        'quantity': (1, numtransform),
        'units': (2, compositetrans.fieldtransformCE),
},
    'CN': {\
        'id_number': (1, None),
        'family_name': (2, None),
        'given_name': (3, None),
        'middle_initial': (4, None),
        'suffix': (5, None),
        'prefix': (6, None),
},
    'CE': {\
        'identifier': (1, None),
        'text': (2, None),
        'name_of_coding_system': (3, None),
},
    'CK': {\
        'id_number': (1, numtransform),
        'check_digit': (2, numtransform),
},
    'FT': {\
        'value': (1, None),
},
}

