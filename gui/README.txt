Here goes the GUI that is used to capture data from arduino, through USB, to a PC or Mac computer.


System Requirements
===================

* Arduino, set up with the correct scripts and with the sensors attached correctly (see the folder called "arduino" in this repository for assistance in setting this up).

In Ubuntu, these requirements can be installed with the following command:
sudo apt-get install arduino

* Python. We recommend the distribution from http://www.python.org. Within your Python distribution, you will need TKinter. This is most likely already included in your Python installation. If not, go to https://wiki.python.org/moin/TkInter
In Ubuntu, this software can be installed with the following command:
sudo apt-get install python

* Furthermore, if you are running Linux then your user account will need to be in the dailout group (in order to have read access to the serial port that connects to Arduino). In order add your account to the dailout group, you can use the following command
sudo gpasswd --add {USERNAME} dialout
(where you replace {USERNAME} by your account name). You will need to log out and in again for these changes to take effect. 



Usage
=====
* Run the script capture-gui.py with Python. In Ubuntu, the easiest is to use a terminal, go to the folder where you have downloaded the gui, and type "python capture-gui.py" (without the quotes).

* Select a file to write the captured data to. To do this, click on the button "Select". Make sure you don't overwrite an existing file.

* Select the correct Arduino setting: discrete or continuous. This should correspond to the way you have programmed Arduino (i.e. the script that you have flashed on to Arduino). In the discrete case, the Arduino will send one data packet for each tap. In the continuous case, the Arduino will communicate the complete recording of the FSR at each point in time (so that you can detect the tap onsets yourself afterwards).

* Press the green "Capture" button. 

* When you are done, press "Stop". All data will be automatically written to a file as well.



