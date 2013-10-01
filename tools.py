def toMaiden(position, precision=4):
    """Returns a maidenloc for specified lat-lon tupel at specified 
    level. (4 being the default)
    """
    lat = position[0]
    lon = position[1]
    A = ord('A')
    a = divmod(lon+180, 20)
    b = divmod(lat+90, 10)
    astring = chr(A+int(a[0])) + chr(A+int(b[0]))
    lon = a[1]/2
    lat = b[1]
    i = 1
    while i < precision:
        i += 1
        a = divmod(lon,1)
        b = divmod(lat,1)
        if not (i%2):
            astring += str(int(a[0])) + str(int(b[0]))
            lon = 24 * a[1]
            lat = 24 * b[1]
        else:
            astring += chr(A+int(a[0])) + chr(A+int(b[0]))
            lon = 10 * a[1]
            lat = 10 * b[1]


    return astring
