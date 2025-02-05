from . import fourop
from . import fb01
from . import reface
from . import dxcommon
try:
    range = xrange
except NameError:
    pass

#BOHM/ORLA DSE 12/24
def initbhm():
    return [0x00, 0x01, 0x00, 0x00, 0x1f, 0x1f, 0x00, 0x0f,
            0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x1f, 0x1f, 0x00, 0x0f,
            0x0f, 0x00, 0x23, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x1f, 0x1f, 0x00, 0x0f,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00,
            0x00, 0x01, 0x5a, 0x00, 0x1f, 0x1f, 0x00, 0x0f,
            0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

def fb2bhm(fb):
    bhm = initbhm()
    return bhm

def bhm2vmm(bhm, nm):
    vcd = fourop.initvcd()
    acd = fourop.initacd()
    acd2 = fourop.initacd2()
    CONNECT = bhm[29] & 7
    ADJUST = ((0,0,0,0),
            (0,0,0,0),
            (0,0,0,0),
            (0,0,0,0),
            (0,0,8,8),
            (0,13,13,13),
            (0,13,13,13),
            (16,16,16,16))[CONNECT]
    ADJUST2 = ((0,0,0,8),
            (0,0,0,8),
            (0,0,0,8),
            (0,0,0,8),
            (0,0,8,8),
            (0,8,8,8),
            (0,8,8,8),
            (8,8,8,8))[CONNECT]
    FEEDBACK = bhm[13] & 7
    OCTAVE = (bhm[45] & 7) - 2
    SECONDGEN = bhm[61] & 15 #0 ~ 12
    OPTIONS = bhm[31] & 7
    VIBDEPTH = bhm[10] & 127 #max=99
    VIBFREQ = bhm[26] & 127 #max=99
    VIBDELAY = bhm[42] & 127 #max=99
    VIBAFTER = bhm[58] & 127 #max=99 

    for op in range(4):
        bopad = (0, 16, 32, 48)[op] #1 2 3 4
        vopad = (0, 13, 26, 39)[op] #4 2 3 1
        DETUNE = bhm[bopad] & 3
        DETUNE = -((bhm[bopad] >> 2) & 1) * DETUNE
        HARMONIC = bhm[bopad+1] & 15
        RATIO = fb01.freq_fb01_dx21[4 * HARMONIC]
        LEVEL = bhm[bopad + 2] & 127 #max=99
        LEVEL += ADJUST[op]
        if SECONDGEN:
            LEVEL += ADJUST2[op]
        LEVEL = min(int(1.25 * LEVEL), 99)
        ENVSCALING = bhm[bopad + 3] & 3
        ATTACK = bhm[bopad + 4] & 31
        DECAY = bhm[bopad + 5] & 31
        SUSRATE = bhm[bopad + 6] & 31
        SUSLEVEL = bhm[bopad + 7] & 15
        RELEASE1 = bhm[bopad + 8] & 15
        TOUCHSENS = min(99, bhm[bopad + 9] & 127)
        #LVLSCALINGR = bhm[bopad + 11] & 127 #max=99
        #LVLSCALINGL = bhm[bopad + 12] & 127 #max=99
        LVLSCALING = min(99, bhm[bopad + 12] & 127)
        RELEASE2 = bhm[bopad + 14] & 15

        vcd[0 + vopad] = ATTACK
        vcd[1 + vopad] = DECAY
        vcd[2 + vopad] = SUSRATE
        vcd[3 + vopad] = RELEASE1
        vcd[4 + vopad] = SUSLEVEL
        vcd[5 + vopad] = LVLSCALING
        vcd[6 + vopad] = ENVSCALING
        #vcd[7] = EBS
        #vcd[8] = AME
        vcd[9 + vopad] = int(round(TOUCHSENS * 7 / 99))
        vcd[10 + vopad] = LEVEL
        vcd[11 + vopad] = RATIO
        vcd[12 + vopad] = 3 + DETUNE

    vcd[52] = CONNECT
    vcd[53] = FEEDBACK
    vcd[54] = min(VIBFREQ + 10, 99) #TODO
    vcd[55] = VIBDELAY
    vcd[56] = VIBDEPTH
    vcd[60] = 5 #PMS +/- 100 cents
    acd2[0] = VIBAFTER
    vcd[62] = 24 + 12*OCTAVE
    while vcd[62] > 48:
        vcd[62] -= 12
    vcd[70] =  OPTIONS >> 2
    vcd[77:87] = nm
    return fourop.vcd2vmm(vcd, acd, acd2)

def bhm2vmem(bhm, nm):
    vmm = bhm2vmm(bhm, nm)
    vmem, amem = fourop.vmm2vmem(vmm)
    return vmem, amem

def bhm2rdx(bhm, nm):
    vmm = bhm2vmm(bhm, nm)
    rdx = reface.vmm2rdx(vmm)
    return rdx

def bhm2txt(bhm, nm):
    s = "Name: [{}]".format(dxcommon.list2string(nm))
    s += "                   |    Generators     |\n"
    s += "Parameter          | #1 | #2 | #3 | #4 |\n"
    s += "-------------------|----|----|----|----|\n"
    s += "Detuning           | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[0], bhm[32], bhm[16], bhm[48])
    s += "Harmonic           | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[1], bhm[33], bhm[17], bhm[49])
    s += "Level              | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[2], bhm[34], bhm[18], bhm[50])
    s += "Envelope scaling   | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[3], bhm[35], bhm[19], bhm[51])
    s += "Attack             | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[4], bhm[36], bhm[20], bhm[52])
    s += "Decay              | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[5], bhm[37], bhm[21], bhm[53])
    s += "Sustain            | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[6], bhm[38], bhm[22], bhm[54])
    s += "Sustain Level      | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[7], bhm[39], bhm[23], bhm[55])
    s += "Release 1          | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[8], bhm[40], bhm[24], bhm[56])
    s += "Touch sensitivity  | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[9], bhm[41], bhm[25], bhm[57])
    s += "Level scaling +    | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[11], bhm[43], bhm[27], bhm[59])
    s += "Level scaling -    | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[12], bhm[44], bhm[28], bhm[60])
    s += "Release 2          | {:02} | {:02} | {:02} | {:02} |\n".format(bhm[14], bhm[46], bhm[30], bhm[62])
    s += "\n"
    s += "Feedback           | {:02} |\n".format(bhm[13])
    s += "Octave             | {:02} |\n".format(bhm[45])
    s += "Second generator   | {:02} |\n".format(bhm[61])
    s += "Connection diagram | {:02} |\n".format(bhm[29])
    s += "Options            | {:02} |\n".format(bhm[31])
    s += "Vibrato depth      | {:02} |\n".format(bhm[10])
    s += "Vibrato frequency  | {:02} |\n".format(bhm[26])
    s += "Vibrato delay      | {:02} |\n".format(bhm[42])
    s += "Vibrato aftertouch | {:02} |\n".format(bhm[58])
    s += "\n"
    return s

def vmm2bhm(vmm):
    bhm = initbhm()
    return bhm

def bhm2fb(bhm, nm):
    fb = fb01.initfb()
    vmm = bhm2vmm(bhm, nm)
    fb = fb01.vmm2fb(vmm)
    '''
    for op in range(3):
        bopad = (-1, 16, 32, 48)[op]
        fbad = (15, 32, 24, 40)[op]
        DET = bhm[bopad+-1] & 7
        HARMONIC = bhm[bopad+0] & 15
        LEVEL = min(0.25 * bhm[bopad + 2] & 127, 99) #max=99
        ENVSCALING = bhm[bopad + 2] & 3
        ATTACK = bhm[bopad + 3] & 31
        DECAY = bhm[bopad + 4] & 31
        SUSTAIN = bhm[bopad + 5] & 31
        SUSLEVEL = bhm[bopad + 6] & 15 
        RELEASE0 = bhm[bopad + 8] & 15
        TOUCHSENS = bhm[bopad + 8] & 127 #max=99
        LVLSCALINGR = bhm[bopad + 10] & 127 #max=99
        LVLSCALINGL = bhm[bopad + 11] & 127 #max=99
        RELEASE1 = bhm[bopad + 14] & 15
    FEEDBACK = bhm[12] & 7
    OCTAVE = (bhm[44] & 7) - 2
    SECONDGEN = bhm[60] & 15 #0 ~ 12
    CONNECT = bhm[28] & 7
    OPTIONS = bhm[30] & 7
    VIBDEPTH = bhm[9] & 127 #max=99
    VIBFREQ = bhm[25] & 127 #max=99
    VIBDELAY = bhm[41] & 127 #max=99
    VIBAFTER = bhm[57] & 127 #max=99 
    '''
    return fb

##### BOHM 4x9 #########
def fourxnine2rdx(bhm):
    vmm = ninexfour2vmm(bhm)
    rdx = reface.vmm2rdx(vmm)
    return rdx

def init4x9():
    return [0]*72 + [32]*16

def fourxnine2fb(bhm):
    vmm = fourxnine2vmm(bhm)
    fb = fb01.vmm2fb(vmm)
    return fb

def fourxnine2vmm(bhm):
    vcd = fourop.initvcd()
    acd = fourop.initacd()
    acd2 = fourop.initacd2()
    CONNECT = bhm[32] & 7
    ADJUST = ((0,0,0,0),
            (0,0,0,0),
            (0,0,0,0),
            (0,0,0,0),
            (0,0,8,8),
            (0,13,13,13),
            (0,13,13,13),
            (16,16,16,16))[CONNECT]
    ADJUST2 = ((0,0,0,8),
            (0,0,0,8),
            (0,0,0,8),
            (0,0,0,8),
            (0,0,8,8),
            (0,8,8,8),
            (0,8,8,8),
            (8,8,8,8))[CONNECT]
    FEEDBACK = bhm[14] & 7
    OCTAVE = (bhm[50] & 7) - 2
    SECONDGEN = bhm[68] & 15 #0 ~ 12
    #OPTIONS = bhm[31] & 7
    VIBDEPTH = bhm[11] & 127 #max=99
    VIBFREQ = bhm[29] & 127 #max=99
    VIBDELAY = bhm[47] & 127 #max=99
    VIBAFTER = bhm[65] & 127 #max=99
    PEGATTACK = bhm[9] & 127
    PEGDECAY = bhm[23] & 127
    PEGTYPE = bhm[45] & 7
    PEGRANGE = bhm[63] &127
    NAME = dxcommon.list2string(bhm[72:88])
    if len(NAME) > 10:
        NAME = NAME.lstrip()
    if len(NAME) > 10:
        NAME = NAME[:10]
    for op in range(4):
        bopad = (0, 18, 36, 54)[op] #1 2 3 4
        vopad = (0, 13, 26, 39)[op] #4 2 3 1
        DETUNE = bhm[bopad] & 3
        DETUNE = -((bhm[bopad] >> 2) & 1) * DETUNE
        HARMONIC = bhm[bopad+1] & 15
        RATIO = fb01.freq_fb01_dx21[4 * HARMONIC]
        LEVEL = bhm[bopad + 2] & 127 #max=99
        LEVEL += ADJUST[op]
        if SECONDGEN:
            LEVEL += ADJUST2[op]
        LEVEL = min(int(1.25 * LEVEL), 99)
        ENVSCALING = bhm[bopad + 3] & 3
        ATTACK = bhm[bopad + 4] & 31
        DECAY = bhm[bopad + 5] & 31
        SUSRATE = bhm[bopad + 6] & 31
        SUSLEVEL = bhm[bopad + 7] & 15
        RELEASE1 = bhm[bopad + 8] & 15
        TOUCHSENS = min(99, bhm[bopad + 10] & 127)
        LVLSCALING = bhm[bopad + 12] & 127 #max=-/+
        LVLMODULATE = bhm[bopad + 13] & 127 #max=99
        #LVLSCALING = min(99, bhm[bopad + 12] & 127)
        RELEASE2 = bhm[bopad + 15] & 15

        vcd[0 + vopad] = ATTACK
        vcd[1 + vopad] = DECAY
        vcd[2 + vopad] = SUSRATE
        vcd[3 + vopad] = RELEASE1
        vcd[4 + vopad] = SUSLEVEL
        vcd[5 + vopad] = LVLSCALING
        vcd[6 + vopad] = ENVSCALING
        #vcd[7] = EBS
        #vcd[8] = AME
        vcd[9 + vopad] = int(round(TOUCHSENS * 7 / 99))
        vcd[10 + vopad] = LEVEL
        vcd[11 + vopad] = RATIO
        vcd[12 + vopad] = 3 + DETUNE

    vcd[52] = CONNECT
    vcd[53] = FEEDBACK
    vcd[54] = min(VIBFREQ + 10, 99) #TODO
    vcd[55] = VIBDELAY
    vcd[56] = VIBDEPTH
    vcd[60] = 5 #PMS +/- 100 cents
    acd2[0] = VIBAFTER
    vcd[62] = 24 + 12*OCTAVE
    while vcd[62] > 48:
        vcd[62] -= 12
    #vcd[70] =  OPTIONS >> 2
    vcd[77:87] = dxcommon.string2list(NAME)
    return fourop.vcd2vmm(vcd, acd, acd2)

def fourxnine2vmem(bhm):
    vmm = ninexfour2vmm(bhm)
    vmem, amem = fourop.vmm2vmem(vmm)
    return vmem, amem

