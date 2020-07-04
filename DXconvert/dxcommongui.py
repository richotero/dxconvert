from . import dxcommon
read_cfg = dxcommon.read_cfg
CFG = dxcommon.CFG
import tkinter
from tkinter.constants import *

#these are just initial values
MIDI_OUT = "MIDI"
MIDI_IN = "MIDI"

try:
    import rtmidi
    ENABLE_MIDI = True
except ImportError:
    print("NO MIDI!")
    ENABLE_MIDI = False

class Midiconf:
    def __init__(self):
        if ENABLE_MIDI:
            IN = read_cfg(CFG)[0]
            OUT = read_cfg(CFG)[1]

            midiout = rtmidi.MidiOut()
            midiin = rtmidi.MidiIn()

            self.child = tkinter.Toplevel()
            self.child.title('MIDI I/O port selection')

            label1 = tkinter.Label(self.child, text="MID_IN:")
            label1.grid(row=1, column=1, padx=4, pady=4, sticky=W)

            self.mi = tkinter.Spinbox(self.child, values=[IN]+midiin.get_ports(), wrap=True)
            self.mi.grid(row=1, column=2, columnspan=2, padx=4, pady=4)

            label2 = tkinter.Label(self.child, text="MID_OUT:")
            label2.grid(row=2, column=1, padx=4, pady=4, sticky=W)
        
            self.mo = tkinter.Spinbox(self.child, values=[OUT]+midiout.get_ports(), wrap=True)
            self.mo.grid(row=2, column=2, columnspan=2, padx=4, pady=4)
        
            button = tkinter.Button(self.child, text='OK', width=6, command=self.get_ok)
            button.grid(row=3, column=2, padx=4, pady=4)
        
            button = tkinter.Button(self.child, text='Cancel', width=6, command=self.child.destroy)
            button.grid(row=3, column=3, padx=4, pady=4)
            return
        else:
            return

    def get_ok(self):
        with open(CFG, 'w') as f:
            f.write('MID_IN = {}\n'.format(self.mi.get()))
            f.write('MID_OUT = {}\n'.format(self.mo.get()))
        self.child.destroy()
        return


