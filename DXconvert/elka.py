# convert Elka EK44/EM44 voicedata
# to Yamaha 4-OP FM voicedata

# offset | size | data
# 0x00 | 5 | F0 2F 40 09 pp (INT=40~5F CRD=60~7F)

# 0x05 | sound1=67 + sound2=67 + 1 | data

# 0x8c      | 8 of 9 bytes | name of preset
# 0x94/0x95 | 1 | checksum
# 0x95/0x96 | 1 | F7
# 150 or 151 bytes total

from . import dx7
from . import fourop
from . import fb01
import math
from . import dxcommon
try:
    range = xrange
except NameError:
    pass

TLADJUST = False
freq44 = (0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
init44 = (0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  #OSC1 
          0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  #OSC3
          0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  #OSC2
          0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x63, 0x00, 0x00, 0x00, 0x00,  #OSC4
          0x0f, 0x07, 0x00, 0x02, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x63,
          0x40,
          0x01, 0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00,   #OSC5
          0x01, 0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00,   #OSC7
          0x01, 0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00,   #OSC6
          0x01, 0x40, 0x1f, 0x00, 0x00, 0x0f, 0x0f, 0x00, 0x63, 0x00, 0x00, 0x00,   #OSC8
          0x0f, 0x07, 0x00, 0x02, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x40,
          0x00,
          0x49, 0x6e, 0x69, 0x74, 0x56, 0x6f, 0x69, 0x63, 0x65) #NAME OF PRESET (9 characters)

#op 4,2,3,1 osc1/5,3/7,2/6,4/8
#adjust osc level depending on number of carriers
tlimit = ((0, 0, 0, 0), 
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 8, 8),
        (0, 13, 13, 13),
        (0, 13, 13, 13),
        (16, 16, 16, 16))

#op4,2,3,1 modulators
modulator = ((1,1,1,0),
          (1,1,1,0),
          (1,1,1,0),
          (1,1,1,0),
          (1,1,0,0),
          (1,0,0,0),
          (1,0,0,0),
          (0,0,0,0))

def ek2vmm(sound, name):
    BRIGHTNESS = 8
    TLADJUST = False
    vmm = fourop.initvmm()
    
    ALG = sound[49] & 7 #ALG
    for i in range(4):
        vmm[0 + 10*i] = sound[12*i + 2] & 31 #AR
        vmm[1 + 10*i] = sound[12*i + 3] & 31 #D1R
        vmm[2 + 10*i] = sound[12*i + 5] & 31 #D2R
        vmm[3 + 10*i] = sound[12*i + 6] & 15 #RR
        vmm[4 + 10*i] = sound[12*i + 4] & 15 #D1L
        vmm[5 + 10*i] = min(99, sound[12*i + 10] * 99 // 64) #LS
        
        KVS = int(round(sound[12*i + 11] * 7 / 127.)) & 7 #KVS
        EBS = (vmm[6 + 10*i] >> 3) & 7
        AME = (vmm[6 + 10*i] >> 6) & 1
        vmm[6 + 10*i] = (AME<<6) + (EBS<<3) + KVS
        
        OUT = dxcommon.tl2out(127-sound[12*i + 8])
        if TLADJUST:
            OUT = OUT - tlimit[ALG][i]
        if modulator[ALG][i] == 1:
            OUT = min(99, OUT + BRIGHTNESS)
        vmm[7 + 10*i] = max(0, min(127, OUT)) #OUT

        vmm[8 + 10*i] = fourop.freq_dx21.index(max(0.5, sound[12*i])) #dxratio(sound[12*N], 0) #op. ratio
       
        DET = (sound[12*i + 1] - 61) & 7 #op. detune -/+ 3 (61-64-67 -> 0 3 6)
        RS = sound[12*i + 7] & 3 #RS
        KVS2 = 0
        LS2 = sound[12*i + 9] & 1 #LS2 (sign)
        vmm[9 + 10*i] = (LS2<<6) + (KVS2<<5) + (RS<<3) + DET

    # ALG/FB
    #48 OSC mask
    FBL = sound[51] & 7 #FB
    SY = (vmm[40] >> 6) & 1
    vmm[40] = (SY<<6) + (FBL<<3) + ALG

# LFO
    vmm[41] = 99 * sound[59] // 31 #LFO speed
    vmm[42] = 99 * sound[61] // 127 #LFO delay
    vmm[43] = 99 * sound[60] // 127 #P.MOD depth
    vmm[44] = 0 #AMD

    LFW = (2,1,0,3)[sound[58]] #LFO wave sin, sqr, saw, rnd
    AMS = (vmm[45] >> 2) & 3
    PMS = sound[62] & 7 # P.MOD sens
    vmm[45] = (PMS<<4) + (AMS<<2) + LFW
    TRPS = (sound[51] - 2)*12 + (sound[52]-64) #OCTAVE, TRANSPOSE
    while TRPS > 24:
        TRPS -= 12
    while TRPS < -24:
        TRPS += 12
    vmm[46] = TRPS + 24
    #vmm[47] = 2 #PBR
    
    CH = min(1, sound[64]) # CHORUS
    vmm[48] += (CH<<4)
    
    #63 repeat (tremolo speed)
    # pfm pitch
    #51 OCTAVE 0...7 
    #52 TRSP 58..64..70 (-/+ 6 semitones)
    #53 DET 48 .. 64 .. 80 (-/+ 16 = -/+ 100 cents max)
    
    #VOICE NAME
    vmm[57:67] = dxcommon.string2list(name)
    
    # PEG
    if sound[57] in (1, 3): #P.ENV TYPE
        vmm[67] = 99 #PR1
    else:
        vmm[67] = sound[54] * 99 // 127 #PR1 P.ATTACK
    vmm[68] = sound[55] * 99 // 127 #PR2 P.DECAY
    #vmm[69] = 99 #PR3

    if sound[57] < 2: #P.ENV TYPE
        vmm[70] = int(50 + (sound[56] * 49 / 127 / 2)) #PL1
    else:
        vmm[70] = int(50 - (sound[56] * 50 / 127 / 2)) #PL1
    vmm[71] = 50 #PL2
    vmm[72] = 50 #PL3
    
    #65 SOUND LEVEL
    #66 RESERVED  

    return vmm

def vmm2ek(vmm, BRIGHTNESS, LOUDNESS):
    #BRIGHTNESS = -8
    TLADJUST = False
    ek44 = list(init44)

    f44 = ratio44(vmm)
    ALG = vmm[40] & 7 # osc. comb (algorithm)
    #SOUND1 OSCILLATORS
    for i in range(4):
        oscad = 12*i
        opad = 10*i
        ek44[oscad] = f44[i]    # REL FREQ 0...15 #vmm
        ek44[oscad+1] = 61 + (vmm[opad+9] & 7) #2 DETUNE 61..64..67
        ek44[oscad+2] = vmm[opad] # AR 0..31
        ek44[oscad+3] = vmm[opad+1] # DR 0..31 D1R
        ek44[oscad+4] = vmm[opad+4] # SL 0..15 D1L
        ek44[oscad+5] = vmm[opad+2] # SR 0..31 D2R
        ek44[oscad+6] = vmm[opad+3] # RR 0..15 RR
        ek44[oscad+7] = (vmm[opad+9] >> 3) & 3 # # RATE SCALING TYPE
        OSCLEVEL = 127 - dxcommon.out2tl(vmm[opad+7]) # OSC LEVEL 0..127
        if modulator[ALG][i] == 1:
            OSCLEVEL = max(0, min(127, OSCLEVEL + BRIGHTNESS))
        else:
            OSCLEVEL = max(0, min(127, OSCLEVEL + LOUDNESS))
        if TLADJUST:
            OSCLEVEL = min(127, OSCLEVEL + tlimit(ek44[49], i))
        ek44[oscad+8] = OSCLEVEL # OSC LEVEL 0..127
        ek44[oscad+9] = (vmm[opad+9] >> 6 ) & 1 # LS SIGN (0=neg 1=pos)
        ek44[oscad+10] = vmm[opad+5] * 64 // 99 # Level Scaling 0..127
        KVS2 = (vmm[opad+9] >> 5) & 1 #KVS sign
        if KVS2:
            ek44[oscad+11] = 0
        else:
            ek44[oscad+11] = (vmm[opad+6] & 7) << 4 #12 KVS 0..127

    #SOUND 1 PARAMETERS
    ek44[49] = ALG
    ek44[50] = (vmm[40] >> 3) & 7 #51 feedback
    ek44[51] = f44[4] # octave
    ek44[52] = f44[5] # transpose
    #53 detune

    #vmm 67 68 69PR1 PR2 PR vmm 70 71 72 PL1 PL2 PL3
    ek44[54] = vmm[67] * 127 // 99 #AR PR1
    ek44[55] = vmm[68] * 127 // 99 #DR PR2
    ek44[56] = min(127, int(abs(50 - vmm[70]) * 2 * 127 / 50)) #PEG LEVEL PL1
    if vmm[70] >= 50:
        if vmm[70] == 99:
            ek44[56] = 1
        else:
            ek44[56] = 0
    else:
        if vmm[70] == 99:
            ek[56] = 3
        else:
            ek[56] = 2

    #57 peg type sign(50-PL1)
    ek44[58] = (2,1,0,3)[vmm[45] & 3] #vib wave
    ek44[59] = vmm[41] * 31 // 99 #60 vib speed
    ek44[60] = vmm[43] * 127 // 99 #61 vib depth
    ek44[61] = vmm[42] * 127 // 99 #62 vib delay
    ek44[62] = (vmm[45] >> 4) & 3 #63 vib depth sens
    #63 repeat
    ek44[64] = vmm[48] >> 4 #65 chorus
    ek44[65] = 127 #66 sound level
    ek44[66] = 0x40 #reserved

    #SOUND 2 PARAMETERS
    ek44[67:134] = ek44[0:67]
    
    ek44[134] = 0 #reserved
    ek44[135:144] = vmm[57:66] #preset name
    return ek44

def check_ratio44(ratios):
    for r in ratios:
        if r not in freq44:
            return False
    return True

def ratio44(vmm):
    # convert 4-op DX/TX Yamaha operator ratios
    # to Elka Ek/ER/EM44 relative frequencies 
    ALG = vmm[40] & 7
    ratios = []

    for i in range(4):
        if (vmm[2*i+73] & 8):
            #    fix_4op(mode4op, rng4op, crs4op, fine4op)
            FIXRM = (vmm[2*i+73] >> 6) & 1
            FIXRG = vmm[2*i+73] & 7
            CRS = vmm[10*i+8]
            FINE = vmm[2*i+74] & 15
            ratios.append(fourop.fix_4op(FIXRM, FIXRG, CRS, FINE)/440.) #not really supported, but this conversion is better than nothing
        else:
            ratios.append(fourop.freq_4op[16*vmm[10*i+8] + (vmm[2*i+74]&15)])
   
    #convert dx transpose (+/-24) -> ek transpose, octave
    octave = 2
    transpose = 64
    trps = vmm[46] -24 #0 ... 48 (24=center)
    transpose += trps
    while transpose>70: #center+6
        transpose -= 12
        octave += 1
    while (transpose<58): #center-6
        transpose += 12
        octave -= 1

    for i in range(4):
        ratios[i] = round(ratios[i], 1)

    if check_ratio44((ratios[0]/2, ratios[1]/2, ratios[2]/2, ratios[3]/2)):
        octave += 1
        return int(ratios[0]/2), int(ratios[1]/2), int(ratios[2]/2), int(ratios[3]/2), max(0, min(7, octave)), transpose
    if check_ratio44((round(ratios[0]/1.5), round(ratios[1]/1.5), round(ratios[2]/1.5), round(ratios[3]/1.5))):
        transpose += 7
        while (transpose>70):
            transpose -= 12
            octave += 1
        return int(ratios[0]/1.5), int(ratios[1]/1.5), int(ratios[2]/1.5), int(ratios[3]/1.5), max(0, min(7, octave)), transpose
    if check_ratio44((min(15, ratios[0]), min(15, ratios[1]), min(15, ratios[2]), min(15, ratios[3]))):
        return int(min(15, ratios[0])), int(min(15, ratios[1])), int(min(15, ratios[2])), int(min(15, ratios[3])), max(0, min(7, octave)), transpose
    if check_ratio44((min(15, round(2*ratios[0])), min(15, round(2*ratios[1])), min(15, round(2*ratios[2])), min(15, round(2*ratios[3])))):
        octave -= 1
        return int(round(min(15, ratios[0]*2))), int(round(min(15, ratios[1]*2))), int(round(min(15, ratios[2]*2))), int(round(min(15, ratios[3]*2))), max(0, min(7, octave)), transpose

    for i in range(4):
        ratios[i] = min(15, max(0, int(round(ratios[i]))))
    return ratios[0], ratios[1], ratios[2], ratios[3], max(0, min(7, octave)), transpose

def ek2rdx(sound, name):
    vmm = ek2vmm(sound, name)
    rdx = reface.vmm2rdx(vmm)
    return rdx

def ek2fb(sound, name):
    vmm = ek2vmm(sound, name)
    fb = fb01.vmm2fb(vmm)
    return fb

