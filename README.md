```
███╗   ███╗██╗██████╗ ██╗    ██████╗      ██████╗██╗   ██╗
████╗ ████║██║██╔══██╗██║    ╚════██╗    ██╔════╝██║   ██║
██╔████╔██║██║██║  ██║██║     █████╔╝    ██║     ██║   ██║
██║╚██╔╝██║██║██║  ██║██║    ██╔═══╝     ██║     ╚██╗ ██╔╝
██║ ╚═╝ ██║██║██████╔╝██║    ███████╗    ╚██████╗ ╚████╔╝ 
╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝    ╚══════╝     ╚═════╝  ╚═══╝  
```

This is a python script for a Raspberry Pi that can convert MIDI to CV, with automatic tuning to determine relationship between voltage and frequency. No PCBs, and no breadboards required. You just need a Raspberry Pi, a USB audio interface, a cheap DAC, and the CV synth that you want to add MIDI.

I use this script to control the Korg Monotron Delay via MIDI but it might work with other CV instruments. More info and tutorial for using with the Monotron: https://schollz.com/raspberrypi/monotron.

## Requirements

- [Raspberry Pi](https://www.amazon.com/gp/product/B07BC7BMHY/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B07BC7BMHY&linkCode=as2&tag=scholl-20) (any model should work)
- [USB audio adapter](https://www.amazon.com/gp/product/B01N905VOY/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B01N905VOY&linkCode=as2&tag=scholl-20) (~$16)
- [MCP4725](https://www.amazon.com/gp/product/B00SK8MBXI/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B00SK8MBXI&linkCode=as2&tag=scholl-20) (~$11)
- [Female-to-female jumper cables](https://www.amazon.com/gp/product/B01L5ULRUA/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B01L5ULRUA&linkCode=as2&tag=scholl-20) (~$6)


## Setup Raspberry Pi


Use SSH to get into your Raspberry Pi and install the following prerequisites:

```
> sudo apt update
> sudo apt install python3 python3-pip python3-numpy portaudio19-dev sox gnuplot ffmpeg
> sudo -H python3 -m pip install loguru click mido python-rtmidi adafruit-circuitpython-mcp4725 termplotlib aubio
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
