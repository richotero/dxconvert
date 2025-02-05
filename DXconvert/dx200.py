from . import dx7
try:
    range = xrange
except NameError:
    pass

def dx2tovmem(dx2):
    vmem = dx7.initvmem()
    for op in range(6):
        for i in range(8):
            vmem[17*(5-op)+i] = dx2[35*op+76+i] #EG: R1~4 L1~4
        vmem[17*(5-op)+8] = max(0, dx2[35*op+84]-21) # BP
        vmem[17*(5-op)+9] = dx2[35*op+87]   # LD
        vmem[17*(5-op)+10] = dx2[35*op+88]  # RD
        vmem[17*(5-op)+11] = dx2[35*op+85] + (dx2[35*op+86]<<2) # LC, RC
        vmem[17*(5-op)+12] = dx2[35*op+89] + (dx2[35*op+75]<<3) # RS, PD
        vmem[17*(5-op)+13] = min(3, dx2[35*op+71]) + (dx2[35*op+91]<<2)  # AMS, TS
        vmem[17*(5-op)+14] = dx2[35*op+90]  # TL
        vmem[17*(5-op)+15] = dx2[35*op+72] + (dx2[35*op+73]<<1) # PM, PC
        vmem[17*(5-op)+16] = dx2[35*op+74]  # PF
    for i in range(4):  # PEG RATE 1~4
        vmem[102+i] = dx2[26+i]
    for i in range(4):  # PEG LEVEL 1~4
        vmem[106+i] = dx2[32+i]
    vmem[110] = dx2[17] # ALS
    vmem[111] = dx2[18] + (dx2[38]<<3)  # FBL, OPI (SYNC)
    for i in range(4):  # LFS, LFD, LPMD, LAMD
        vmem[112+i] = dx2[20+i]
    vmem[116] = dx2[24] + (dx2[19]<<1) + (dx2[25]<<4)   # LFKS, LFW, LPMS
    vmem[117] = max(0, dx2[37]-36)   # TRNP
    for i in range(10): # NAME 
        vmem[118+i] = max(32, dx2[i])
    
    return dx7.cleanvmem(vmem)


def dx2toamem(dx2):
    amem = dx7.initamem()
    amem[1] = dx2[246] + (dx2[211]<<3)
    amem[2] = dx2[176] + (dx2[141]<<3)
    amem[3] = dx2[106] + (dx2[71]<<3)
    amem[4] = dx2[36] + (dx2[69]<<2) + (dx2[65]<<3) + (dx2[66]<<4)
    amem[5] = dx2[59] + (dx2[68]<<1) + (dx2[60]<<2)
    amem[6] = dx2[61] # + PitchBendMode *16
    amem[7] = dx2[62] + (dx2[63]<<1)
    amem[8] = dx2[64]
    amem[24] = dx2[30]
    amem[34] = dx2[67] # + FCCS1 *8
    return dx7.cleanamem(amem)

