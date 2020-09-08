# midi2cv.py
#
# https://github.com/schollz/midi2cv
#
# convert incoming midi signals to a calibrated voltage
#
# run 'python3 midi2cv.py --tune' to generate a calibraiton
# run 'python3 midi2cv.py --play' to listen to midi
#
import sys
import threading
import time
import os
import json
import math
from subprocess import Popen, PIPE, STDOUT
from signal import signal, SIGINT

import click
import numpy as np
from loguru import logger
import mido
from mido.ports import MultiPort
import termplotlib as tpl

# rail-to-rail voltage
# set this with `--vdd`
rail_to_rail_vdd = 5.2
mb = [1.51, 1.38]
keys_on = 0

#
# mcp4725 functions
#


def init_mcp4725():
    global i2c, dac
    import board
    import busio
    import adafruit_mcp4725

    i2c = busio.I2C(board.SCL, board.SDA)
    dac = adafruit_mcp4725.MCP4725(i2c)


def set_voltage(volts):
    global dac
    # logger.info("setting voltage={}", volts)
    if volts >= 0 and volts < rail_to_rail_vdd:
        dac.value = int(round(float(volts) / rail_to_rail_vdd * 65535.0))


#
# frequency / midi / voltage conversoins
#


def freq_to_voltage(freq):
    return mb[0] * math.log(freq) + mb[1]


def note_to_freq(note):
    a = 440  # frequency of A (common value is 440Hz)
    return (a / 32) * (2 ** ((note - 9) / 12))


def note_to_voltage(note):
    return freq_to_voltage(note_to_freq(note))


def match_note_to_freq(freq):
    closetNote = -1
    closestAmount = 10000
    closestFreq = 10000
    for note in range(1, 90):
        f = note_to_freq(note)
        if abs(f - freq) < closestAmount:
            closestAmount = abs(f - freq)
            closetNote = note
            closestFreq = f
    return closetNote


#
# calibration / tuning
#


def do_tuning():
    print(
        """note! before tuning...

- ...make sure that your synth is connected
  via the USB audio adapter line-in. 
- ...make sure that your synth outputs only
  pure tones (turn off effects!).

"""
    )

    for i in range(5):
        print("initiating tuning in {}".format(5 - i), end="\r")
        time.sleep(1)
    voltage_to_frequency = {}
    previous_freq = 0
    for voltage in range(240, int(rail_to_rail_vdd * 80), 8):
        voltage = float(voltage) / 100.0
        freq = sample_frequency_at_voltage(voltage)
        if freq < previous_freq:
            continue
        voltage_to_frequency[voltage] = freq
        previous_freq = freq
        os.system("clear")
        plot_points(voltage_to_frequency)

    with open("voltage_to_frequency.json", "w") as f:
        f.write(json.dumps(voltage_to_frequency))


def plot_points(voltage_to_frequency):
    x = []
    y0 = []
    for k in voltage_to_frequency:
        x.append(float(k))
        y0.append(voltage_to_frequency[k])
    fig = tpl.figure()
    print("\n")
    fig.plot(
        x,
        y0,
        plot_command="plot '-' w points",
        width=50,
        height=20,
        xlabel="voltage (v)",
        title="frequency (hz) vs voltage",
    )
    fig.show()
    print("\n")


def load_tuning():
    global mb
    voltage_to_frequency = json.load(open("voltage_to_frequency.json", "rb"))
    x = []
    y = []
    y0 = []
    for k in voltage_to_frequency:
        x.append(float(k))
        y0.append(voltage_to_frequency[k])
        y.append(math.log(voltage_to_frequency[k]))
    mb = np.polyfit(y, x, 1)
    fig = tpl.figure()
    print("\n")
    fig.plot(
        x,
        y0,
        plot_command="plot '-' w points",
        width=60,
        height=22,
        xlabel="voltage (v)",
        title="frequency (hz) vs voltage",
        label="freq = exp((volts{:+2.2f})/{:2.2f})   ".format(mb[1], mb[0]),
    )
    fig.show()
    print("\n")
    time.sleep(1)
    # plx.scatter(x, y,cols=80,rows=10,xlim=[np.min(x), np.max(x)])
    # plx.show()


def sample_frequency_at_voltage(voltage):
    set_voltage(voltage)
    time.sleep(1.0)
    record_audio()
    freq = analyze_sox()
    # print("{:2.2f} hz at {:2.2f} volt".format(freq, voltage))
    return freq


def record_audio():
    cmd = "arecord -d 1 -f cd -t wav -D sysdefault:CARD=1 /tmp/1s.wav"
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    output = p.stdout.read()
    if b"Recording WAVE" not in output:
        raise output
    cmd = "sox /tmp/1s.wav -n stat -freq"
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    output = p.stdout.read()
    with open("/tmp/1s.dat", "wb") as f:
        f.write(output)


def analyze_sox():
    previous_amp = 0
    previous_freq = 0
    gathering = -1
    gathered_freqs = []
    gathered_amps = []
    known_frequencies = {}
    known_powers = {}
    with open("/tmp/1s.dat") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                continue
            nums = line.split()
            if len(nums) > 2:
                continue
            amp = float(nums[1])
            freq = float(nums[0])
            if amp > 10 and amp > previous_amp:
                gathering = 0
            if gathering == 0:
                gathered_amps = []
                gathered_freqs = []
                gathered_freqs.append(previous_freq)
                gathered_amps.append(previous_amp)
            if gathering > -1:
                gathering += 1
                gathered_freqs.append(freq)
                gathered_amps.append(amp)
            if gathering == 3:
                gathering = -1
                freq_power = np.sum(gathered_amps)
                freq_average = (
                    np.sum(np.multiply(gathered_amps, gathered_freqs)) / freq_power
                )
                found = False
                for f in known_frequencies:
                    if freq_average < f * 0.92 or freq_average > f * 1.08:
                        continue
                    found = True
                    known_frequencies[f].append(freq_average)
                    known_powers[f].append(freq_power)
                if not found:
                    known_frequencies[freq_average] = [freq_average]
                    known_powers[freq_average] = [freq_power]
            previous_freq = freq
            previous_amp = amp

    freq_and_power = {}
    for f in known_frequencies:
        freq_and_power[np.mean(known_frequencies[f])] = np.mean(known_powers[f])
    for i, v in enumerate(
        sorted(freq_and_power.items(), key=lambda x: x[1], reverse=True)
    ):
        if i == 1:
            return v[0]
    return -1


#
# midi listeners
#


def midi(name):
    global keys_on
    logger.info("listening on '{}'", name)
    with mido.open_input(name) as inport:
        for msg in inport:
            if msg.type == "note_on":
                logger.info(f"{msg.type} {msg.note} {msg.velocity}")
                set_voltage(note_to_voltage(msg.note))
                keys_on += 1
            elif msg.type == "note_off":
                keys_on -= 1
                if keys_on == 0:
                    set_voltage(0)


def listen_for_midi():
    inputs = mido.get_input_names()
    for name in inputs:
        t = threading.Thread(target=midi, args=(name,))
        t.daemon = True
        t.start()

    while True:
        time.sleep(10)


#
# cli
#


def handler(signal_received, frame):
    try:
        set_voltage(0)
    except:
        pass
    logger.info("exiting")
    sys.exit(0)


@click.command()
@click.option("--vdd", help="set the rail-to-rail voltage", default=5.2)
@click.option("--tune", help="activate tuning", is_flag=True, default=False)
@click.option("--play", help="initialize playing", is_flag=True, default=False)
@click.option(
    "--noinit",
    help="do not intiialize mcp4725 (debugging)",
    is_flag=True,
    default=False,
)
def gorun(tune, play, vdd, noinit):
    signal(SIGINT, handler)

    global rail_to_rail_vdd
    rail_to_rail_vdd = vdd

    if not noinit:
        init_mcp4725()
    if tune:
        do_tuning()
    if play:
        load_tuning()
        listen_for_midi()


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> (<cyan>{function}:{line}</cyan>) - {message}")
    print(
        """
███╗   ███╗██╗██████╗ ██╗    ██████╗      ██████╗██╗   ██╗
████╗ ████║██║██╔══██╗██║    ╚════██╗    ██╔════╝██║   ██║
██╔████╔██║██║██║  ██║██║     █████╔╝    ██║     ██║   ██║
██║╚██╔╝██║██║██║  ██║██║    ██╔═══╝     ██║     ╚██╗ ██╔╝
██║ ╚═╝ ██║██║██████╔╝██║    ███████╗    ╚██████╗ ╚████╔╝ 
╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝    ╚══════╝     ╚═════╝  ╚═══╝  
version v0.1.0 (github.com/schollz/midi2cv)

convert any incoming midi signal into a control voltage
from your raspberry pi.
"""
    )
    gorun()
