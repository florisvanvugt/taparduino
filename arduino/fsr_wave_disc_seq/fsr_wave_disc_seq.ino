// -*- Mode:c -*-
// The above incantation tells emacs to do C style syntax highlighting

/* Use FSR to create a sound on the Wave Shield

Add the Wave Shield (we used version 1.1) to the Arduino 
(we used the Arduino Uno)

Connect the Wave Shield digital pins as described here (the second-to-last panel):
http://www.ladyada.net/make/waveshield/solder.html

Connect one end of FSR to 5V, the other end to Analog 0.
Then connect one end of a 10K resistor from Analog 0 to ground

For more information see http://www.ladyada.net/learn/sensors/fsr.html
and http://www.ladyada.net/make/waveshield/examples.html

The volume control requires changing the "WaveHC.h" library. Line 24 should read: #define DVOLUME 1
*/

//////////////////////////////////// load libraries
#include <avr/pgmspace.h>
#include <WaveHC.h>
#include <WaveUtil.h>

////////////////////////////////////  set variables 
int fsrAnalogPin = 0; // FSR is connected to analog 0
int fsrReading;      // the analog reading from the FSR resistor divider
const int threshold = 20; // the FSR threshold necessary to make a sound (ON)
const int low_thresh = 10; // where the FSR reading must go to to be OFF
int time_thresh = 40; // set a time threshold for how long to wait until another sound can be made
int offset_thresh = 40; // set a time threshold for how long to wait after depression (prevent double taps)
unsigned long time_tol = 0; // preset the exact time from which it is ok to make another sound
unsigned long timeStamp=0; // timestamp for Arduino
unsigned long prevt=-1; // the previous time value to ensure sample rate of 1000Hz
int cur_on = 0; // say if the FSR is "on" or "off"

// variables for discrete data
unsigned long cur_onset = 0; // preset current onset time
unsigned long cur_offset = 0; // preset current offset time
int max_force = 0; // preset maximum fsr reading

// variables for sequences
int cur_pos = 0;

char* timbreList[] = {"SI","SA","TR","SQ"}; // SI = Sine, SA = Saw, TR = Triangle, SQ = Square
char* durList[] = {"D1","D2","D3","D4","D8"}; // 1-8, multipliers of 25ms
char* toneList[] = {"53","55","57","58","60"}; // MIDI notes

const int all_tones[15] = {2,2,3,4,4,3,2,1,0,0,1,2,2,1,1}; // Order of tones (see toneList)
const int all_durs[15] = {1,1,1,2,2,3,3,3,3,3,3,3,4,0,4}; // Order of Durations (see durList)
const int all_timbres[15] = {0,0,0,0,1,1,1,1,2,2,2,2,3,3,3}; // Timbres (0-3), (see timbreList)
const int all_delays[15] = {0,0,0,0,50,50,100,100,0,0,0,0,0,0,0}; // auditory feedback delays
const int all_intense[15] = {5,5,7,9,11,10,8,7,6,5,4,3,2,1,5}; // volume levels between 0 and 12

int tone_num = all_tones[cur_pos];
int timb_num = all_timbres[cur_pos];
int dur_num = all_durs[cur_pos];

char* cur_timbre = timbreList[timb_num];
char* cur_tone = toneList[tone_num];
char* cur_dur = durList[dur_num];
int cur_del = all_delays[cur_pos];
int cur_intense = all_intense[cur_pos];

int num_sounds = sizeof(all_tones)/sizeof(all_tones[0])-1;
int i;

char* wavFile = "XXXXXX.wav";
char* curFile = changeString(wavFile,cur_timbre,cur_tone,cur_dur);

//////////////////////////////////// set objects for Wave Shield
SdReader card;    // This object holds the information for the card
FatVolume vol;    // This holds the information for the partition on the card
FatReader root;   // This holds the information for the volumes root directory
FatReader file;   // This object represent the WAV file 
WaveHC wave;      // This is the only wave (audio) object, since we1 will o1nly pla1y one at a time

//////////////////////////////////// Define macro to put error messages in flash memory (for Wave Shield)
#define error(msg) error_P(PSTR(msg))

//////////////////////////////////// SETUP
void setup() {
  Serial.begin(9600); // slow speed debugging
  //Serial.begin(115200); // high speed debugging
  //Serial.begin(1555200); // good speed for processing (must match python code for reading!)
  
  Serial.println(curFile);
  ////// setup for waveshield
  if (!card.init()) error("card.init");

  // enable optimized read - some cards may timeout
  card.partialBlockRead(true);

  if (!vol.init(card)) error("vol.init");

  if (!root.openRoot(vol)) error("openRoot");
  
  // Set the output pins for the DAC control. This pins are defined in the library
  // This is for the Wave shield output
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  
// look in the root directory and open the file
  if (!file.open(root, curFile)) {
    putstring("Couldn't open file "); Serial.print(curFile); return;
  }
  // OK read the file and turn it into a wave object
  if (!wave.create(file)) {
    putstring_nl("Not a valid WAV"); return;
  }
  
  // preload the sound from the outside for speed
  file.open(root, curFile);
  wave.create(file);
  wave.volume = cur_intense;
}

//////////////////////////////////// LOOP
void loop(void) {
  getInfos(); // read info 
  
  if (fsrReading > threshold){
    cur_onset = timeStamp; // get onset time
    time_tol = timeStamp+time_thresh; // set time threshold
    cur_on=1; // say FSR is "on"
    time_tol = timeStamp+cur_del;
    
    while (timeStamp < time_tol) { // wait for delay time
      getInfos(); // read info    
    }

    // play the wav file
    playcomplete(curFile);        
    getInfos(); // read info
    
    // now let's stop it from playing again until after the time threshold and the FSR reading returns to zero    
    while ((timeStamp < time_tol) || (fsrReading > low_thresh)) {
      getInfos(); // read info
    }
          
    time_tol = timeStamp+offset_thresh; // set time until next tap can occur
    
    // now let's stop it from playing again until after the time threshold and the FSR reading returns to zero    
    while ((timeStamp < time_tol) || (fsrReading > low_thresh)) {      
      getInfos(); // read info      
    }
    
    // preset next delay
    cur_del = all_delays[cur_pos];
    
  }
  
  max_force = fsrReading; // reset max force
     
}

//////////////////////////////////// WAVE SHIELD FUNCTIONS

// Plays a full file from beginning to end with no pause.
void playcomplete(char *name) {
  getInfos();
  //collectData();
  // call our helper to find and play this name
  playfile(name);
  while (wave.isplaying) {
  // collect data while it is playing (because otherwise it blocks the readings)
  getInfos();
  }
  getInfos();
  
  if (cur_pos == num_sounds) {
    cur_pos = 0; 
  }
  else {
    cur_pos = ++cur_pos;  
  }
  
  // preset new sound variables   
  tone_num = all_tones[cur_pos];
  timb_num = all_timbres[cur_pos];   
  dur_num = all_durs[cur_pos];
  
  cur_timbre = timbreList[timb_num];
  cur_tone = toneList[tone_num];
  cur_dur = durList[dur_num];
  curFile = changeString(wavFile,cur_timbre,cur_tone,cur_dur); /* sets the whole array */
  cur_intense = all_intense[cur_pos];
  wave.volume = cur_intense;
    
  // open and create wavefile for next read
  file.open(root, name);
  wave.create(file);
  
}

void playfile(char *name) {
  // see if the wave object is currently doing something
  if (wave.isplaying) {// already playing something, so stop it!
    wave.stop(); // stop it
  }  
  getInfos();
  // start playback
  wave.play();
}

/////////////////////////////////// WAVE SHIELD HELPERS
/*
 * print error message and halt
 */
void error_P(const char *str) {
  PgmPrint("Error: ");
  SerialPrint_P(str);
  sdErrorCheck();
  while(1);
}
/*
 * print error message and halt if SD I/O error, great for debugging!
 */
void sdErrorCheck(void) {
  if (!card.errorCode()) return;
  PgmPrint("\r\nSD I/O error: ");
  Serial.print(card.errorCode(), HEX);
  PgmPrint(", ");
  Serial.println(card.errorData(), HEX);
  while(1);
}

//////////////////////////////////// FUNCTIONS
// Send data to serial port
void collectData() { 
      
  if (prevt==-1 | timeStamp!=prevt) { 
    // only send if the time has changed, that is, 
    // force the data transfer to maximum of 1000Hz.
    // Using higher sample rates can result in buffer
    // overflows and missed packets

    // Send data to the serial port (for degugging in Arduino serial manager)
    //Serial.print("Onset time = ");
    //Serial.print(cur_onset);
    //Serial.print(" Offset time = ");
    //Serial.print(cur_offset);
    //Serial.print(" Maximum force = ");
    //Serial.print(max_force);    
    //Serial.print("\n");
    
    // Send data to the serial port
    Serial.print("B"); // signal packet start (hardcoded)
    sendBinary(cur_onset); // send onset time
    sendBinary(cur_offset); // send offset time
    sendBinary(max_force); // send max FSR reading
    Serial.print("E"); // signal packet end (hardcoded)
    prevt=timeStamp; // send previous time marker
  }    
}

// get FSR and timing info, and turn off the sound at end of tone duration
void getInfos() {
  fsrReading = analogRead(fsrAnalogPin); // read FSR
  timeStamp = millis(); // get time (in milliseconds)      
  if (fsrReading > max_force) max_force = fsrReading;
  
  if ((cur_on==1) && (fsrReading < low_thresh)) {
    cur_offset = timeStamp; // get offset time    
    collectData(); // send data 
    cur_on=0; // turn off
  }
}

// Send data in binary to increase speed and reduce buffer overflow
void sendBinary(int value) 
// Send a binary value directly (without conversion to string)
// based on http://my.safaribooksonline.com/book/hobbies/9781449399368/serial-communications/sending_binary_data_from_arduino#X2ludGVybmFsX0ZsYXNoUmVhZGVyP3htbGlkPTk3ODE0NDkzOTkzNjgvMTAy
{
  Serial.write(lowByte(value));
  Serial.write(highByte(value));
}

// Function to update the change in song name
char* changeString(char* oldChar,char *newTimb,char *newTone, char *newDur)
{
  for ( i = 0; i < strlen(newTimb); i++) {
   oldChar[i]=newTimb[i];
   Serial.println(i);
  } 
  
  for ( i = 2; i < strlen(newTone)+2; i++) {
   oldChar[i]=newTone[i-2];
   Serial.println(i);
  } 
  
  for ( i = 4; i < strlen(newDur)+4; i++) {
   oldChar[i]=newDur[i-4];
   Serial.println(i);
  } 
  return oldChar;  
  Serial.println(oldChar);
}

