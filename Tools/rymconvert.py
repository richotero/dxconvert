#!/usr/bin/env python3
import sys, os
from DXconvert import rym2612
from DXconvert import dxcommon
from DXconvert import TXC
from argparse import ArgumentParser
from glob import glob

VERSION = "20241015"

def tx2rym(infile, prefix, category, rating, type_, directory, backend, name_from_filename):
    if backend == 'fb01':
        fbb = TXC.read(infile, '0', False, 'fb01')[0]
        n=0
        for patch in range(len(fbb)//64):
            fb = fbb[64*patch:64*(patch+1)]
            rym = rym2612.fb2rym(fb)
            rym['category'] = category
            rym['rating'] = rating
            rym['type'] = type_
            if name_from_filename:
                #print("NAME FROM PATCHNAME = {}".format(rym['patchName']))
                rym['patchName'] = prefix + os.path.splitext(os.path.basename(infile))[0]
            else:
                rym['patchName'] = prefix + rym['patchName']
            rym['Output_Filtering'] = 0.0
            outfile = os.path.join(directory, "{}.rym2612".format(dxcommon.validfname(rym['patchName'])))
            n=0
            if os.path.exists(outfile):
                newfile = outfile
                while os.path.exists(newfile):
                    n += 1
                    newfile = "{}({}).rym2612".format(outfile[:-8], n)
                outfile = newfile
            xml = rym2612.rym2xml(rym)
            with open(outfile, 'w') as f:
                f.write(xml)
            print(outfile)
 
    else:
        dxx = TXC.read(infile, '0', False, backend)[0] 
        for patch in range(len(dxx)//128):
            vmm = dxx[128*patch:128*(patch+1)]
            rym = rym2612.vmm2rym(vmm)
            rym['category'] = category
            rym['rating'] = rating
            rym['type'] = type_
            if name_from_filename:
                #print("NAME FROM PATCHNAME = {}".format(rym['patchName']))
                rym['patchName'] = prefix + os.path.splitext(os.path.basename(infile))[0]
            else:
                rym['patchName'] = prefix + rym['patchName']
 
            if backend in ('fb01', 'dx100', 'dx27', 'dx21'):
                rym['Output_Filtering'] = 0.0
            else:
                rym['Output_Filtering'] = 1.0
            outfile = os.path.join(directory, "{}.rym2612".format(dxcommon.validfname(rym['patchName'])))
            n=0
            while os.path.exists(outfile):
                n += 1
                outfile = "{}({}).rym2612".format(outfile[:-8], n)
            xml = rym2612.rym2xml(rym)
            with open(outfile, 'w') as f:
                f.write(xml)
            print(outfile)

if __name__ == '__main__':
    parser = ArgumentParser(description = 'Inphonik RYM2612 file conversion utility')
    parser.add_argument('-b', '--backend', default='tx81z', help='set intermediate BACKEND (tx81z)') 
    parser.add_argument('-c', '--category', default='Synth', help='set CATEGORY (Synth)')
    parser.add_argument('-d', '--directory', default="./", help='Save files in existing DIRECTORY')
    parser.add_argument('-n', '--name_from_filename', action='store_true', default=False, help='take patchName from infile-name')
    parser.add_argument('-p', '--prefix', default='', help='output filename with PREFIX')
    parser.add_argument('-r', '--rating', type=int, default=3, help='set stars RATING 1...5 (3)')
    parser.add_argument('-t', '--type', default='User', help='set TYPE_ (User)')
    parser.add_argument('-v', '--version', action = 'version', version=VERSION)
    parser.add_argument('infile', nargs='+', help = 'Read data from INFILE')

    args = parser.parse_args()
    if args.directory:
        directory = args.directory
        if not os.path.exists(directory):
            os.makedirs(directory)
    else:
        directory = ''
    prefix = args.prefix
    rating = float(args.rating)
    category = args.category
    backend = args.backend
    type_ = args.type
    name_from_filename = args.name_from_filename
    #print(name_from_filename)
    if args.infile:
        for infiles in args.infile:
            for infile in glob(infiles):
                tx2rym(infile, prefix, category, rating, type_, directory, backend, name_from_filename)
 
    sys.exit(0)

