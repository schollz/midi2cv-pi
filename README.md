```
███╗   ███╗██╗██████╗ ██╗    ██████╗      ██████╗██╗   ██╗
████╗ ████║██║██╔══██╗██║    ╚════██╗    ██╔════╝██║   ██║
██╔████╔██║██║██║  ██║██║     █████╔╝    ██║     ██║   ██║
██║╚██╔╝██║██║██║  ██║██║    ██╔═══╝     ██║     ╚██╗ ██╔╝
██║ ╚═╝ ██║██║██████╔╝██║    ███████╗    ╚██████╗ ╚████╔╝ 
╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝    ╚══════╝     ╚═════╝  ╚═══╝  
```

This is a python script for a Raspberry Pi that can convert MIDI to CV, with automatic tuning to determine relationship between voltage and frequency. No PCBs, and no breadboards required. Just six wires, a MCP4725, a Raspberry Pi, and a CV device you want to add MIDI.

I use this script to control the Korg Monotron Delay via MIDI. More info and tutorial: https://schollz.com/raspberrypi/monotron.

You can use this with basically any device that outputs sound and is controlled via CV. The following are generic instructions. See [the instructions for the Monotron](https://schollz.com/raspberrypi/monotron) for a more specific example.

## Requirements

- Raspberry Pi
- USB audio adapter
- MCP4725


## Setup Raspberry Pi


Use SSH to get into your Raspberry Pi and install the following prerequisites:

```
> sudo apt update
> sudo apt install python3 python3-pip python3-numpy portaudio19-dev sox
> sudo -H python3 -m pip install loguru click mido python-rtmidi adafruit-circuitpython-mcp4725
```

Now download the `midi2cv.py` script:

```
> wget https://raw.githubusercontent.com/schollz/midi2cv/master/midi2cv.py
```

## Tuning

Attach the MCP4725 to the Raspberry Pi and attach the MCP4725 voltage output to your device. Now connect an audio cable from your device to the USB audio adapter on the Raspberry Pi. 

Make sure that your device is outputting as pure a sound as possible. And then run:


```
> python3 midi2cv.py --tune
```

After tuning, it will save a calibration that will automatically load the settings for playing.

## Playing 

First plug in your MIDI devices (if you have) and then just run:

```
> python3 midi2cv.py --play
```

That will automatically load the calibration and listen for any MIDI devices. 

You don't need to plug in a MIDI device, you can always use the MIDI through port to do sequencing, for example with [miti](https://github.com/schollz/miti).

## License 

MIT
