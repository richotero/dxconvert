The tools in the Tools directory
================================

General usage:

All the commandline tools in this directory use a similar commandline 
syntax:

Short options start with "-"

Long options start with "--"

All other options are used as INPUT files.

Wildcards are allowed for infiles.

Unless "-o OUTFILE" or "--outfile=OUTFILE" is used, outfile names are 
derived from infile names. Existing filenames are first copied to numbered 
backup files, and then overwritten. (dx7iisyx2fd.py works a little different)
 
TIP: When using multiple input files, I recommend NOT to use the -o option.

Use the -h option for specific help.


syx2mid.py: 

A tool to convert SysEx files (usually, but not always, with .syx 
extension) to Standard MIDI files with the same content.

mid2syx.py: 

A tool to extract SyxEx information from MIDI files.

qr2syx.py: 

A tool to convert QR code images for the Yamaha Reface synths to SysEx 
files. This tool depends on Zbar for QR decoding. A binary called zbarimg 
(or zbarimg.exe on Windows) should be in your system PATH. You can find 
Zbar at http://zbar.sourceforge.net/

syx2qr.py: 

A tool to convert Yamaha Reface SysEx files to QR code images. This tool 
requires a python module named qrcode. https://pypi.python.org/pypi/qrcode 
You can use "pip install qrcode" for easy installation.

dx7iifd2syx.py: 

A tool to convert *.Ixx (xx is a number) from DX7IIFD floppy disks to 
normal SysEx files. Only the VOICE and PERFORMANCE data are converted. 
Other information, like microtuning tables, is ignored.

dx7iisyx2fd.py:
A tool to search data (VMEM, AMEM, PMEM, SYSTEM, MCT) from one or more DX7(II) sysex files 
and convert these into one DX7IIFD floppy disk file (*.Ixx) 

v50convert.py:

A tool to convert between V50 floppy disk files (*.Ixx, etc.) and SysEx files.

-- 

MT


