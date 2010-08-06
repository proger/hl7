import datetime

def numtransform(obj, data, dt):
    dt = dt[0]
    return float(dt)
    
def datetransform(obj, data, dt):
    dt = dt[0]
    args = [dt[:4], dt[4:6], dt[6:8]]
    if len(dt) > 8:
        args.append(dt[8:10])
    if len(dt) > 10:
        args.append(dt[10:12])
    if len(dt) > 12:
        args.append(dt[12:14])
    zargs = [0] * 7
    zargs = zargs[len(args):]
    args = args + zargs
    args = map(int, args)
    #args.append(datetime.tzinfo("+0000")) # TODO: extract possible timezone
    args = tuple(args)
    return datetime.datetime(*args)

def typetrans(obj, data, val):
    val = val[0]
    if val == u'' and data[3][0] == u'HTML': # HTML-formatted
        return unicode
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
    val = val[0]
    return obj.valuetype(val)

