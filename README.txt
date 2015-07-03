Tap-Arduino
===========

This is a library of functions for using the Arduino in tapping experiments.

We supply code that you can flash onto the Arduino board. This code presupposes that you have built Arduino exactly according to the diagrams that we provide. We similarly provide a graphical user interface (GUI) that communicates with the Arduino through USB and allows you to capture and store the data on your computer harddrive. This GUI requires python (see its README).

Folders of this repository:
* **arduino** contains the scripts that you can flash onto the Arduino
* **gui** contains the python-based graphical user interface to conveniently capture data from the Arduino.
* **stimuli** contains a series of wave files used in the Arduino scripts that illustrate different types of feedback manipulation.
* **sounds** contains a sample wave file that can be used as a feedback in the wave shield version of our scripts.
* **synchronisation** contains a python script that can be used to record taps aligned with an audio recording (such as a musical excerpt or a track of metronome clicks).


