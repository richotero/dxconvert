# Inphonik Iconic FM Synthesizer
from . import dxcommon
from . import fourop
from . import fb01
import sys
from math import log

try:
    range = xrange
except NameError:
    pass
import xml.etree.ElementTree as ET

#(108, 77, 71, 67, 62, 44, 8, 5)
#lfs = (3.82, 5.33, 5.77, 6.11, 6.6, 9.23, 46.11, 69.22
lfs = (3.85, 5.40, 5.86, 6.21, 6.71, 9.45, 51.98, 83.16)

paramsOP = ("Vel", "TL", "SSGEG", "RS", "RR", "MW", "MUL",
            "Fixed", "DT", "D2R", "D2L", "D1R", "AR", "AM")
params = ("volume", "Ladder_Effect", "Output_Filtering", "Polyphony", "TimerA",
          "Spec_Mode", "Pitchbend_Range", "Legato_Retrig", "LFO_Speed", "LFO_Enable",
          "Feedback", "FMSMW", "FMS", "DAC_Prescaler", "Algorithm", "AMS", "masterTune")

#TODO feature request upstream to add support for "masterTranspose"

paramID = []
for p in paramsOP:
    for op in (4,3,2,1):
        paramID.append("OP{}{}".format(op, p))
for p in params:
    paramID.append(p)
paramID = tuple(paramID)

def initrym():
    initrym = {"patchName":"Init Patch", "category":"Synth", "rating":3, "type":"User"}
    for i in paramID:
        initrym[i] = 0.0
    initrym["DAC_Prescaler"] = 1.0
    initrym['Ladder_Effect'] = 0.0
    initrym['Output_Filtering'] = 1.0
    initrym['Pitchbend_Range'] = 2.0
    initrym['Polyphony'] = 8.0
    initrym['Spec_Mode'] = 1.0
    initrym['timerA'] = 0.2
    initrym['volume'] = 0.7
    return initrym

def xml2rym(xml):
    root = ET.fromstring(xml)
    rym = initrym()
    rym['patchName'] = root.attrib['patchName']
    rym['category'] = root.attrib['category']
    rym['rating'] = root.attrib['rating']
    rym['type'] = root.attrib['type']

    for child in root:
        if child.attrib['id'] in paramID and child.attrib['id']!='masterTune':
            rym[child.attrib['id']] = float(child.attrib['value'])
    return rym

def rym2xml(rym):
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n\n'
    patchName = patchname2xml(rym['patchName'])
    xml += '<RYM2612Params patchName="{}" category="{}" rating="{}" type="{}">\n'.format(patchName, rym['category'], rym['rating'], rym['type'])
    for i in paramID:
        try: xml += '  <PARAM id="{}" value="{}"/>\n'.format(i, rym[i])
        except: pass

    xml += "</RYM2612Params>\n"
    return xml

def patchname2xml(patchname):
    patchName = ''
    for k in patchname:
        if k == '>':
            k = '&gt;'
        elif k == '<':
            k = '&lt;'
        elif k == '"':
            k = '&quot;'
        elif k == "'":
            k = '&apos;'
        elif k == "&":
            k == '&amp;'
        patchName = patchName + k
    return patchName.strip()

def dB_mastervolume(dB):
    return 0.7 * (10 ** (dB/60))
def mastervolume_dB(volume):
    if volume > 0:
        return 60 * (log(volume/0.7, 10))
    else:
        return -0xffff

def rym2vmm(rym):
    #print("rym2vmm")
    vmm = fourop.initvmm()
    ALG = int(rym['Algorithm'] - 1)
    FB = int(rym['Feedback'])
    opVolume = (0, 0, 0, 0, 6.02, 9.54, 9.54, 12.04)[ALG]
    adjustVolume = 0.75 * (mastervolume_dB(rym['volume']) - opVolume)
    for opi in range(4):
        opad = (0, 20, 10, 30)[opi]
        opad2 = (0, 4, 2, 6)[opi]
        op = opi+1
        vmm[0+opad] = int(rym['OP{}AR'.format(op)])
        vmm[1+opad] = int(rym['OP{}D1R'.format(op)])
        vmm[2+opad] = int(rym['OP{}D2R'.format(op)])
        vmm[3+opad] = int(rym['OP{}RR'.format(op)])
        vmm[4+opad] = int(rym['OP{}D2L'.format(op)])
        #vmm[5+opad] = LS
        AME = int(rym['OP{}AM'.format(op)])
        EBS = 0
        KVS = abs(int(rym['OP{}Vel'.format(op)])) >> 4
        vmm[6+opad] = (AME<<6) + (EBS<<3) + KVS
        
        TL = 127 - int(rym['OP{}TL'.format(op)])
        TLADJ = fb01.TLIMIT[ALG][3-opi]
        TL = TL - TLADJ - (KVS<<4)  
        if fourop.carrier(ALG, 3-opi):
            TL = TL - adjustVolume
        TL = int(round(min(127, max(0, TL))))
        OUT = min(99, max(0, dxcommon.tl2out(TL)))
        vmm[7+opad] = OUT
        
        DET = int(rym['OP{}DT'.format(op)] + 3)
        RS = int(rym['OP{}RS'.format(op)])
        if rym['OP{}Vel'.format(op)] < 0:
            KVS2 = 1
        else:
            KVS2 = 0
        LS2 = 0
        vmm[9+opad] = (LS2<<6) + (KVS2<<5) + (RS<<3) + DET

        FIX = int(rym['OP{}Fixed'.format(op)])
        if FIX == 1:
            freq = max(20, rym['OP{}MUL'.format(op)])
            fixdif = 50000
            for fine in range(16):
                for crs in range(16):
                    for fixrg in range(8):
                        fix = fourop.fix_4op(0, fixrg, crs*4, fine)
                        if abs(fix-freq) < fixdif:
                            fixdif = abs(fix-freq)
                            FINE, CRS, FIXRG = fine, crs*4, fixrg

        else:
            freq = rym['OP{}MUL'.format(op)] / 1000.
            if rym['Spec_Mode'] == 2.0:
                freq = max(0.5, round(freq))
            ratio = dxcommon.closeto(freq, fourop.freq_4op, True)
            CRS = ratio // 16
            FINE = ratio % 16
            FIXRG = 0

        FIXRM = 0
        EGSFT = 0
        vmm[8+opad] = CRS
        vmm[73+opad2] = (FIXRM<<6) + (EGSFT<<5) + (FIX<<3) + FIXRG
        OSW = 0
        vmm[74+opad2] = (OSW<<4) + FINE
        CRS = vmm[8+opad]
        FINE = vmm[74+opad2] & 15
    SY = 0
    vmm[40] = (SY<<6) + (FB<<3) + ALG
    vmm[41] = dxcommon.closeto(lfs[int(rym['LFO_Speed'])], fourop.lfs)

    #vmm[42] = LFD
    if rym['LFO_Enable']:
        vmm[43] = 15 #PMD
        vmm[44] = 15  #AMD
    PMS = int(rym['FMS'])
    AMS = int(rym['AMS'])
    LFW = 2
    vmm[45] = (PMS<<4) + (AMS<<2) + LFW
    #TODO TRPS = rym['masterTranspose'] = TRPS
    #vmm[46] = TRPS + 24
    vmm[47] = int(max(0, rym['Pitchbend_Range']))
    #vmm[48] = (CH<<4) + (MO<<3) + (SU<<2) + (PO<<1) + PM
    #vmm[49] = PORT
    #vmm[50] = FCVOL
    vmm[51] = max(0, min(99, int(rym['FMSMW']))) #MWPITCH
    #vmm[52] = MWAMPLI
    #vmm[53] = BCPITCH
    #vmm[54] = BCAMPLI
    #vmm[55] = BCPBIAS
    #vmm[56] = BCEBIAS
    pname = rym['patchName'].strip()
    if len(pname) > 10:
        pnm = ''
        for k in pname:
            if k != ' ':
                pnm += k
        pname = pnm
    pname = pname + "          "
    vmm[57:67] = dxcommon.string2list(pname)[:10]
    #vmm[67] = PR1
    #vmm[68] = PR2
    #vmm[69] = PR3
    #vmm[70] = PL1
    #vmm[71] = PL2
    #vmm[72] = PL3
    #vmm[81] = REV
    #vmm[82] = FCPITCH
    #vmm[83] = FCAMPLI
    #vmm[84] = ATPITCH
    #vmm[85] = ATAMPLI
    #vmm[86] = ATPBIAS
    #vmm[87] = ATEGBIAS
    #vmm[88] = reserved
    #vmm[89] = reserved
    #vmm[90] = DS55DELAY
    #vmm[91] = YSFXPRESET
    #vmm[92] = YSFXTIME
    #vmm[93] = YSFXBALANCE
    #vmm[94) = V50FXSEL
    #vmm[95] = V50FXBALANCE
    #vmm[96] = V50FXOUTLEVEL
    #vmm[97] = V50FXSTEREOMIX
    #vmm[98] = V50FXPARAM1
    #vmm[99] = V50FXPARAM2
    #vmm[100] = V50FXPARAM3
    return vmm

def vmm2rym(vmm):
    #print("vmm2rym")
    rym = initrym()

    rym['patchName'] = dxcommon.list2string(vmm[57:67]).strip()
    rym['category'] = 'Synth'
    rym['rating'] = '3'
    rym['type'] = 'RYMCONVERT'

    ALG = vmm[40] & 7
    rym['Algorithm'] = float(1+ALG)

    rym['AMS'] = (vmm[45] >> 2) & 3
    amd = vmm[44]
    if amd < 50:
        rym['AMS'] = float(round(amd / 50  * rym['AMS']))

    rym['FMS'] = (vmm[45] >> 4) & 7
    pmd = vmm[43]
    if pmd < 16:
        rym['FMS'] = float(round(pmd / 16 * rym['FMS']))

    rym['FMSMW'] = float(vmm[51])
    rym['Feedback'] = float((vmm[40] >> 3) & 7)
    if vmm[43] > 3:
        rym['LFO_Enable'] = 1.0
    LFS = dxcommon.closeto(fourop.lfs[vmm[41]], lfs, True)
    rym['LFO_Speed'] = float(LFS)
    rym['Ladder_Effect'] = 0.0
    rym['Legato_Retrig'] = 0.0
    rym['Spec_Mode'] = 2.0
    rym['Output_Filtering'] = 0.0
    rym['Pitchbend_Range'] = float(vmm[47])
    if (vmm[48] >> 3) & 1 == 0:
        rym['Polyphony'] = 8.0
    else:
        rym['Polyphony'] = 1.0
    rym['TimerA'] = 0.0
    rym['masterTune'] = 0.0
    rym['volume'] = 0.7
 
    TRPS = vmm[46] - 24
    #TODO rym['masterTranspose'] = TRPS
    if vmm[46] % 12 == 0:
        TRPS = 1
    else:
        TRPS = 2 ** (TRPS/12)

    for opi in range(4):
        op = opi+1
        opad = (0, 20, 10, 30)[opi]
        opad2 = (0, 4, 2, 6)[opi]
        rym['OP{}AM'.format(op)] = float(vmm[6+opad] >> 6)
        rym['OP{}AR'.format(op)] = float(vmm[0 + opad] & 31)
        rym['OP{}D1R'.format(op)] = float(vmm[1 + opad] & 31)
        rym['OP{}D2L'.format(op)] = float(vmm[4 + opad] & 15)
        rym['OP{}D2R'.format(op)] = float(vmm[2 + opad] & 31)
        rym['OP{}MW'.format(op)] = 0.0
        rym['OP{}RR'.format(op)] = float(vmm[3 + opad] & 15)
        rym['OP{}RS'.format(op)] = float((vmm[9 + opad] >> 3) & 3)
        rym['OP{}SSGEG'.format(op)] = 0.0

        #operator ratio/frequency
        CRS = vmm[8 + opad] & 63
        FIXRM = (vmm[73 + opad2] >> 6) & 1
        FIX = (vmm[73 + opad2] >> 3) & 1
        FIXRG = vmm[73 + opad2] & 7
        FINE = vmm[74 + opad2] & 15
        if FIX == 1:
            rym['Spec_Mode'] = 1.0
            rym['OP{}Fixed'.format(op)] = 1.0
            freq = fourop.fix_4op(FIXRM, FIXRG, CRS, FINE)
        else:
            rym['OP{}Fixed'.format(op)] = 0.0
            freq = 1000. * fourop.freq_4op[16*CRS+FINE]
            if freq not in (0.0, 500.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0, 9000.0, 10000.0, 11000.0, 12000.0, 13000.0, 14000.0, 15000.0):
                rym['Spec_Mode'] = 1.0
        freq = freq*TRPS
        rym['OP{}MUL'.format(op)] = freq
        rym['OP{}DT'.format(op)] = float(vmm[9+opad]-3)
         
        KVS = 8 * (vmm[opad+6] & 7)
        KVS2 = (vmm[opad+9] >> 5) & 1 #V50 kvs sign
        if KVS2 == 1:
            KVS = -KVS
        rym['OP{}Vel'.format(op)] = float(KVS)
        OUT = vmm[opad+7]
        TL = 127 - dxcommon.out2tl(OUT)
        TLADJ = fb01.TLIMIT[ALG][3-opi]
        LS = vmm[opad+5] // 11
        LSSIGN = (1,-1)[vmm[opad+9] >> 6] #LS SIGN V50
        TL = min(127, max(0, TL - TLADJ - KVS - LSSIGN*LS))
        rym['OP{}TL'.format(op)] = float(TL)

    ottava=False
    for op in (1,2,3,4):
        if (rym['OP{}MUL'.format(op)] < 500) and (rym['OP{}Fixed'.format(op)] == 0.0):
            ottava=True
    if ottava:
        rym['OP1MUL'] *= 2
        rym['OP2MUL'] *= 2
        rym['OP3MUL'] *= 2
        rym['OP4MUL'] *= 2

    for op in (1,2,3,4):
        if rym['OP{}Fixed'.format(op)] == 0.0:
            if rym['OP{}MUL'.format(op)] <= 500:
                rym['OP{}MUL'.format(op)] = 0.0
    return rym


def fb2rym(fb):
    #print(fb2rym)
    rym = initrym()
    rym['patchName'] = dxcommon.list2string(fb[:7]).strip()
    rym['category'] = 'FB01'
    rym['rating'] = '3'
    rym['type'] = 'User'

    rym['AMS'] = float(fb[0x0d] & 3)
    amd = fb[0x09]&127
    if amd < 64:
        rym['AMS'] = float(round(amd / 64 * rym['AMS']))

    rym['FMS'] = fb[0x0d] >> 4
    pmd = fb[0x0a] & 127
    if pmd < 20:
        rym['FMS'] = float(round(pmd / 20 * rym['FMS']))

    ALG = fb[0x0c] & 7
    rym['Algorithm'] = float(1+ALG)
    if (fb[0x3b] >> 4) > 0:
        rym['FMSMW'] = 100.0
    else:
        rym['FMSMW'] = 0.0
    rym['Feedback'] = float((fb[0x0c] >> 3) & 7)
    if (fb[0x0a] & 127) > 3:
        rym['LFO_Enable'] = 1.0
    LFS = dxcommon.closeto(fb01.lfs[fb[0x08]], lfs, True)
    rym['LFO_Speed'] = float(LFS)
    rym['Ladder_Effect'] = 0.0
    rym['Legato_Retrig'] = 0.0
    rym['Spec_Mode'] = 2.0
    
    TRPS = fb[0x0f]
    if TRPS > 127:
        TRPS = TRPS - 256
    while TRPS > 24:
        TRPS -= 12
    while TRPS < -24:
        TRPS += 12
    if TRPS % 12 == 0:
        TRPS = 1
    else:
        TRPS = 2 ** (TRPS/12)
    for opi in range(4):
        op = opi+1
        fop = (16,24,32,40)[opi]
        rym['OP{}AM'.format(op)] = float(fb[0x05+fop] >> 7)
        rym['OP{}AR'.format(op)] = float(fb[0x04+fop] & 31)
        rym['OP{}D1R'.format(op)] = float(fb[0x05+fop] & 31)
        rym['OP{}D2L'.format(op)] = float(15 - (fb[0x07+fop] >> 4))
        rym['OP{}D2R'.format(op)] = float(fb[0x06+fop] & 31)
        DT = (0,1,2,3,0,-1,-2,-3)[(fb[0x03+fop] >> 4) & 7]
        rym['OP{}DT'.format(op)] = float(DT)
        rym['OP{}Fixed'.format(op)] = 0.0

        mul = fb[0x03+fop] & 15
        ih = fb[0x06+fop] >> 6
        if ih>0:
            rym['Spec_Mode'] = 1.0
        ratio = fb01.freq_fb01[4*mul+ih]
        ratio = ratio*TRPS
        freq = 1000.*ratio
        if freq not in (0.0, 500.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0, 9000.0, 10000.0, 11000.0, 12000.0, 13000.0, 14000.0, 15000.0):
            rym['Spec_Mode'] = 1.0
        rym['OP{}MUL'.format(op)] = float(freq)
        rym['OP{}MW'.format(op)] = 0.0
        rym['OP{}RR'.format(op)] = float(fb[0x07+fop] & 15)
        rym['OP{}RS'.format(op)] = float(fb[0x04+fop] >> 6)
        rym['OP{}SSGEG'.format(op)] = 0.0
        KVS = (fb[0x01+fop] >> 4) & 7
        KVS = KVS*4
        rym['OP{}Vel'.format(op)] = float(KVS)
        TL = 127 - fb[0x00 + fop]
        TLADJ = fb[0x02 + fop] & 15
        #LSTYPE 0,1,2,3 = -LIN, +LIN, -EXP, +EXP
        LSSIGN = (1,-1)[fb[0x01 + op] >> 7] #LS sign
        LSTYPE = (fb[0x03 + op] >> 7) #LS type Linear, Exponential
        LS = fb[0x02+fop] >> 4
        rym['OP{}TL'.format(op)] = float(min(127,max(0, TL-TLADJ-KVS-LS*LSSIGN)))
    rym['Output_Filtering'] = 0.0
    rym['Pitchbend_Range'] = float(fb[0x3b] & 15)
    if (fb[0x3a] >> 7) & 1 == 0:
        rym['Polyphony'] = 8.0
    else:
        rym['Polyphony'] = 1.0
 
    rym['Spec_Mode'] = 1.0
    rym['TimerA'] = 0.0
    rym['masterTune'] = 0.0
    rym['volume'] = 0.7
    ottava=False
    for op in (1,2,3,4):
        if rym['OP{}MUL'.format(op)] < 500:
            ottava=True
    if ottava:
        rym['OP1MUL'] *= 2
        rym['OP2MUL'] *= 2
        rym['OP3MUL'] *= 2
        rym['OP4MUL'] *= 2
    for op in (1,2,3,4):
        if rym['OP{}MUL'.format(op)] <= 500:
            rym['OP{}MUL'.format(op)] = 0.0
    return rym

def rym2fb(rym):
    #print("rym2fb")
    ALG = int(rym['Algorithm'] - 1)
    FB = int(rym['Feedback'])
    fb = fb01.initfb()
    pname = rym['patchName'].strip()
    if len(pname) > 7:
        pnm = ''
        for k in pname:
            if k != ' ':
                pnm += k
        pname = pnm
    pname = pname + "       "
    fb[:7] = dxcommon.string2list(pname)[:7]
    fb[7] = 0
    LFS = int(rym['LFO_Speed'])
    fb[8] = dxcommon.closeto(lfs[LFS], fb01.lfs, True)
    if rym['LFO_Enable']:
        LFOLOAD, AMD = 1, 19
        fb[9] = (LFOLOAD << 7) + AMD
        LFSYNC, PMD = 1, 19
        fb[0x0a] = (LFSYNC << 7) + PMD
    fb[0x0b] = 0b01111000 #operator enable 
    fb[0x0c] = (FB << 3) + ALG
    PMS, AMS = int(rym['FMS']), int(rym['AMS']) 
    fb[0x0d] = (PMS << 4) + AMS
    LFW = 2 #Triangle
    fb[0x0e] = (LFW << 5)
    #TODO TRPS = rym['masterTranspose']
    fb[0x0f] = 0 #TRPS
    if rym['Polyphony'] == 1.0:
        MONO = 1
    else:
        MONO = 0
    PORTATIME = 0
    fb[0x3a] = (MONO << 7) + PORTATIME
    ASGN, PBR = 2, int(rym['Pitchbend_Range']) #MW PITCH
    fb[0x3b] = (ASGN << 4) + PBR

    ALG = int(rym['Algorithm'] - 1)
    opVolume = (0, 0, 0, 0, 6.02, 9.54, 9.54, 12.04)[ALG]
    adjustVolume = 0.75 * (mastervolume_dB(rym['volume']) - opVolume)

    for opi in range(4):
        op = opi+1
        fop = (16, 24, 32, 40)
        
        TL = 127 - int(rym['OP{}TL'.format(op)])
        KVS = int(rym['OP{}Vel'.format(op)]) << 4
        TL = TL - KVS/4
        if fourop.carrier(3-opi, ALG):
            TL = TL - adjustVolume
        TL = int(round(min(127, max(0, TL))))
        fb[0 + fop] = TL
        
        LStype0 = fb[1+fop] >> 7
        fb[1 + fop] = (LStype0 << 7) + (KVS << 4)
        #fb[2 + fop] = (LSdepth << 4) + TLadjust

        if rym['OP{}Fixed'.format(op)] == 0.0:
            ratio = rym['OP{}MUL'.format(op)]/1000
        else:
            ratio = rym['OP{}MUL'.format(op)]/261.6256
        if rym['Spec_Mode'] == 2.0:
            ratio = max(0.5, round(ratio))
        MUL = dxcommon.closeto(ratio, freq_fb01) // 4
        DT1 = dxcommon.closeto(ratio, freq_fb01) % 4
        LStype1 = fb[3+fop] >> 7
        fb[3 + fop] = (LStype1 << 7) + (DT1 << 4) + MUL
        RS, AR = int(rym['OP{}RS'.format(op)]), int(rym['OP{}AR'.format(op)])
        fb[4 + fop] = (RS << 5) + AR
        AME, KVSAR, D1R = int(rym['OP{}AM'.format(op)]), 0, int(rym['OP{}D1R'.format(op)])                                           
        fb[5 + fop] = (AME << 7) + (KVSAR << 5) + D1R
        DT2 = int(rym['OP{}DT'.format(op)])
        if DT2 < 0:
            DT2 = 4 - DT2
        DT2 = int(rym['OP{}D2R'.format(op)])
        fb[6 + fop] = (DT2 << 6) + D2R
        SL, RR = int(rym['OP{}D2L'.format(op)]), int(rym['OP{}RR'.format(op)])
        fb[7 + fop] = (SL << 4) + RR
    return(fb)

def rdxalg(algi, opi):
    alg = (0, 1, 2, 2, 7, 8, 10, 11)[algi]
    if algi == 3:
        op = (3, 0, 2, 1)[opi]
    else:
        op = 3-opi
    opad = 28*op + 38
    return alg, op, opad

def rym2rdx(rym):
    from . import reface
    vmm = rym2vmm(rym)
    rdx = reface.vmm2rdx(vmm)
    LFS = int(rym['LFO_Speed'])
    rdx[0x12] = dxcommon.closeto(lfs[LFS], reface.lfs, True)
    ALG = int(rym['Algorithm']-1)
    for opi in range(4):
        OP = opi+1
        alg, op, opad = rdxalg(ALG, opi) #Reface
        FIXED = int(rym['OP{}Fixed'.format(OP)])
        rdx[opad+0x15] = FIXED
        MUL = rym['OP{}MUL'.format(OP)]

        if FIXED == 0:
            freq = max(0.5, MUL/1000)
            if rym['Spec_Mode'] == 2.0:
                freq = max(0.5, round(freq))
        else:
            freq = max(20, MUL)
        crs = int(freq)
        if crs > 0:
            fine = int(round(100*((freq) - crs)))
        else:
            fine = int(round(200*((freq) - 0.5)))
        rdx[opad+0x16] = min(31, crs)
        rdx[opad+0x17] = min(99, fine)
    return rdx


