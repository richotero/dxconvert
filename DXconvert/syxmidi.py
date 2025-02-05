try:
    range = xrange
except NameError:
    pass

def mid2syx(mid):
    SYX = []
    syx = []
    i = 0
    n = 0
    while i < len(mid):
        n = 0
        if mid[i] in (0xf0, 0xf7):
            if mid[i] == 0xf0: 
                syx.append(0xf0)
            i += 1
            if mid[i]<128:
                n = mid[i]
                i += 1
            elif mid[i+1]<128:
                n = mid[i+1]
                n += (mid[i]&127)<<7
                i += 2
            elif mid[i+2]<128:
                n = mid[i+2]
                n += (mid[i+1]&127)<<7
                n += (mid[i]&127)<<14
                i += 3
            elif mid[i+3]<128:
                n = mid[i+3]
                n += (mid[i+2]&127)<<7
                n += (mid[i+1]&127)<<14
                n += (mid[i]&127)<<21
                i += 4
            syx += mid[i:i+n]
            if (syx[0] == 0xf0) and (syx[-1] == 0xf7):
                SYX += syx
                syx = []
            i += n
        else:
            i += 1
    return SYX

def syx2mid(syx):
    #####  HEADER CHUNK #####
    # format 0, 1 track, 96 ticks/quarter
    mid = [0x4d, 0x54, 0x68, 0x64, 0, 0, 0, 6, 0, 0, 0, 1, 0, 0x60]
    
    ##### TRACK CHUNK #####
    mid += [0x4d, 0x54, 0x72, 0x6b]
    mid += [0, 0, 0, 0] # tracklength=mid[18:22]
    
    ##### TRACK events #####
    # text meta event "SysEx Data"
    mid += [0x00, 0xff, 0x01]
    mid += [10, ord('S'), ord('y'), ord('s'), ord('E'), ord('x'), 
            ord(' '), ord('D'), ord('a'), ord('t'), ord('a')]
    # trackname meta event
    mid += [0x00, 0xff, 0x03]
    mid += [10, ord('S'), ord('y'), ord('s'), ord('E'), ord('x'), 
            ord(' '), ord('D'), ord('a'), ord('t'), ord('a')]

    # SysEx events
    mid.append(0) # delta time before first sysex event
    for i in range(len(syx)):
        if syx[i] == 0xf0:
            count = 0
            syxevent = []
            i += 1
            while syx[i] != 0xf7:
                syxevent.append(syx[i])
                i += 1
                count += 1
            mid += [0xf0] + varlen(count + 1) + syxevent + [0xf7]
            mid += varlen(ticks(int(10 + 0.32 * count))) # delta time before next event + 10ms

    # End of Track meta event
    mid += [0xff, 0x2f, 0x00]
    
    trlen = len(mid[22:])
    mid[18] = (trlen&0xff000000)>>24
    mid[19] = (trlen&0xff0000)>>16
    mid[20] = (trlen&0xff00)>>8
    mid[21] = trlen&0xff

    return mid

def varlen(i):
    vl = []
    if i < 128:
        vl.append(i)
    elif i < 16384:
        vl.append(128 + ((i>>7)&127))
        vl.append(i&127)
    elif i < 2097152:
        vl.append(128 + ((i>>14)&127))
        vl.append(128 + ((i>>7)&127))
        vl.append(i&127)
    else:
        vl.append(128 + ((i>>21)&127))
        vl.append(128 + ((i>>14)&127))
        vl.append(128 + ((i>>7)&127))
        vl.append(i&127)
    return vl

def ticks(ms):
    '''
    bpm=120
    res=96
    return ms*bpm*res//60000
    '''
    return int(0.192*ms)

