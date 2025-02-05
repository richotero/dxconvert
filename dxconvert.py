#!/usr/bin/env python3

"""
dxconvert.py

(c)2020 Martin Tarenskeen <m.tarenskeenATkpnmailDOTnl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

__license__ = 'GPL v3'

import sys
import os
from argparse import ArgumentParser
from glob import glob
from DXconvert import DXC
from DXconvert import dxcommon

PROGRAMNAME = DXC.PROGRAMNAME
PROGRAMVERSION = dxcommon.PROGRAMVERSION
PROGRAMDATE = dxcommon.PROGRAMDATE

############# CLI ###################

def cli_main(argv=sys.argv):
    progname=os.path.basename(argv[0])

    parser=ArgumentParser(
            description='{}\nVersion: {} ({})'.format(PROGRAMNAME, PROGRAMVERSION, PROGRAMDATE))
    parser.add_argument('-bc2at', '--bc2at', action='store_true', default=False, help='Copy BreathControl data to AfterTouch')
    parser.add_argument('-bc', '--nobreathcontrol', action="store_false", default=True, help='Do NOT use BreathControl data')
    parser.add_argument('-b', '--brightness', default=0, type=int, help='Adjust global brightness (+/-)')
    parser.add_argument('-c', '--channel', default=0, type=int, help='Midi channel (1~16) in SysEx header')
    parser.add_argument('-C', '--check', action='store_true', default=False, help='Check SysEx checksum before import') 
    parser.add_argument('-d', '--dx72', action='store_true', default=False, help='Save with AMEM/ACED (DX7II) data')
    parser.add_argument('-f', '--find', metavar='STRING', help='Search for STRING in patchnames')
    parser.add_argument('-fc1', '--fc1', action='store_false', default=True, help='Do NOT use FC1 foot controller data')
    parser.add_argument('-fc2', '--fc2', action='store_false', default=True, help='Do NOT use FC2 foot controller data')
    parser.add_argument('-n', '--nosplit', action='store_true', default=False, help="Don't split: save data in one file")
    parser.add_argument('-nd', '--nodupes', action='store_true', default=False, help='Remove duplicates')
    parser.add_argument('-nd2', '--nodupes2', action='store_true', default=False, help='Remove duplicates, also with different names')
    parser.add_argument('-ns', '--nosilence', action='store_true', default=False, help='Remove patches that produce no sound')
    parser.add_argument('-no4', '--no4op', action='store_true', default=False, help="Remove patches that use only 4 operators (or less)")
    parser.add_argument('-o', '--offset', default='0', help="Ignore first/last (+/-) OFFSET bytes in input file(s)")
    parser.add_argument('-r', '--random', action='store_true', default=False, help="Renata's Randomizer") 
    parser.add_argument('-sp', '--split', action='store_true', help="save each single patch as a separate file")
    parser.add_argument('-s', '--select', metavar='RANGE', help='Select RANGE to save')
    parser.add_argument('-S', '--sort', action='store_true', default=False, help='Sort patches by name, not case-sensitive')
    parser.add_argument('-S2', '--sort2', action='store_true', default=False, help='Sort patches by name, case-sensitive')
    parser.add_argument('--copy', nargs=2, metavar=('X', 'Y'), help='Copy patch nr X to nr Y')
    parser.add_argument('--swap', nargs=2, metavar=('X', 'Y'), help='Swap patch nr X and nr Y')
    parser.add_argument('--view', action='store_true', default=False, help='Print patchnames to stdout')
    parser.add_argument('-t', '--tx7', action='store_true', default=False, help='Save with TX7 Performance data')
    parser.add_argument('-v', '--version', action='version', version='{} ({})'.format(PROGRAMVERSION, PROGRAMDATE))
    parser.add_argument('-x', '--exclude', metavar='STRING', help='Exclude if STRING is found in patchname')
    parser.add_argument('infile', nargs='+', help='Selects input file(s)')
    parser.add_argument('outfile', help='Select output file')

    args=parser.parse_args()
    infilez = args.infile
    infiles = []
    for i in infilez:
        infiles += glob(i)

    outfile = args.outfile
    outfile_ext = os.path.splitext(outfile)[1]
    outfile_dir = os.path.split(outfile)[0]

    brightness = args.brightness
    dx72 = args.dx72
    TX7 = args.tx7
    nosplit = args.nosplit
    ch = args.channel
    check = args.check
    select = args.select
    sort = args.sort
    sort2 = args.sort2
    split = args.split
    swap = args.swap
    copy = args.copy
    nodupes = args.nodupes
    nodupes2 = args.nodupes2
    nosilence = args.nosilence
    no4op = args.no4op
    offset = args.offset
    bc2at = args.bc2at
    bc = args.nobreathcontrol
    fc1 = args.fc1
    fc2 = args.fc2
    Random = args.random
    find = args.find
    exclude = args.exclude
    view = args.view

    dx7data, tx7data, dx72data = [], [], []
    for infile in infiles:
        print ("Reading {}".format(infile))
        if not os.path.exists(infile):
            print ("{} not found".format(infile))
            return 1
        if infile == outfile:
            print ("Must have different input and output files")
            return 1

        if os.path.isfile(infile):
            dx7dat, dx72dat, tx7dat, channel = DXC.read(infile, offset, check)
            dx7data += dx7dat
            dx72data += dx72dat
            tx7data += tx7dat

    if ch != None:
        channel = ch-1
        channel = max(0, channel)
        channel = min(15, channel)

    if select != None:
        dx7dat, dx72dat, tx7dat = [], [], []
        for i in dxcommon.range2list(select):
            dx7dat += dx7data[128*(i-1): 128*i]
            dx72dat += dx72data[35*(i-1): 35*i]
            tx7dat += tx7data[64*(i-1): 64*i]
        dx7data, dx72data, tx7data = dx7dat, dx72dat, tx7dat
    
    if args.find != None:
        dx7data, dx72data, tx7data = DXC.dxfind(dx7data, dx72data, tx7data, find)

    if args.exclude:
        dx7data, dx72data, tx7data = DXC.dxexclude(dx7data, dx72data, tx7data, exclude)
    
    if brightness:
        dx7data = DXC.dxbrightness(dx7data, brightness)

    if Random:
        dx7data = dxcommon.dxrandom(dx7data)

    if nodupes2:
        nodupes = True
            
    if nodupes or nodupes2:
        dx7data, dx72data, tx7data = DXC.dxnodupes(dx7data, dx72data, tx7data, dx72, TX7, nodupes2)

    if nosilence:
        dx7data, dx72data, tx7data = DXC.dxnosilence(dx7data, dx72data, tx7data)

    if no4op:
        dx7data, dx72data, tx7data = DXC.dxno4op(dx7data, dx72data, tx7data)

    if sort:
        dx7data, dx72data, tx7data = DXC.dxsort(dx7data, dx72data, tx7data, dx72, TX7, False)
    if sort2:
        dx7data, dx72data, tx7data = DXC.dxsort(dx7data, dx72data, tx7data, dx72, TX7, True)
    
    if copy:
        dx7data, dx72data, tx7data = DXC.dxcopy(dxcommon.range2list(copy[0]), int(copy[1]), dx7data, dx72data, tx7data)
    
    if swap:
        dx7data, dx72data, tx7data = DXC.dxswap(int(swap[0]), int(swap[1]), dx7data, dx72data, tx7data)

    if view:
        DXC.dxview(dx7data)

    for i in range(len(dx7data)//128):
        if bc2at:
            dx72data[20+35*i:24+35*i] = dx72data[16+35*i:20+35*i]
        if fc1 == False:
            dx72data[12+35*i:16+35*i] = [0, 0, 0, 0]
        if fc2 == False:
            dx72data[26+35*i:30+35*i] = [0, 0, 0, 0]
        if bc == False:
            dx72data[16+35*i:20+35*i] = [0, 0, 0, 50]

    if split and (len(dx7data)//128 > 1):
        for i in range(len(dx7data)//128):
            outfile_name = dxcommon.list2string(dx7data[128*i+118:128*i+128])
            outfile_name = dxcommon.validfname(outfile_name)
            Outfile = os.path.join(outfile_dir, outfile_name + outfile_ext)
            
            count = 0
            while os.path.exists(Outfile):
                count += 1
                if count>1:
                    Outfile = os.path.join(outfile_dir, outfile_name + "(" + str(count) + ")" + outfile_ext)

            print (DXC.write(Outfile, dx7data[128*i:128*(i+1)], dx72data[35*i:35*(i+1)], tx7data[64*i:64*(i+1)], dx72, TX7, channel, nosplit))

    else:
        print(DXC.write(outfile, dx7data, dx72data, tx7data, dx72, TX7, channel, nosplit))

    return 0


################### MAIN #####################

if __name__ == '__main__':
    sys.exit(cli_main())


