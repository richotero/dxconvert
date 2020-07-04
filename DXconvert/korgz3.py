from . import fourop
from . import fb01
from . import dxcommon

ADJUST = ((16,16,16,16),
        (16,16,16,16),
        (16,16,16,16),
        (16,16,16,16),
        (8,0,8,0),
        (4,4,4,0),
        (4,4,4,0),
        (0,0,0,0))

def z3_to_vmm(Z3):
    z3 = [0]*50
    for i in range(50):
        z3[i] = ((Z3[2*i]&15)<<4) + (Z3[2*i+1]&15)
    vcd, acd, acd2, acd3, delay, efeds = fourop.initvcd(), fourop.initacd(), fourop.initacd2(), fourop.initacd3(), fourop.initdelay(), fourop.initefeds()
    
    vcd[77:87] = z3[:8] + [32, 32]
    NAME = dxcommon.list2string(z3[:8])
    vcd[54] = dxcommon.closeto(z3[8], fb01.LFS) #0~255 ???
    vcd[56] = z3[9] & 127 #PMD
    vcd[57] = z3[10] & 127 #AMD
    vcd[59] = z3[11] & 3 #LFW
    vcd[53] = (z3[12] >> 3) & 7 #FB
    ALG = z3[12] & 7 #ALGORITHM
    vcd[52] = ALG
    vcd[60] = (z3[13] >> 4) & 7 #PMS
    vcd[61] = z3[13] & 3 #AMS
    for oper in range(4):
        opv = (3,1,2,0)[oper]
        op = (3,1,2,0)[oper]
        DT2 = (z3[34+opv] >> 6) & 3 #DT2
        MUL = z3[14+opv] & 15 #MUL
        CRS = fb01.freq_fb01_dx21[4*MUL+DT2]
        vcd[11 + 13*opv] = CRS
        vcd[12 + 13*opv] = ((z3[14+op]) >> 4) & 7 #DT1
        acd[2 + 5*opv] = z3[18+op] & 15 #MUL2
        acd[3 + 5*opv] = (z3[18+op] >> 4) & 7 #OSW
        TL = z3[22+op] & 127 #TL
        OUT = int(round(99*TL/127.))  #?
        OUT += ADJUST[ALG][op]
        vcd[10+13*opv] = min(99, OUT)

        vcd[13*opv] = z3[26+op] & 31 #AR
        vcd[1+13*opv] = z3[30+op] & 31 #D1R
        vcd[2+13*opv] = z3[34+op] & 31 #D2R
        RR = z3[42+op]&15 #RR
        vcd[3+13*opv] = max(1, RR) #RR
        SL = (z3[42+opv] >> 4) & 15 #D1L
        vcd[4+13*opv] = 15 - SL
        vcd[6+13*opv] = (z3[26+op] >> 6) & 3 #RS
        
        vcd[13*opv+8] = (z3[30+op] >> 7) & 1 #AME
        acd[5*opv+4] = (z3[38+op] >> 6) & 3 #EGshift
        RVL = (z3[38+op] >> 3) & 1 #REVlevel
        RVR = z3[38+op] & 7 #REVrate
        acd[20] = RVL * RVR
        
        KVS = (z3[46+op] >> 4) & 15 #KVS
        vcd[9 + 13*opv] = KVS//2
        
        KTR = z3[46+op] & 15 #Ktrack
        vcd[5+13*opv] = KTR*4

    vmm = fourop.vcd2vmm(vcd, acd, acd2, acd3, efeds, delay)
    return vmm

def z3text(Z3, n=0):
    z3 = [0]*50
    for i in range(50):
        z3[i] = ((Z3[2*i]&15)<<4) + (Z3[2*i+1]&15)
    
    s =  "+------+-----------------------+\n"
    NAME = '"{}" ({:03})'.format(dxcommon.list2string(z3[:8]), n)
    s += "| NAME | {:<22}|\n".format(NAME)
    s += "| LFS  | {:<22}|\n".format(z3[8])
    s += "| PMD  | {:<22}|\n".format(z3[9] & 127)
    s += "| AMD  | {:<22}|\n".format(z3[10] & 127)
    s += "| LFW  | {:<22}|\n".format(z3[11] & 3)
    s += "| FB   | {:<22}|\n".format((z3[12] >> 3) & 7)
    ALG = (z3[12] & 7)
    s += "| ALG  | {:<22}|\n".format(ALG+1)
    s += "| PMS  | {:<22}|\n".format((z3[13] >> 4) & 7)
    s += "| AMS  | {:<22}|\n".format(z3[13] & 3)
    # op = (3,1,2,0)
    s += "+------+-----+-----+-----+-----+\n"
    OP1, OP2, OP3, OP4 = "op1", "op2", "op3", "op4"
    for op in range(4):
        if fourop.carrier(ALG, op):
            if op == 0:
                OP1 = OP1.upper()
            if op == 1:
                OP2 = OP2.upper()
            if op == 2:
                OP3 = OP3.upper()
            if op == 3:
                OP4 = OP4.upper()

    s += "|      | {:3} | {:3} | {:3} | {:3} |\n".format(OP1, OP2, OP3, OP4)
    s += "+------+-----+-----+-----+-----+\n"
    MUL4 = z3[14] & 15
    MUL2 = z3[15] & 15
    MUL3 = z3[16] & 15
    MUL1 = z3[17] & 15
    s += "| MUL  | {:03} | {:03} | {:03} | {:03} |\n".format(MUL1,MUL2,MUL3,MUL4)
    DT24  = (z3[34] >> 6) & 3
    DT22  = (z3[35] >> 6) & 3
    DT23  = (z3[36] >> 6) & 3
    DT21  = (z3[37] >> 6) & 3
    s += "| DT2  | {:03} | {:03} | {:03} | {:03} |\n".format(DT21,DT22,DT23,DT24)
 
    CRS1 = fb01.freq_fb01_dx21[4*MUL1+DT21]
    CRS2 = fb01.freq_fb01_dx21[4*MUL2+DT22]
    CRS3 = fb01.freq_fb01_dx21[4*MUL3+DT23]
    CRS4 = fb01.freq_fb01_dx21[4*MUL4+DT24]
    #s += "| CRS  | {:03} | {:03} | {:03} | {:03} |\n".format(CRS1,CRS2,CRS3,CRS4)

    FIN4 = z3[18] & 15
    FIN2 = z3[19] & 15
    FIN3 = z3[20] & 15
    FIN1 = z3[21] & 15
    s += "| MUL2 | {:03} | {:03} | {:03} | {:03} |\n".format(FIN1,FIN2,FIN3,FIN4)
    RAT1 = fourop.freq_4op[16*CRS1+FIN1]
    RAT2 = fourop.freq_4op[16*CRS2+FIN2]
    RAT3 = fourop.freq_4op[16*CRS3+FIN3]
    RAT4 = fourop.freq_4op[16*CRS4+FIN4]
    s += "|=RATIO|{:5.02f}|{:5.02f}|{:5.02f}|{:5.02f}|\n".format(RAT1,RAT2,RAT3,RAT4)
    DET4 = ((z3[14]) >> 4) & 7
    DET2 = ((z3[15]) >> 4) & 7
    DET3 = ((z3[16]) >> 4) & 7
    DET1 = ((z3[17]) >> 4) & 7
    s += "| DET  | {:03} | {:03} | {:03} | {:03} |\n".format(DET1,DET2,DET3,DET4)
    OSW4 = (z3[18] >> 4) & 7
    OSW2 = (z3[19] >> 4) & 7
    OSW3 = (z3[20] >> 4) & 7
    OSW1 = (z3[21] >> 4) & 7
    s += "| OSW  | {:03} | {:03} | {:03} | {:03} |\n".format(OSW1,OSW2,OSW3,OSW4)
    TL4 = z3[22] & 127
    TL2 = z3[23] & 127
    TL3 = z3[24] & 127
    TL1 = z3[25] & 127
    s += "| TL   | {:03} | {:03} | {:03} | {:03} |\n".format(TL1,TL2,TL3,TL4)
    AR4 = z3[26] & 31
    AR2 = z3[27] & 31
    AR3 = z3[28] & 31
    AR1 = z3[29] & 31
    s += "| AR   | {:03} | {:03} | {:03} | {:03} |\n".format(AR1,AR2,AR3,AR4)
    D1R4 = z3[30] & 31
    D1R2 = z3[31] & 31
    D1R3 = z3[32] & 31
    D1R1 = z3[33] & 31
    s += "| D1R  | {:03} | {:03} | {:03} | {:03} |\n".format(D1R1,D1R2,D1R3,D1R4)
    D2R4 = z3[34] & 31
    D2R2 = z3[35] & 31
    D2R3 = z3[36] & 31
    D2R1 = z3[37] & 31
    s += "| D2R  | {:03} | {:03} | {:03} | {:03} |\n".format(D2R1,D2R2,D2R3,D2R4)
    RR4 = z3[42] & 15
    RR2 = z3[43] & 15
    RR3 = z3[44] & 15
    RR1 = z3[45] & 15
    s += "| RR   | {:03} | {:03} | {:03} | {:03} |\n".format(RR1,RR2,RR3,RR4)
    SL4 = 15 - ((z3[42] >> 4) & 15)
    SL2 = 15 - ((z3[43] >> 4) & 15)
    SL3 = 15 - ((z3[44] >> 4) & 15)
    SL1 = 15 - ((z3[45] >> 4) & 15)
    s += "| SL   | {:03} | {:03} | {:03} | {:03} |\n".format(SL1,SL2,SL3,SL4)
    RS4 = (z3[26] >> 6) & 3
    RS2 = (z3[27] >> 6) & 3
    RS3 = (z3[28] >> 6) & 3
    RS1 = (z3[29] >> 6) & 3
    s += "| RS   | {:03} | {:03} | {:03} | {:03} |\n".format(RS1,RS2,RS3,RS4)
    AME4 = (z3[30] >> 7) & 1
    AME2 = (z3[31] >> 7) & 1
    AME3 = (z3[32] >> 7) & 1
    AME1 = (z3[30] >> 7) & 1
    s += "| AME  | {:03} | {:03} | {:03} | {:03} |\n".format(AME1,AME2,AME3,AME4)
    EGS4 = (z3[38] >> 6) & 3
    EGS2 = (z3[39] >> 6) & 3
    EGS3 = (z3[40] >> 6) & 3
    EGS1 = (z3[41] >> 6) & 3
    s += "| EGS  | {:03} | {:03} | {:03} | {:03} |\n".format(EGS1,EGS2,EGS3,EGS4)
    RVL4 = (z3[38] >> 3) & 1
    RVL2 = (z3[39] >> 3) & 1
    RVL3 = (z3[40] >> 3) & 1
    RVL1 = (z3[41] >> 3) & 1
    s += "| RVL  | {:03} | {:03} | {:03} | {:03} |\n".format(RVL1,RVL2,RVL3,RVL4)
    RVR4 = z3[38] & 7
    RVR2 = z3[39] & 7
    RVR3 = z3[40] & 7
    RVR1 = z3[41] & 7
    s += "| RVR  | {:03} | {:03} | {:03} | {:03} |\n".format(RVR1,RVR2,RVR3,RVR4)
    KVS4 = (z3[46] >> 4) & 15
    KVS2 = (z3[47] >> 4) & 15
    KVS3 = (z3[48] >> 4) & 15
    KVS1 = (z3[49] >> 4) & 15
    s += "| KVS  | {:03} | {:03} | {:03} | {:03} |\n".format(KVS1,KVS2,KVS3,KVS4)
    KTR4 = z3[46] & 15
    KTR2 = z3[47] & 15
    KTR3 = z3[48] & 15
    KTR1 = z3[49] & 15
    s += "| KTR  | {:03} | {:03} | {:03} | {:03} |\n".format(KTR1,KTR2,KTR3,KTR4)
    s +=  "+------+-----------------------+\n"
    return s


