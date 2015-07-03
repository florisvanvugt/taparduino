# This script was written by Benjamin Schultz with the help of Floris van Vugt
# For any inquiries, please  email Ben at benjamin.glenn.schultz@gmail.com
# The script has not been commented very well, but hopefully it makes sense
#
# Arduino is sending in blocks of 6 bytes:
#      byte1    byte2&3   byte4&5    byte6 
#       "B"       int      int       "E"
#     'begin'    t(ms)   Pressure    'end'
#


# import modules (aka libraries)
import sys
import serial, time
import os
import datetime
import wave # to read wave files
import pyaudio # in Mac OS, use the universal installer from http://people.csail.mit.edu/hubert/pyaudio/

baudrate = 115200 # this is the baudrate set on the Arduino for the continuous scripts

try:
    sound_file = sys.argv[1]
except:
    sound_file = "Dont_stop_me_now.wav"
    print("Using default sound\n")

try:
    condID = sys.argv[2]
except:
    condID = "TEST.txt"
    print("This will be a test\n")

try:
    comm_port = sys.argv[3]
except:
    comm_port = "COM4"
    print("Comm port %s will be used"%comm_port)

PACKET_LENGTH = 5

# Setup the sound
# Initialise pyaudio
pAudio = pyaudio.PyAudio()
#pyaudio.paASIO = 3 #comment this out if errors (some issues with ASIO drivers)
wavefile = wave.open(sound_file, 'rb')
i=0

# LET'S MAKE SOME FUNCTIONS
# define callback (2)
def callback(in_data, frame_count, time_info, status):
    wavFile = wavefile.readframes(frame_count)
    return (wavFile, pyaudio.paContinue)

def report_package(r,dumpfile,sound_on,time_now):
    """ Given a packet that we just read from the serial port,
	extract the package contents and write them to the output file.
	"""
    
    b1 = ord(r[0])+256*ord(r[1])
    b2 = ord(r[2])+256*ord(r[3])    
    b3 = r[4]

    #print b1,b2
    output = "%i %i %f %f\n"%(b1,b2,time_now,sound_on) #original
    print(output)
	
    dumpfile.write(output)

    # uncomment this to see print of output
    if True:
        print output,

    
def process_packages(comm_port,sound_on,dumpfile):
    """ Process the packages that might have been sent to the comm_port,
	and report them if they have."""

    # Read the incoming packet
    r = comm_port.read(1)

    if True:
        if r=="B": # This should be the beginning of a signal
            time_now = time.clock() #get time immediately for stamping
            avail=0 # how many bytes are available
            while avail<PACKET_LENGTH: # we need at least as many bytes as there are in the packet
                avail=comm_port.inWaiting()

            # Received the expected number of packets. Now we can read
            r = comm_port.read(PACKET_LENGTH) # read the whole thing straight away

            # Now continue to work with this
            if len(r)==PACKET_LENGTH and r[-1]=="E": # if we have the correct ending also
			    #get CPU clock and sound time
                report_package(r,dumpfile,sound_on,time_now)
            else:
                if len(r)>0:
                    print "rejected",r # let's us know if something is wrong (e.g., full buffer)

        else:
            if r=="\n":
                pass
            else:
                print "rejected non-B",r

# read in sound
#wavFile = wavefile.readframes(wavefile.getnframes())#just read the whole thing
waveformat = pAudio.get_format_from_width(wavefile.getsampwidth())
wavechannels = wavefile.getnchannels()
waveframerate = wavefile.getframerate()

# set timing options
timeDelay = 2 # two seconds before song to ensure Arduino has started
endDelay = 1 # one second after song
endTime=float('inf')

if True:        
    
    try:
        comm = serial.Serial(comm_port, baudrate, timeout=0.25)
    except:
        print "Cannot open USB port %s. Is the device connected?\n"%comm_port
        sys.exit(-1)

    filename = condID
        
    dumpfile = open(filename,'w')

    do_continue=True
    sound_started=False
    sound_ended=False
    sound_on = 0

    timeStart = time.clock()
    waitTime = timeStart+timeDelay

    while do_continue:
        
        if sound_started==False and time.clock() > waitTime:
            audioOutStream = pAudio.open(format=waveformat,channels=wavechannels,rate=waveframerate,output=True,stream_callback=callback)
            soundTime = time.clock()
            sound_started=True

        if sound_started==True and sound_ended==False:
            sound_on=audioOutStream.get_time()
            
        # Ok, let's read something
        process_packages(comm,sound_on,dumpfile)
        
        if sound_started==True:
            if audioOutStream.is_active()==False and sound_ended==False:
                timeEnd = time.clock()
                sound_on=audioOutStream.get_output_latency()#just a hack to get this value
                sound_ended = True
                endTime = timeEnd+endDelay
                
        if time.clock()>endTime:
            audioOutStream.stop_stream()
            audioOutStream.close()
            wavefile.close()
            pAudio.terminate()
            sys.exit(0)