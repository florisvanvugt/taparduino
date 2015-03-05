// -*- Mode:c -*-
// The above incantation tells emacs to do C style syntax highlighting

/* Use FSR to record tapping responses with the Arduino

Connect one end of FSR to 5V, the other end to Analog 0.
Then connect one end of a 10K resistor from Analog 0 to ground

For more information see http://www.ladyada.net/learn/sensors/fsr.html

*/

////////////////////////////////////  set variables 
int fsrAnalogPin = 0; // FSR is connected to analog 0
int fsrReading;      // the analog reading from the FSR resistor divider
int threshold = 20; // the FSR threshold necessary to make a sound (ON)
int low_thresh = 10; // where the FSR reading must go to to be OFF
int time_thresh = 40; // set a time threshold for how long to wait until another sound can be made
int offset_thresh = 40; // set a time threshold for how long to wait after depression (prevent double taps)
char* beginRead = "B"; // gives a start read barrier for the FSR reading
char* endRead = "E"; // gives an end read barrier for the FSR reading
unsigned long time_tol = 0; // preset the exact time from which it is ok to make another sound
unsigned long timeStamp=0; // timestamp for Arduino
unsigned long prevt=-1; // the previous time value to ensure sample rate of 1000Hz
int cur_on = 0; // say if the FSR is "on" or "off"

// variables for discrete data
unsigned long cur_onset = 0; // preset current onset time
unsigned long cur_offset = 0; // preset current offset time
int max_force = 0; // preset maximum fsr reading

//////////////////////////////////// load libraries
#include <avr/pgmspace.h>

//////////////////////////////////// SETUP
void setup() {
  Serial.begin(9600); // slow speed debugging
  //Serial.begin(115200); // high speed debugging
  //Serial.begin(1555200); // good speed for processing (must match python code for reading!)
  
}

//////////////////////////////////// LOOP
void loop(void) {
  getInfos(); // read info 
  
  if (fsrReading > threshold){
    
    cur_onset = timeStamp; // get onset time
    cur_on = 1; // FSR is now on
    time_tol = timeStamp+time_thresh; // set time threshold
    
    // now let's stop it from playing again until after the time threshold and the FSR reading returns to zero    
    while (fsrReading > low_thresh) {
      getInfos(); // read info
    }
          
    time_tol = timeStamp+offset_thresh; // set time until next tap can occur
    
    // now let's stop it from playing again until after the time threshold and the FSR reading returns to zero    
    while ((timeStamp < time_tol) || (fsrReading > low_thresh)) {      
      getInfos(); // read info      
   }
   
  }
  
  max_force = fsrReading; // reset max force
     
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