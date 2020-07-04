# read .opm files from VOPM OPM synth emulator
# and convert to FB01 format
from . import dxcommon
from . import fourop
from . import fb01
import os
try:
    range = xrange
except NameError:
    pass

def file2data(opmfile):

    try:
        with open(opmfile, 'r', errors="replace") as f:
            lines = f.readlines()
    except:
         with open(opmfile, 'r') as f:
            lines = f.readlines()
  
    data=[]
    p=-1
    for i in range(len(lines)):
        if lines[i].startswith('@:'):
            p += 1
            nm = lines[i][3+len(str(p)):].strip()
            name = 20*[32] # This is probably more than we really need
            for n in range(min(20, len(nm))):
                name[n] = ord(nm[n])

            for initvoice in ("init      ", "Null      ", "no Name   "):
                n = dxcommon.list2string(name[:10])
                if n.lower() == initvoice.lower():
                    name[:10] = [73, 78, 73, 84, 32, 86, 79, 73, 67, 69] # "INIT VOICE"
                    break
            
            if dxcommon.list2string(name)[:10].lower() == "instrument":
                x = "{:04}".format(int(dxcommon.list2string(name[11:15])))
                newname = os.path.basename(opmfile)[:-4]
                if len(newname)<6:
                    newname += "_"*(6-len(newname))
                newname = newname[:6]+"{}".format(x)
                name[:10] = dxcommon.string2list(newname)

            # parse OPM data
            for x in range(i+1, len(lines)):
                thisline = lines[x].strip()
                if thisline.startswith("LFO:"):
                    lfo = lines[x][4:].split()
                elif thisline.startswith("CH:"):
                    ch = lines[x][4:].split()
                elif thisline.startswith("M1:"):
                    m1 = lines[x][4:].split()
                elif thisline.startswith("C1:"):
                    c1 = lines[x][4:].split()
                elif thisline.startswith("M2:"):
                    m2 = lines[x][4:].split()
                elif thisline.startswith("C2:"):
                    c2 = lines[x][4:].split()
                elif thisline.startswith("@:"):
                    break
                
            # stringnumbers to intnumbers
            for i in range(len(lfo)):
                lfo[i] = int(lfo[i])
            for i in range(len(ch)):
                ch[i] = int(ch[i])
            for i in range(len(m1)):
                m1[i] = int(m1[i])
            for i in range(len(c1)):
                c1[i] = int(c1[i])
            for i in range(len(m2)):
                m2[i] = int(m2[i])
            for i in range(len(c2)):
                c2[i] = int(c2[i])
            
            data += (name+lfo+ch+m1+c1+m2+c2)
    return data

def vopm2fb01(vopm):
    ADJUST = 8
    fb = fb01.initfb()
    fb[0:7] = vopm[0:7] #NAME
    fb[8] = vopm[20]&255 # LFO speed
    fb[9] = vopm[21]&127 # AMD
    fb[10] = vopm[22]&127 #PMD
    fb[11] = vopm[30]&120 #Operator enable
    ALG = vopm[27]&7
    fb[12] = ((vopm[26]&7)<<3) + ALG # FBL, ALG
    fb[13] = (vopm[28]&3) + ((vopm[29]&3)<<4) # AMS, PMS
    fb[14] = (vopm[23]&3)<<5
    fb[15] = 0 #Transpose
    for op in range(4):
        if ((vopm[30]>>(op+3))&1) == 0:
            TL = 127
        else:
            TL = vopm[37+11*op]&127 #TL
        if fourop.carrier(ALG, 3-op) == False:
            TL -= ADJUST
        fb[16+8*op] = max(0, min(127, TL))
        fb[1+16+8*op] = 0   # KStype, Velocity sensitivity
        fb[2+16+8*op] = 0   # Level Scaling, TL adjust
        if op in (1, 3):
            pass #fb[2+16+8*op] = 15
        fb[3+16+8*op] = (vopm[39+11*op]&15) + ((vopm[40+11*op]&7)<<4) #MUL, DT1
        fb[4+16+8*op] = (vopm[32+11*op]&31) + ((vopm[38+11*op]&3)<<6) #AR, RS
        fb[5+16+8*op] = (vopm[42+11*op]&128) + (vopm[33+11*op]&31)    #AMS-EN, D1R 
        fb[6+16+8*op] = (vopm[34+11*op]&31) + ((vopm[41+11*op]&3)<<6)  #D2R, DT2
        fb[7+16+8*op] = (vopm[35+11*op]&15) + ((vopm[36+11*op]&15)<<4)   #RR, D1L
    return fb

def fb2vopm(fbdata):
    ADJUST = 8
    opm = '//Converted using TXconvert-{} ({})\n'.format(dxcommon.PROGRAMVERSION, dxcommon.PROGRAMDATE)
    opm += '//LFO: LFRQ AMD PMD WF NFRQ\n'
    opm += '//@:[Num] [Name]\n'
    opm += '//CH: PAN FL CON AMS PMS SLOT NE\n'
    opm += '//[OPname]: AR D1R D2R  RR D1L  TL  KS MUL DT1 DT2 AMS-EN\n\n'
    for p in range(len(fbdata)//64):
        fb = fbdata[64*p:64*p+64]
        #convert FB01 to VOPM .opm ascii file format
        naam = ''
        for i in range(7):
            naam += chr(fb[i])
        opm += '@:{} {}\n'.format(p, naam)
    
        opm += 'LFO:{:3d} {:3d} {:3d} {:3d} {:3d}\n'.format(fb[8], fb[9]&127, fb[10]&127, (fb[14]>>5)&3, 0)
    
        ALG = fb[12]&7
        opm += 'CH:{:3d} {:3d} {:3d} {:3d} {:3d} {:3d} {:3d}\n'.format(64, (fb[12]>>3)&7, ALG, fb[13]&3, (fb[13]>>4)&7, 120, 0)
  
        #VOPM does not have a global TRANSPOSE parameter. Try transposing the MUL parameter.
        trps = fb[15]
        muls = [max(0.5, fb[43]&15), max(0.5, fb[35]&15), max(0.5, fb[27]&15), max(0.5, fb[19]&15)]
        if trps > 127:
            trps -= 256
        if trps != 0:
            trpx = (2.**(1./12.))**trps
            for i in range(4):
                muls[i] = round(trpx * muls[i], 1)

            if muls[0] in fb01.freq_fb01:
                if muls[1] in fb01.freq_fb01:
                    if muls[2] in fb01.freq_fb01:
                        if muls[3] in fb01.freq_fb01:
                            fb[43] = (fb[43]&0xf0) + fb01.freq_fb01.index(muls[0])%16
                            fb[46] = (fb[46]&31) + ((fb01.freq_fb01.index(muls[0])//16)<<5)
                        
                            fb[35] = (fb[35]&0xf0) + fb01.freq_fb01.index(muls[1])%16
                            fb[38] = (fb[38]&31) + ((fb01.freq_fb01.index(muls[1])//16)<<5)

                            fb[27] = (fb[27]&0xf0) + fb01.freq_fb01.index(muls[2])%16
                            fb[30] = (fb[30]&31) + ((fb01.freq_fb01.index(muls[2])//16)<<5)

                            fb[19] = (fb[19]&0xf0) + fb01.freq_fb01.index(muls[3])%16
                            fb[22] = (fb[22]&31) + ((fb01.freq_fb01.index(muls[3])//16)<<5)

        for op in range(4):

            opa = 16+8*op
            opn = ('M1:', 'C1:', 'M2:', 'C2:')[op]


            TL = (fb[opa]&127) + (fb[opa+2]&15)
            if fourop.carrier(ALG, 3-op) == False:
                TL += ADJUST
            
            LSSIGN = fb[opa+1]>>7 # 0=NEG 1=POS
            LSTYPE = fb[opa+3]>>7 # 0=LIN 1=EXP
            LSDEPTH = fb[opa+2]>>4 
            
            if LSSIGN:
                TL -= LSDEPTH
            else:
                TL += LSDEPTH

            TL = max(0, min(127, TL))

            opm += '{:s}{:3d} {:3d} {:3d} {:3d} {:3d} {:3d} {:3d} {:3d} {:3d} {:3d} {:3d}\n'.format(opn, fb[opa+4]&31, fb[opa+5]&31, fb[opa+6]&31, fb[opa+7]&15, fb[opa+7]>>4, TL, fb[opa+4]>>6, fb[opa+3]&15, (fb[opa+3]>>4)&7, fb[opa+6]>>6, fb[opa+5]&128)
        opm += '\n'
    return dxcommon.string2list(opm)
    

