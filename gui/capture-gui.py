
#
#
#
# This is a graphical user interface that is used to conveniently capture data from arduino, 
# through USB, to a PC or Mac computer, and dump it to a text file for future analysis.
#
#
#
#





import threading

import os.path 


import Tkinter 
import tkFileDialog
from Tkinter import *
from tkFileDialog import asksaveasfilename

import tkMessageBox


from FileDialog import LoadFileDialog, SaveFileDialog

import platform
import os


import sys
import serial, time
baudrate_discrete   = 9600    # for the discrete data setting (load the corresponding Arduino script)
baudrate_continuous = 115200  # for the continuous data setting (load the corresponding Arduino script)








class Reporter:

    # This class will receive the data and display it in the text field in the GUI.

    def __init__(self):
        self.thread = None
    
    def report(self,message):
        self.text.insert(END,message)
        self.text.see(Tkinter.END)

    def settextreceiver(self,textreceiver):
        self.text = textreceiver

    def startNew(self):
        # Clear the text field
        self.text.delete(1.0, END)

    def updateButtons(self):
        # This enables/disables buttons depending on whether we are running a capture at the moment or not
        if keepGoingB.get():
            #self.previewB.configure(state=NORMAL,background="yellow")
            self.stopB.configure   (state=NORMAL,  background="red")
            self.captureB.configure(state=DISABLED,background="gray")
        else:
            self.stopB.configure   (state=DISABLED,background="gray")
            if len(fileS.get())>0:
                self.captureB.configure(state=NORMAL,  background="darkgreen")
            else:
                reporter.captureB.configure( state=DISABLED, background="gray" )







def interpret_output_discrete(r):
    # Interpret the raw (binary) output that we got from Arduino.

    #Packet
    #|---------+---+---------+----------+-------------+---|
    #| Byte    | 1 | 2,3     | 4,5      | 6,7         | 8 |
    #| Content | B | [onset] | [offset] | [max force] | E |
    #|---------+---+---------+----------+-------------+---|
    
    #Where [t] = N for oNset, F for oFfset
    #and [time] is the timestamp (in msec)


    # Here we interpret the packet that we received from Arduino.
    # Note that the first element of the packet (B in our case) has been omitted here.
    tap_onset  = ord(r[0])+256*ord(r[1])
    tap_offset = ord(r[2])+256*ord(r[3])
    maxforce   = ord(r[4])+256*ord(r[5])
    
    # Make a formatted output
    output = "%i %i %i"%(tap_onset,tap_offset,maxforce)

    return output



def interpret_output_continuous(r):
    # Interpret the raw (binary) output that we got from Arduino.

    # Packet
    #|---------+---+-------------+---------------+---|
    #| Byte    | 1 | 2,3         | 4,5           | 6 |
    #| Content | B | [timestamp] | [fsr-reading] | E |
    #|---------+---+-------------+---------------+---|
    #Here [timestamp] is the timestamp (in msec)
    #and [fsr-reading] is the FSR voltage (in arduino's arbitrary units).


    # Here we interpret the packet that we received from Arduino.
    # Note that the first element of the packet (B in our case) has been omitted here.
    timestamp   = ord(r[0])+256*ord(r[1])
    fsr_reading = ord(r[2])+256*ord(r[3])
    
    # Make a formatted output
    output = "%i %i"%(timestamp,fsr_reading)

    return output












def askSaveFile():
    # Asks where to save the file

    global fileS
    global reporter

    filename = asksaveasfilename(parent=root,
                                 defaultextension=".txt",
                                 initialfile=fileS.get(),
                                 filetypes=[("text files","*.txt"),
                                            ("all files","*")])

    if filename:
        fileS.set(filename)
        reporter.updateButtons()
        


def stopCapture():
    global keepGoingB
    global reporter

    keepGoingB.set(False)
    reporter.report("Capture stopped.\n\n")
    reporter.thread=None
    reporter.updateButtons()




def runCapture():

    # This is called from the doCapture function

    print ("Starting capture")
        
    # Start up the serial communication
    commport = usbS.get()
    packet_type = packetI.get()
    if (packet_type==1):
        baudrate = baudrate_discrete
    else:
        baudrate = baudrate_continuous

    try:
        comm = serial.Serial(commport, baudrate, timeout=0.25)
    except:
        reporter.report("Cannot open USB port %s. Is the device connected?\n"%commport)
        stopCapture()
        return -1


    filename = fileS.get() # get the filename we are supposed to output to

    if len(filename)==0:
        reporter.report("Please select an output file.\n")
        stopCapture()
        return -1

       
    if os.path.isfile(filename):
        reporter.report("Output file previously existed! If we continue, we will overwrite all data in it.\n")
        if not tkMessageBox.askyesno('Confirm overwriting data file', 'The data file you have selected for output already exists.\nIf we proceed, all data currently in the file will be erased.\n\nAre you sure that you want to continue?'):
            reporter.report("Capture aborted because the user does not want to overwrite the data file.\n")
            stopCapture()
            return -1
        

    dumpfile = open(filename,'w')

    do_continue=True
    keepGoingB.set(do_continue)
    reporter.report("Starting capture (%s)\n"%filename)
    reporter.updateButtons()


    reporter.report("")
    reporter.report(output_header+"\n")
    dumpfile.write(output_header+"\n")

    i=0
    while do_continue:

        # Ok, let's read one byte
        r = comm.read(1)

        if r=="B": # This could be the beginning of a packet from arduino

            avail=0 # how many bytes are available
            while avail<PACKET_LENGTH-1: # read to fill up the packet
                avail=comm.inWaiting()

            # all right, now we can read
            r = comm.read(PACKET_LENGTH-1) # read the whole packet straight away

            # Now continue to work with this
            if len(r)==(PACKET_LENGTH-1) and r[-1]=="E": # if we have the correct ending also

                output = interpret_output(r)
                dumpfile.write(output+"\n")
                dumpfile.flush()

                # Occasionally give a bleep so the user knows
                # we're still working
                i+=1
                if i>=report_dump_interval:
                    reporter.report(output+"\n")
                    i=0

            else:
                if len(r)>0:
                    reporter.report("rejected")

        do_continue = keepGoingB.get()


    # Update which button is enabled etc.
    reporter.updateButtons()






def doCapture():

    # This is when the "capture" button is pressed
    # First, we set everything up and then we set the actual capture in motion

    global reporter

    if reporter.thread!=None:
        reporter.report("Already running!\n")
        return -1


    # The expected packet length

    global PACKET_LENGTH
    global interpret_output
    global output_header
    global report_dump_interval
    packet_type = packetI.get()
    if packet_type==1:
        # discrete: one packet per tap
        PACKET_LENGTH = 8
        interpret_output = interpret_output_discrete
        output_header = "onset offset maxforce"
        report_dump_interval = 1


    if packet_type==2:
        # continuous: simply forwarding the trace of the FSR sensor
        PACKET_LENGTH = 6
        interpret_output = interpret_output_continuous
        output_header = "timestamp force_reading"
        report_dump_interval = 1000



    reporter.startNew()
    reporter.thread = threading.Thread(target=runCapture)
    reporter.thread.start()



    





def build_gui():


    # Making a bunch of variables that I will access from anywhere in this GUI
    global usbS       # the current setting for the serial port
    global fileS      # the current setting for the file name
    global packetI    # the type of data that we will receive from arduino
    global keepGoingB # keep track of whether we're still capturing
    global root

    root =Tk()
    root.title('Tap-Arduino Capture GUI (Ben Schultz & Floris van Vugt)')

    usbS       = StringVar()
    fileS      = StringVar()
    packetI    = IntVar()
    keepGoingB = BooleanVar()

    packetI.set(1)
    if platform.system()=="Windows":
        usbS.set("COM<NUMBER>")
    elif os.name=="posix":
        usbS.set("/dev/ttyACM0")
    else:
        usbS.set("<ENTER SERIAL PORT HERE>")
    fileS.set("")
    keepGoingB.set(False)


    global reporter
    reporter = Reporter()


    usbF = Frame(root)
    Label (usbF,text='serial port').pack(side=LEFT,padx=10,pady=10)
    usbEntry = Entry (usbF,width=30,textvariable=usbS)
    #usbEntry = Frame (usbF,background="red")
    usbEntry.pack(expand=True,side=LEFT,padx=10,pady=10,fill=BOTH)
    #Label (usbEntry,text="this will expand?").pack(side=LEFT,padx=10,pady=10,fill=BOTH)
    #usbEntry.pack(side=LEFT,padx=10,pady=10,fill=BOTH)
    usbF.pack(side=TOP,padx=10,fill=X)



    fileF = Frame(root)
    Label (fileF,text='save to file').pack(side=LEFT,padx=10)
    fileEntry = Entry (fileF,width=30,textvariable=fileS)
    fileEntry.pack(side=LEFT,expand=True,padx=10,pady=10,fill=X)
    fileB = Button(fileF,text="select",command=askSaveFile)
    fileB.pack(side=RIGHT,padx=10,pady=10)
    fileF.pack(padx=10,pady=0,fill=X)




    packetF = Frame(root)
    Label (packetF,text='data type').pack(side=LEFT,padx=10)
    discR = Radiobutton(packetF, text="discrete",   variable=packetI, value=1)
    contR = Radiobutton(packetF, text="continuous", variable=packetI, value=2)
    discR.pack(side=LEFT,padx=10,pady=10)
    contR.pack(side=LEFT,padx=10,pady=10)
    packetF.pack(padx=10,pady=0,fill=X)




    reportF = Frame(root)
    s       = Scrollbar(reportF)
    reportT = Text(reportF,height=8,width=8)
    reporter.settextreceiver(reportT)
    reportT.pack(side=LEFT, padx=5, pady=5,fill=BOTH,expand=True)
    s.pack(side=RIGHT,fill=Y)
    s.config(command=reportT.yview)
    reportT.config(yscrollcommand=s.set)               
    reportF.pack(side=TOP,fill=BOTH,expand=True)

    #for i in range(80): 
    #   reportT.insert(END, "This is line %d\n" % i)


    buttonF = Frame(root)
    captureB = Button(buttonF, text='capture', command=doCapture, background="darkgreen" )
    captureB.configure(state=DISABLED,background="darkgray")
    captureB.pack(side=LEFT,padx=10,pady=10)
    stopB = Button(buttonF, text='stop', command=stopCapture, background="red" )
    stopB.pack(side=LEFT,padx=10,pady=10)
    buttonF.pack(side=BOTTOM,padx=10,pady=10)
    stopB.configure(state=DISABLED,background="darkgray")


    reporter.stopB    = stopB
    reporter.captureB = captureB
    reporter.updateButtons()

    root.geometry("600x700")

    root.mainloop()







build_gui()


