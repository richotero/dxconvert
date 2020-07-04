from . import dx7
try:
    range = xrange
except NameError:
    pass

# initpced:
def initpced():
    initpced = [0]*94
    initpced[1] = 1
    for i in (3, 26):
        initpced[i] = 7
    for i in (9, 11, 13):
        initpced[i] = 8
    initpced[15] = 15
    initpced[30:60] = initpced[:30]
    for i in range(30):
        initpced[i+64] = ord(" YAMAHA  TX7  FUNCTION  DATA  "[i])
    return initpced

def initpmem():
    initpmem = [0, 7, 0, 0, 8, 8, 8, 15, 0, 0, 0, 0, 0, 0, 7, 0, 
            0, 7, 0, 0, 8, 8, 8, 15, 0, 0, 0, 0, 0, 0, 7, 0, 
            0, 0, 32, 89, 65, 77, 65, 72, 65, 32, 32, 84, 88, 55, 32, 32, 
            70, 85, 78, 67, 84, 73, 79, 78, 32, 32, 68, 65, 84, 65, 32, 32]
    return initpmem

def pced2pmem(pced):
    pmem = [0]*64
    for v in range(2):
        pmem[0+16*v] = (pced[2+30*v]&1)*64
        pmem[1+16*v] = (pced[3+30*v]&15) + ((pced[4+30*v]&7)*16)
        pmem[2+16*v] = pced[5+30*v]&127
        pmem[3+16*v] = (pced[6+30*v]&1) + (pced[7+30*v]&1)*2
        pmem[4+16*v] = (pced[9+30*v]&15) + (pced[10+30*v]&7)*16
        pmem[5+16*v] = (pced[11+30*v]&15) + (pced[12+30*v]&7)*16
        pmem[6+16*v] = (pced[13+30*v]&15) + (pced[14+30*v]&7)*16
        pmem[7+16*v] = (pced[15+30*v]&15) + (pced[16+30*v]&7)*16
        pmem[14+16*v] = pced[26+30*v]
        pmem[15+16*v] = (pced[4+30*v]&0b1000)*8
    pmem[32] = (pced[61]&1)*4
    #pmem[16:32] = pmem[:16]
    pmem[34:64] = pced[64:94]
    return pmem

def pmem2pced(pmem):
    if len(pmem) == 0:
        pmem = initpmem()
    pced = [0]*94
    for v in range(2):
        pced[2+30*v] = (pmem[0+16*v]&64)//64
        pced[3+30*v] = pmem[1+16*v]&15
        pced[4+30*v] = ((pmem[1+16*v]&0b1110000)//16) + ((pmem[15+16*v]&64)//8)
        pced[5+30*v] = pmem[2+16*v]&127
        pced[6+30*v] = pmem[3+16*v]&1
        pced[7+30*v] = (pmem[3+16*v]&3)//2
        pced[9+30*v] = pmem[4+16*v]&15
        pced[10+30*v] = (pmem[4+16*v]&1110000)//16
        pced[11+30*v] = pmem[5+16*v]&15
        pced[12+30*v] = (pmem[5+16*v]&1110000)//16
        pced[13+30*v] = pmem[6+16*v]&15
        pced[14+30*v] = (pmem[6+16*v]&1110000)//16
        pced[15+30*v] = pmem[7+16*v]&15
        pced[16+30*v] = (pmem[7+16*v]&1110000)//16
        pced[26+30*v] = pmem[14+16*v]
    #pced[30:60] = pced[:30]
    pced[61] = (pmem[32]//4)&1
    pced[64:94] = pmem[34:64]
    return pced

def cleanpced(pced):
    pmax=(0, 0, 1, 12, 12, 99, 1, 1, 1, 15, 7, 15, 7, 15, 7, 15, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0)*2 + (0, 1, 0, 0) + (127, )*30
    for i in range(94):
        pced[i] = min(pced[i], pmax[i])
    for i in range(64, 94):
        pced[i] = min(127, max(32, pced[i]))
    return pced

def cleanpmem(pmem):
    pced = pmem2pced(pmem)
    pced = cleanpced(pced)
    return pced2pmem(pced)

def amem2pmem(amem):
    p = initpced()
    a = dx7.amem2aced(amem)
    p[2] = a[15]&1
    p[3] = a[16]
    p[4] = a[17]
    p[5] = a[22]
    p[6] = min(1, a[21])
    p[7] = a[20]

    #MW
    # convert xrange  0~99 -> 0~15 
    pm = 15*a[23]//99
    am = 15*a[24]//99
    eb = 15*a[25]//99
    # find highest value
    sens = max(pm, am, eb)
    # asign for highest values
    maxdiff=10
    asgn = 0
    sens2 = 0.0
    n = 0.0
    if sens != 0:
        if pm >= sens-maxdiff:
            asgn += 1
            sens2 += pm
            n += 1
        if am >= sens-maxdiff:
            asgn += 2
            sens2 += am
            n += 1
        if eb >= sens-maxdiff:
            asgn += 4
            sens2 += eb
            n += 1
        # calculate average sens. value
        sens = round(sens2/n)
    p[9] = int(sens)
    p[10] = asgn
    
    #FC1
    pm = 15*a[26]//99
    am = 15*a[27]//99
    eb = 15*a[28]//99
    sens = max(pm, am, eb)
    asgn = 0
    sens2 = 0.0
    n = 0.0
    if sens != 0:
        if pm >= sens-maxdiff:
            asgn += 1
            sens2 += pm
            n += 1
        if am >= sens-maxdiff:
            asgn += 2
            sens2 += am
            n += 1
        if eb >= sens-maxdiff:
            asgn += 4
            sens2 += eb
            n += 1
        sens = round(sens2/n)
    p[11] = int(sens)
    p[12] = asgn
    
    #AT
    pm = 15*a[34]//99
    am = 15*a[35]//99
    eb = 15*a[36]//99
    sens = max(pm, am, eb)
    asgn = 0
    sens2 = 0.0
    n = 0.0
    if sens != 0:
        if pm >= sens-maxdiff:
            asgn += 1
            sens2 += pm
            n += 1
        if am >= sens-maxdiff:
            asgn += 2
            sens2 += am
            n += 1
        if eb >= sens-maxdiff:
            asgn += 4
            sens2 += eb
            n += 1
        sens = round(sens2/n)
    p[13] = int(sens)
    p[14] = asgn
    
    #BC
    pm = 15*a[30]//99
    am = 15*a[31]//99
    eb = 15*a[32]//99
    sens = max(pm, am, eb)
    asgn = 0
    sens2 = 0.0
    n = 0.0
    if sens != 0: 
        if pm >= sens-maxdiff:
            asgn += 1
            sens2 += pm
            n += 1
        if am >= sens-maxdiff:
            asgn += 2
            sens2 += am
            n += 1
        if eb >= sens-maxdiff:
            asgn += 4
            sens2 += eb
            n += 1
        sens = round(sens2/n)
    p[15] = int(sens)
    p[16] = asgn
    
    p[30:60] = p[:30]
    return pced2pmem(p)

def pmem2amem(pmem):
    p = pmem2pced(pmem)
    a = dx7.initaced()
    a[15] = p[2]
    a[16] = p[3]
    a[17] = p[4]
    a[22] = p[5]
    a[21] = p[6]
    a[20] = p[7]
    
    # MW
    a[23] = (p[10]&1) * (99*p[9]//15)
    a[24] = ((p[10]&2)//2) * (99*p[9]//15)
    a[25] = ((p[10]&4)//4) * (99*p[9]//15)
    
    # FC1
    a[26] = (p[12]&1) * (99*p[11]//15)
    a[27] = ((p[12]&2)//2) * (99*p[11]//15)
    a[28] = ((p[12]&4)//4) * (99*p[11]//15)
    
    # AT
    a[34] = (p[14]&1) * (99*p[13]//15)
    a[35] = ((p[14]&2)//2) * (99*p[13]//15)
    a[36] = ((p[14]&4)//4) * (99*p[13]//15)
    
    # BC
    a[30] = (p[16]&1) * (99*p[15]//15)
    a[31] = ((p[16]&2)//2) * (99*p[15]//15)
    a[32] = ((p[16]&4)//4) * (99*p[15]//15)
    
    return dx7.aced2amem(a)

def pmem2txt(pmem):
    p = pmem2pced(pmem)
    n = ['']*94
    n[2:8] = ['MONO', 'PBR', 'PBS', 'PTIM', 'GLIS', 'PORM']
    n[9:17] = ['MWS', 'MWA', 'FCS', 'FCA', 'ATS', 'ATA', 'BCS', 'BCA']
    n[26] = 'ATN'
    n[30:60] = n[:30]
    n[61] = 'VMS'
    pname=""
    for i in range(64, 94):
        n[i] = 'PNAM' + str(i-63)
        pname += chr(p[i])

    t =  "TX7 Performance: {} \n".format(pname)
    t += "-----------------------------------------------\n"
    t += "{:<13}{:4}{:4}\n".format('Parameter', 'A', 'B')
    for i in (2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 26):
        t += "{:>2}: {:<7} {:03} {:03}\n".format(i, n[i], p[i], p[i+30])
    t += "{:>2}: {:<7} {:03}\n".format(61, n[61], p[61])
    for i in range(64, 94):
        t += "{:>2}: {:<7} {:03}\n".format(i, n[i], p[i])
    k=[]
    for i in t:
        k.append(ord(i))
    return k

