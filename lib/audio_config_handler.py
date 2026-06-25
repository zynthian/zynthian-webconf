# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
#
# Copyright (C) 2017-2025 Fernando Moyano <jofemodo@zynthian.org>
#
# ********************************************************************
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
#
# ********************************************************************

import os
import copy
import re
import alsaaudio
import logging
import tornado.web
from lib.zynthian_config_handler import ZynthianConfigHandler
from zyngine.zynthian_engine_alsa_mixer import *

# ------------------------------------------------------------------------------
# Soundcard Presets
# ------------------------------------------------------------------------------
try:
    rpi_version_number = int(os.environ.get('RBPI_VERSION_NUMBER', '4'))
except:
    rpi_version_number = 4
if rpi_version_number == 5:
    default_i2s_bufreq_config = "-r 48000 -p 128 -n 2"
else:
    default_i2s_bufreq_config = "-r 48000 -p 256 -n 2"

soundcard_presets = {
    'V5 ADAC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,Digital Right,ADC Left,ADC Right,ADC Left Input,ADC Right Input,PGA Gain Left,PGA Gain Right'
    },
    'Z2 ADAC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,Digital Right,PGA Gain Left,PGA Gain Right,ADC Left Input,ADC Right Input,ADC Left,ADC Right'
    },
    'ZynADAC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,PGA Gain Left,Digital Right,PGA Gain Right,ADC Left Input,ADC Left,ADC Right Input,ADC Right'
    },
    'ZynAudio8x': {
        'SOUNDCARD_CONFIG': 'dtoverlay=zynaudio8x,inputs=8,outputs=8',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:zynaudio8x {default_i2s_bufreq_config} -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'HifiBerry DAC8X': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dac8x\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry -r 48000 -p 256 -n 2 -o 8 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'HifiBerry DAC+ ADC PRO': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,PGA Gain Left,Digital Right,PGA Gain Right,ADC Left Input,ADC Left,ADC Right Input,ADC Right'
    },
    'HifiBerry DAC+ ADC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadc\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
    },
    'HifiBerry DAC+': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplus\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
    },
    'HifiBerry DAC+ light': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dac\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
    },
    'HifiBerry DAC+ RTC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dac\ndtoverlay=i2c-rtc,ds130\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
    },
    'HifiBerry Digi': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-digi\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'HifiBerry Amp': {
        'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-amp\nforce_eeprom_read=0',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:sndrpihifiberry {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'AlloBoss - Innomaker - PCM5142': {
        'SOUNDCARD_CONFIG': 'dtoverlay=allo-boss-dac-pcm512x-audio',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:BossDAC {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': 'Digital Left,PGA Gain Left,Digital Right,PGA Gain Right,ADC Left Input,ADC Left,ADC Right Input,ADC Right'
    },
    'AudioInjector': {
        'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-wm8731-audio',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:audioinjectorpi {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Master Left,Capture Left,Master Right,Capture Right'
    },
    'AudioInjector Isolated': {
        'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-isolated-soundcard',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:audioinjectoris {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'Master Left,Master Right'
    },
    'AudioInjector Ultra': {
        'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-ultra',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:audioinjectorul {default_i2s_bufreq_config} -o 2 -i 2 -X raw",
        'SOUNDCARD_MIXER': 'DAC Left,DAC Right,PGA'
    },
    'Fe-Pi Audio': {
        'SOUNDCARD_CONFIG': 'dtoverlay=fe-pi-audio',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:0 {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'IQAudio DAC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dac',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:IQaudIODAC {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'IQAudio DAC+': {
        'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dacplus',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:IQaudIODAC {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'IQAudio DAC Pro': {
        'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dac',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:Pro {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'IQAudio Digi': {
        'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-digi-wm8804-audio',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:0 {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'JustBoom DAC': {
        'SOUNDCARD_CONFIG': 'dtoverlay=justboom-dac',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:0 {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'JustBoom Digi': {
        'SOUNDCARD_CONFIG': 'dtoverlay=justboom-digi',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:0 {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'PiSound': {
        'SOUNDCARD_CONFIG': 'dtoverlay=pisound',
        'JACKD_OPTIONS': f"-P 70 -s -S -d alsa -d hw:pisound {default_i2s_bufreq_config} -o 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'Generic USB device': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': f"-P 70 -s -d alsa -d hw:0 -r 48000 -p 256 -n 2 -X raw",
        'SOUNDCARD_MIXER': ''
    },
    'Behringer UCA222': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:CODEC -r 48000 -p 256 -n 3 -s -S -X raw',
        'SOUNDCARD_MIXER': 'PCM'
    },
    'Behringer UMC404HD': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:U192k -r 48000 -p 256 -n 3 -s -S -X raw',
        'SOUNDCARD_MIXER': 'UMC404HD_192k_Output,Mic'
    },
    'Behringer UMC1820': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:UMC1820 -r 48000 -p 256 -n 2 -s -S -X raw',
        'SOUNDCARD_MIXER': 'UMC1820 Output'
    },
    'Behringer X18XR18': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:X18XR18 -r 48000 -p 256 -n 2 -s -S -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'C-Media Electronics (Unitek Y-247A)': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Device -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'Creative-EMU 0202': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:USB -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'Edirol UA1-EX': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:UA1EX -r 48000 -p 1024 -n 2 -S -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'GeneralPlus USB': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Device -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': 'Speaker Left,Speaker Right,Mic Left,Mic Right,Auto Gain Control'
    },
    'Lexicon Alpha': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Alpha -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'LogicLink UA0099': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:ICUSBAUDIO7D -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'M-Audio M-Track Plus 2': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Plus -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': 'Mic Left,Mic Right,M-Audio M-Track Plus Left,M-Audio M-Track Plus Right'
    },
    'Steinberg UR22 MKII': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:UR22mkII -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': 'Clock_Source_41_Validity'
    },
    'Tascam US-2x2HR': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:US2x2HR -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'Tascam US-16x08': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:US16x08 -r 48000 -p 256 -n 2 -s -S -X raw',
        'SOUNDCARD_MIXER': ','.join(f'Compressor_{i},Compressor_{i}_switch,Compressor_Attack_{i},Compressor_Ratio_{i},Compressor_Release_{i},Compressor_Threshold_{i},EQ_{i},EQ_High_{i},EQ_High_Frequency_{i},EQ_Low_{i},EQ_Low_Frequency_{i},EQ_MidHigh_{i},EQ_MidHigh_Frequency_{i},EQ_MidHigh_Q_{i},EQ_MidLow_{i},EQ_MidLow_Frequency_{i},EQ_MidLow_Q_{i}' for i in range(16)) + ',DSP_Bypass'
    },
    'Yamaha VKB-100 Vocaloid': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Keyboard -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'Yeti Microphone': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Microphone -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': 'Speaker Left,Mic Left,Speaker Right,Mic Right'
    },
    'RBPi Headphones': {
        'SOUNDCARD_CONFIG': 'dtparam=audio=on\naudio_pwm_mode=2',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:#DEVNAME# -r 48000 -p 512 -n 3 -o 2 -X raw',
        'SOUNDCARD_MIXER': 'Headphone'
    },
    'RBPi HDMI': {
        'SOUNDCARD_CONFIG': 'dtparam=audio=on',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:#DEVNAME# -r 48000 -p 512 -n 2 -o 2 -X raw',
        'SOUNDCARD_MIXER': 'HDMI Left,HDMI Right'
    },
    'Dummy device': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -d alsa -d hw:Dummy -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    },
    'Custom device': {
        'SOUNDCARD_CONFIG': '',
        'JACKD_OPTIONS': '-P 70 -s -S -d alsa -d hw:0 -r 48000 -p 256 -n 2 -X raw',
        'SOUNDCARD_MIXER': ''
    }
}

if rpi_version_number != 5:
    del soundcard_presets["ZynAudio8x"]

try:
    zynthian_engine_alsa_mixer.init_zynapi_instance()
    rbpi_device_name = zynthian_engine_alsa_mixer.zynapi_get_rbpi_device_name()
    logging.info("RBPi Device Name: '{}'".format(rbpi_device_name))
except Exception as err:
    rbpi_device_name = None
    logging.error(err)

if rbpi_device_name == "Headphones":
    soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'] = soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'].replace(
        "#DEVNAME#", "Headphones")
    soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'] = soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'].replace(
        "#DEVNAME#", "b1")
elif rbpi_device_name == "ALSA":
    soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'] = soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'].replace(
        "#DEVNAME#", "ALSA")
    soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'] = soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'].replace(
        "#DEVNAME#", "ALSA")
else:
    del soundcard_presets['RBPi Headphones']
    del soundcard_presets['RBPi HDMI']

# ------------------------------------------------------------------------------
# Audio Configuration Class
# ------------------------------------------------------------------------------


class AudioConfigHandler(ZynthianConfigHandler):

    zctrls = None

    @tornado.web.authenticated
    def get(self, errors=None):

        zc_config = {
            'ZCONTROLLERS': AudioConfigHandler.get_controllers()
        }
        logging.info(zc_config)

        config = {}

        try:
            jackd_options = os.environ.get('JACKD_OPTIONS', "-P 70 -t 2000 -s -d alsa -d hw:0 -r 48000 -p 256 -n 2")
            alsa_config = re.split(r"-d\salsa", jackd_options)[1] + " "
            val = re.search(r"-d\s*(\S*)", alsa_config)
            device = "hw:0" if val is None else val.group(1)[3:]
            val = re.search(r"-r\s*(\S*)", alsa_config)
            samplerate = "48000" if val is None else val.group(1)
            val = re.search(r"-p\s*(\S*)", alsa_config)
            num_frames = "1024" if val is None else val.group(1)
            val = re.search(r"-n\s*(\S*)", alsa_config)
            num_periods = "2" if val is None else val.group(1)
            mode_soft = "1" if " -s" in alsa_config else "0"
            mode_16 = "1" if " -S" in alsa_config else "0"
            latency = 1000 * int(num_periods) * int(num_frames) / int(samplerate)
        except Exception as e:
            logging.error(f"Bad jack configuration {e}")
        device_list = []
        for pcm in alsaaudio.pcms():
            if pcm.startswith("hw:CARD=") and not pcm.startswith("hw:CARD=b1"):
                device_list.append(pcm[8:].split(',')[0])
        if device not in device_list:
            device_list.insert(0, f"{device} (Not detected)")

        if os.environ.get('ZYNTHIAN_KIT_VERSION') != 'Custom':
            custom_options_disabled = True
            config['ZYNTHIAN_MESSAGE'] = {
                'type': 'html',
                'content': "<div class='alert alert-warning'>Some config options are disabled. You may want to <a href='/hw-kit'>choose Custom Kit</a> for enabling all options.</div>"
            }
        else:
            custom_options_disabled = False

        scpresets = copy.copy(soundcard_presets)
        if os.environ.get('ZYNTHIAN_DISABLE_RBPI_AUDIO', '0') == '1':
            try:
                del scpresets['RBPi Headphones']
                del scpresets['RBPi HDMI']
            except:
                pass

        config['SOUNDCARD_NAME'] = {
            'type': 'select',
            'title': "Soundcard",
            'value': os.environ.get('SOUNDCARD_NAME'),
            'options': list(scpresets.keys()),
            'presets': scpresets,
            'disabled': custom_options_disabled,
            'refresh_on_change': True
        }
        config['SOUNDCARD_CONFIG'] = {
            'type': 'textarea',
            'title': "Driver Config",
            'cols': 50,
            'rows': 4,
            'value': os.environ.get('SOUNDCARD_CONFIG'),
            'advanced': True,
            'disabled': custom_options_disabled
        }
        config['ALSA_DEVICE'] = {
            'type': 'select',
            'title': "Soundcard Device",
            'value': device,
            'options': device_list,
            'refresh_on_change': True
        }
        config['_PARAM_WARNING_'] = {
            'type': 'html',
            'content': f"<br><div class='alert alert-warning'>Software latency: {latency:0.1f}ms. (Actual latency may be higher due to soundcard hardware.)<br>Note: Some parameter values do not work on some soundcards.</div>"
        }
        config['ALSA_SAMPLERATE'] = {
            'type': 'select',
            'title': "Samplerate",
            'value': str(samplerate),
            'options': ['32000', '44100', '48000', '96000'],
            'refresh_on_change': True
        }
        config['ALSA_NUM_FRAMES'] = {
            'type': 'select',
            'title': "Buffer Size",
            'value': str(num_frames),
            'options': ['64', '128', '256', '512', '1024', '2048'],
            'refresh_on_change': True
        }
        config['ALSA_NUM_PERIODS'] = {
            'type': 'select',
            'title': "Number of Buffers",
            'value': str(num_periods),
            'options': ['2', '3'],
            'refresh_on_change': True
        }
        config['ALSA_MODE_16'] = {
            'type': 'boolean',
            'title': '16-bit mode',
            'value': mode_16,
            'refresh_on_change': True
        }
        config['ALSA_MODE_SOFT'] = {
            'type': 'boolean',
            'title': 'Soft x-run mode',
            'value': mode_soft,
            'refresh_on_change': True
        }
        config['JACKD_OPTIONS'] = {
            'type': 'text',
            'title': "Jackd Options",
            'value': jackd_options,
            'advanced': True,
            'disabled': custom_options_disabled
        }
        config['ZYNTHIAN_AUBIONOTES_OPTIONS'] = {
            'type': 'text',
            'title': "Aubionotes Options",
            'value': os.environ.get('ZYNTHIAN_AUBIONOTES_OPTIONS', "-O complex -t 0.5 -s -88  -p yinfft -l 0.5"),
            'advanced': True
        }
        if rpi_version_number <= 4:
            config['ZYNTHIAN_DISABLE_RBPI_AUDIO'] = {
                'type': 'boolean',
                'title': "Disable RBPi Audio",
                'value': os.environ.get('ZYNTHIAN_DISABLE_RBPI_AUDIO', '0'),
                'advanced': True,
                'refresh_on_change': True
            }
            if os.environ.get('ZYNTHIAN_DISABLE_RBPI_AUDIO', '0') == '0' and os.environ.get('SOUNDCARD_NAME') != "RBPi Headphones":
                config['ZYNTHIAN_RBPI_HEADPHONES'] = {
                    'type': 'boolean',
                    'title': "RBPi Headphones",
                    'value': os.environ.get('ZYNTHIAN_RBPI_HEADPHONES', '0')
                }
        config['SOUNDCARD_MIXER'] = {
            'type': 'textarea',
            'title': "Mixer Controls",
            'value': os.environ.get('SOUNDCARD_MIXER'),
            'cols': 50,
            'rows': 3,
            'addButton': 'display_zcontroller_panel',
            'addPanel': 'zcontroller.html',
            'addPanelConfig': zc_config,
            'advanced': True
        }
        config['_SPACER_'] = {
            'type': 'html',
            'content': "<br>"
        }

        super().get("Audio", config, errors)

    @tornado.web.authenticated
    def post(self):
        command = self.get_argument('_command', '')
        logging.info("COMMAND = {}".format(command))

        self.request.arguments['ZYNTHIAN_DISABLE_RBPI_AUDIO'] = self.request.arguments.get(
            'ZYNTHIAN_DISABLE_RBPI_AUDIO', '0')
        self.request.arguments['ZYNTHIAN_RBPI_HEADPHONES'] = self.request.arguments.get(
            'ZYNTHIAN_RBPI_HEADPHONES', '0')

        try:
            changed = self.request.arguments['_changed'][0].decode()
            if changed.startswith("ALSA") or command == "SAVE":
                jackd_options = self.get_argument('JACKD_OPTIONS', os.environ.get('JACKD_OPTIONS', "-P 70 -t 2000 -s -d alsa -d hw:0 -r 48000 -p 256 -n 2"))
                jack_config, alsa_config = re.split(r'-d\salsa', jackd_options)
                val = self.get_argument('ALSA_DEVICE')
                if val.endswith(" (Not detected)"):
                    val = val[:-15]
                if val in ("vc4hdmi0", "vc4hdmi1"):
                    dtype = "hdmi"
                else:
                    dtype = "hw"
                match = re.search(r"-d\s*(\S*)", alsa_config)
                if match is None:
                    alsa_config += f" -d {dtype}:{val}"
                else:
                    alsa_config = alsa_config.replace(match.group(0), f"-d {dtype}:{val}")
                if val == "US16x08":
                    # Set default audio routing
                    for idx in range(8):
                        alsaaudio.Mixer("Line Out", idx).setenum(idx + 2)
                    alsaaudio.Mixer("Buss Out").setmute(1)
                val = self.get_argument('ALSA_SAMPLERATE')
                match = re.search(r"-r\s*(\S*)", alsa_config)
                if match is None:
                    alsa_config += f" -r {val}"
                else:
                    alsa_config = alsa_config.replace(match.group(0), f"-r {val}")
                val = self.get_argument('ALSA_NUM_FRAMES')
                match = re.search(r"-p\s*(\S*)", alsa_config)
                if match is None:
                    alsa_config += f" -p {val}"
                else:
                    alsa_config = alsa_config.replace(match.group(0), f"-p {val}")
                val = self.get_argument('ALSA_NUM_PERIODS')
                match = re.search(r"-n\s*(\S*)", alsa_config)
                if match is None:
                    alsa_config += f" -n {val}"
                else:
                    alsa_config = alsa_config.replace(match.group(0), f"-n {val}")
                if self.get_argument("ALSA_MODE_16", "0") == "0":
                    alsa_config = alsa_config.replace(" -S", " ")
                elif " -S" not in alsa_config:
                    alsa_config += " -S"
                if self.get_argument("ALSA_MODE_SOFT", "0") == "0":
                    alsa_config = alsa_config.replace(" -s", " ")
                elif " -s" not in alsa_config:
                    alsa_config += " -s"

                jackd_options = f"{jack_config}-d alsa{alsa_config}"
                self.request.arguments["JACKD_OPTIONS"] = [jackd_options.encode('utf-8')]
        except Exception as e:
            logging.error(e)

        try:
            previous_soundcard = os.environ.get('SOUNDCARD_NAME')
            current_soundcard = self.get_argument('SOUNDCARD_NAME')
            if current_soundcard.startswith('AudioInjector') and current_soundcard != previous_soundcard:
                self.persist_update_sys_flag()
            if current_soundcard == "RBPi Headphones":
                self.request.arguments['ZYNTHIAN_RBPI_HEADPHONES'] = ['0']
        except:
            pass

        posted_config = tornado.escape.recursive_unicode(
            self.request.arguments)

        if command == 'REFRESH':
            errors = None
            self.config_env(posted_config)
        else:
            for k in list(posted_config):
                if k.startswith('ZYNTHIAN_CONTROLLER') or k.startswith('ALSA_'):
                    del posted_config[k]
            errors = self.update_config(posted_config)
            self.reboot_flag = True

        self.get(errors)

    def get_device_name(self):
        try:
            zynthian_engine_alsa_mixer.init_zynapi_instance()
            device_name = zynthian_engine_alsa_mixer.zynapi_get_device_name()
        except Exception as e:
            device_name = 0
            logging.error(e)

        return device_name

    @classmethod
    def get_controllers(cls):
        try:
            zynthian_engine_alsa_mixer.init_zynapi_instance()
            AudioConfigHandler.zctrls = zynthian_engine_alsa_mixer.zynapi_get_controllers("*")
            return AudioConfigHandler.zctrls
        except Exception as e:
            logging.error(e)
            return {}

# ------------------------------------------------------------------------------
