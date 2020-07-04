from . import dx7
from . import reface
from . import fourop
from . import fb01
from os import path
from . import dxcommon
try:
    range = xrange
except NameError:
    pass

def pss2vmem(pss, infile, voicename=''):
    vced = dx7.initvced()
    vced[112] = 32
    vced[145:155] = [0x20]*10
    vced[134]=4 # Algorithm 5

    if voicename:
        NAME = voicename.strip()
        if len(NAME) > 10:
            NAME = NAME.replace(' ','')
            NAME = NAME.ljust(10)[:10]
    else:
        NAME = path.split(infile)[1]
        NAME = path.splitext(NAME)[0]
        NAME = NAME[:10].ljust(10)
        #NAME = NAME[3:13].ljust(10)
    for k in range(len(NAME)):
        vced[145+k] = ord(NAME[k])

    FB = (pss[15]>>3) & 7
    vced[135] = FB*2
    V = (pss[24]>>7)&1
    PMS = ((pss[16]>>4)&7)*V
    vced[143] = PMS
    AMS = pss[16]&3
    VDT = pss[22]&127
    vced[113] = int(round(99*VDT/127.))
    vced[138] = VDT
    vced[139] = 20 # LPMD
    vced[140] = 20 # LAMD
    vced[142] = 4 #LFW = sin
    S = (pss[24]>>6)&1 #Sustain Enable

    for op in range(2): #0=Modulator 1=Carrier
        dxop = 21*op
        DT1 = (pss[op+1]>>4)&7
        if pss[op+1]>127: 
            DT1 = -1*DT1
        DT2 = (pss[op+9]>>6)&1
        MUL = pss[op+1]&15
        vced[18+dxop] = MUL
        vced[19+dxop] = DT2*50
        vced[20+dxop] = DT1+7

        TL = pss[op+3]&127
        TL = max(0, TL - 8)
        #vced[16+dxop] = fb01.out[TL]
        vced[16+dxop] = dxcommon.tl2out(TL)
        
        LKSL = pss[op+5]&15
        LKSH = (pss[op+5]>>4)&15
        RKS = (pss[op+7]>>6)&3
        vced[13+dxop] = 2*RKS

        if LKSL==0:
            vced[11+dxop]=0
        elif LKSL>7: # LC=-LIN
            vced[11+dxop] = 0
            vced[dxop+9] = (LKSL-7)*4
        elif LKSL<8: # LC=+LIN
            vced[11+dxop] = 3
            vced[dxop+9] = (8-LKSL)*4

        if LKSH==0:
            vced[11+dxop] = 0
        elif LKSH<4: # RC=+LIN
            vced[11+dxop] = 3
            vced[op+10] = (4-LKSH)*4
        elif LKSH>10: #RC=-EXP
            vced[11+dxop] = 1
            vced[dxop+10] = (LKSH-10)*4
        elif LKSH>3: #RC=-LIN
            vced[11+dxop] = 0
            vced[dxop+10] = (LKSH-3)*4
        vced[8+dxop] = 27 #BP = C3
        
        AMEN = (pss[op+9]>>7)&1
        vced[14+dxop] = AMS*AMEN

        AR = pss[op+7]&63 # 63?
        D1R = pss[op+9]&63 # 63?
        D2R = pss[op+11]&63 # 63?
        D1L = (pss[op+13]>>4)&15
        RR = pss[op+13]&15
        SRR = pss[op+20]&15
        factor=99./63.
        '''
        vced[0+dxop] = int(factor*AR)
        vced[1+dxop] = int(factor*D1R)
        vced[2+dxop] = int(factor*D2R)
        '''
        vced[0+dxop] = fourop.r1[AR>>1]
        vced[1+dxop] = fourop.r2[D1R>>1]
        vced[2+dxop] = fourop.r3[D2R>>1]
        vced[3+dxop] = fourop.r4[RR]
        vced[4+dxop] = 99
        vced[5+dxop] = fourop.l2[15-D1L]
        if D2R == 0:
            vced[6+dxop] = fourop.l2[15-D1L]
        else:
            vced[6+dxop] = 0
        vced[7+dxop] = 0
        # SINTBL = (pss[op+11]>>6)&3

    ''
    vced[42:84] = vced[84:126] = vced[:42]
    vced[58] = vced[79] = vced[100] = vced[121] = 0 #Level op1-4 

    return dx7.vced2vmem(vced)

def pss2vmm(pss, infile, voicename=''):
    vmm = fourop.initvmm()
    vmm[57:67] = [0x20]*10

    ALG = 4
    FBL = (pss[15]>>3) & 7

    vmm[40] = ALG + (FBL<<3)
    vmm[41] = 30 #LFS
    if voicename:
        NAME = voicename.strip()
        if len(NAME) > 10:
            NAME = NAME.replace(' ','')
            NAME = NAME[:10]
    else:
        NAME = path.split(infile)[1]
        NAME = path.splitext(NAME)[0]
        #NAME = NAME[3:13].ljust(10)
        NAME = NAME[:10].ljust(10)
        
    for k in range(len(NAME)):
        vmm[57+k] = ord(NAME[k])

    V = (pss[24]>>7)&1
    PMS = ((pss[16]>>4)&7)*V
    AMS = pss[16]&3
    LFW = 2 #tri
    vmm[45] = (PMS<<4) + (AMS<<2) + LFW

    VDT = pss[22]&127
    vmm[42] = int(round(VDT*99/127.))

    vmm[43] = 20 # PMD
    vmm[44] = 20 # AMD
    S = (pss[24]>>6)&1


    for op in range(2):   #0=Modulator 1=Carrier
        txop=(0, 20)[op]   #OP4>OP3
        #txop=(10, 30)[op] #OP2>OP1
        DET = (pss[op+1]>>4) & 15
        det = (3,3,4,4,5,5,6,6,3,3,2,2,1,1,0,0)[DET]
        RS = (pss[op+7]>>6)&3
        vmm[9+txop] = det + (RS<<3)
        
        DT2 = (pss[op+9]>>6)&1
        MUL = pss[op+1]&15
        vmm[txop+8] = (0, 1, 4, 5, 8, 9, 10, 14, 
            13, 18, 16, 23, 19, 26, 22, 30, 
        25, 35, 28, 39, 31, 44, 34, 46, 
        26, 49, 40, 52, 42, 55, 45, 58)[2*MUL+DT2] 
    
        TL = pss[op+3]&127
        vmm[txop+7] = dxcommon.tl2out(TL) 
        
        LKSL = pss[op+5]&15
        LKSH = (pss[op+5]>>4)&15
        
        '''
        if LKSL==0:
            vced[11+dxop]=0
        elif LKSL>7: # LC=-LIN
            vced[11+dxop] = 0
            vced[dxop+9] = (LKSL-7)*4
        elif LKSL<8: # LC=+LIN
            vced[11+dxop] = 3
            vced[dxop+9] = (8-LKSL)*4

        if LKSH==0:
            vced[11+dxop] = 0
        elif LKSH<4: # RC=+LIN
            vced[11+dxop] = 3
            vced[op+10] = (4-LKSH)*4
        elif LKSH>10: #RC=-EXP
            vced[11+dxop] = 1
            vced[dxop+10] = (LKSH-10)*4
        elif LKSH>3: #RC=-LIN
            vced[11+dxop] = 0
            vced[dxop+10] = (LKSH-3)*4
        vced[8+dxop] = 27 #BP = C3
        '''

        AME = (pss[op+9]>>7)&1
        vmm[6+txop] = AME<<6


        AR = pss[op+7]&63 # 63?
        D1R = pss[op+9]&63 # 63?
        D2R = pss[op+11]&63 # 63?
        D1L = (pss[op+13]>>4)&15
        RR = pss[op+13]&15
        SRR = pss[op+20]&15
        vmm[0+txop] = AR>>1
        vmm[1+txop] = D1R>>1
        vmm[2+txop] = D2R>>1
        vmm[3+txop] = max(1, RR)
        vmm[4+txop] = 15 - D1L
        
    vmm[10:20] = vmm[0:10]
    vmm[30:40] = vmm[20:30]
    vmm[37] = vmm[17] = 0

    # SINTBL --> OSW
    osw4 = osw2 = (pss[op+11]>>6)&3
    osw3 = osw1 = (pss[op+12]>>6)&3
    vmm[74] = osw4<<4
    vmm[76] = osw2<<4
    vmm[78] = osw3<<4
    vmm[80] = osw1<<4
    for i in range(128):
        vmm[i] = vmm[i] & 127
    return vmm

def pss2rdx(pss, voicename):
    vmm = pss2vmm(pss, voicename)
    rdx = reface.vmm2rdx(vmm)
    rdx[38:38+2*28] = rdx[38+2*28:38+4*28]
    
    #Carrier
    SINTBL = pss[12]>>6
    rdx[38 + 0x14] = rdx[38 + 28*2 + 0x14] = SINTBL % 2 #FB Type
    rdx[38 + 0x13] = (0, 32, 32, 32)[SINTBL] #FB
    rdx[38 + 28*2 + 0x13] = rdx[38 + 0x13]

    #Modulator
    FB = (pss[15]>>3) & 7
    SINTBL = pss[11]>>6
    rdx[38 + 28 + 0x14] = rdx[38 + 28*3 + 0x14] = SINTBL % 2 #FB Type
    rdx[38 + 28 + 0x13] = (0, 16, 32, 48)[SINTBL] + 8*FB
    rdx[38 + 28*3 + 0x13] = rdx[38 + 28 + 0x13]
    return rdx

def pss2txt(pss, fname):
    ON = ("OFF", "ON")
    SIGN = ("+", "-")
    txt =  "PSS-480 voice parameters\n"
    txt += "{}\n".format(fname)
    if pss[0]>4:
        pss[0] = 0
    txt += "BANK NUMBER: {}\n".format(pss[0]+1)
    txt += "FB         : {}\n".format((pss[15]>>3)&7)
    txt += "PMS        : {}\n".format((pss[16]>>4)&7)
    txt += "AMS        : {}\n".format(pss[16]&3)
    txt += "VDT        : {}\n".format(pss[22]&127)
    txt += "VIB        : {}\n".format(ON[pss[24]>>7])
    txt += "SUS        : {}\n\n".format(ON[(pss[24]>>6)&1])

    txt += "             MOD       CAR\n"
    txt += "MUL        : {:<10}{:<10}\n".format(pss[1]&7, pss[2]&7)
    txt += "DT2(coarse): +{:<9}+{:<5}cents\n".format(600*(pss[9]>>6), 600*(pss[10]>>6))
    txt += "DT1(fine)  : {}{:<9}{}{:<9}\n".format(
            SIGN[pss[1]>>7],
            (pss[1]>>4)&15,
            SIGN[pss[2]>>7],
            (pss[2]>>4)&15)
    txt += "TL         : {:<10}{:<10}\n".format(pss[3]&127, pss[4]&127)
    txt += "LKS(LO)    : {:<10}{:<10}\n".format(pss[5]&15, pss[6]&15)
    txt += "LKS(HI)    : {:<10}{:<10}\n".format((pss[5]>>4)&15, (pss[6]>>4)&15)
    txt += "RKS        : {:<10}{:<10}\n".format(pss[7]>>6, pss[8]>>6)
    txt += "AR         : {:<10}{:<10}\n".format(pss[7]&63, pss[8]&63)
    txt += "D1R        : {:<10}{:<10}\n".format(pss[9]&63, pss[10]&63)
    txt += "D2R        : {:<10}{:<10}\n".format(pss[11]&63, pss[12]&63)
    txt += "D1L        : {:<10}{:<10}\n".format(pss[13]>>4, pss[14]>>4)
    txt += "RR         : {:<10}{:<10}\n".format(pss[13]&31, pss[14]&31)
    txt += "SRR        : {:<10}{:<10}\n".format(pss[20]&15, pss[21]&15)
    txt += "AME        : {:<10}{:<10}\n".format(ON[pss[9]>>7], ON[pss[10]>>7])
    SINTBL = ("SIN", "SQRSIN", "SINHLF", "SQRSINHLF")
    txt += "SINTBL     : {:<10}{:10}\n".format(SINTBL[pss[11]>>6], SINTBL[pss[11]>>6])
    return txt

