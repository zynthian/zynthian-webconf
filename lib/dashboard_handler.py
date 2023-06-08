# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Dashboard Handler
#
# Copyright (C) 2018 Fernando Moyano <jofemodo@zynthian.org>
#
#********************************************************************
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
#********************************************************************

import os
import re
import sys
import logging
import tornado.web
from subprocess import check_output, DEVNULL
from distutils import util
from collections import OrderedDict
from lib.zynthian_config_handler import ZynthianBasicHandler

sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))
import zynconf

#------------------------------------------------------------------------------
# Dashboard Handler
#------------------------------------------------------------------------------

class DashboardHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self):
		# Get git info
		git_info_zyncoder = self.get_git_info("/zynthian/zyncoder")
		git_info_ui = self.get_git_info("/zynthian/zynthian-ui")
		git_info_sys = self.get_git_info("/zynthian/zynthian-sys")
		git_info_webconf = self.get_git_info("/zynthian/zynthian-webconf")
		git_info_data = self.get_git_info("/zynthian/zynthian-data")

		# Get Memory & SD Card info
		ram_info = self.get_ram_info()
		sd_info = self.get_sd_info()

		# get I2C chips info
		i2c_chips = self.get_i2c_chips()
		if len(i2c_chips)>0:
			i2c_info = ", ".join(map(str, i2c_chips))
		else:
			i2c_info = "Not detected"

		config = OrderedDict([
			['HARDWARE', {
				#'icon': 'glyphicon glyphicon-wrench',
				'icon': 'glyphicon glyphicon-cog',
				'info': OrderedDict([
					['RBPI_VERSION', {
						'title': os.environ.get('RBPI_VERSION')
					}],
					['SOUNDCARD_NAME', {
						'title': 'Audio',
						'value': os.environ.get('SOUNDCARD_NAME'),
						'url': "/hw-audio"
					}],
					['DISPLAY_NAME', {
						'title': 'Display',
						'value': os.environ.get('DISPLAY_NAME'),
						'url': "/hw-display"
					}],
					['WIRING_LAYOUT', {
						'title': 'Wiring',
						'value': os.environ.get('ZYNTHIAN_WIRING_LAYOUT'),
						'url': "/hw-wiring"
					}],
					['I2C_CHIPS', {
						'title': 'I2C',
						'value': i2c_info,
						'url': "/hw-wiring"
					}]
				])
			}],
			['SYSTEM', {
				#'icon': 'glyphicon glyphicon-dashboard',
				'icon': 'glyphicon glyphicon-tasks',
				'info': OrderedDict([
					['OS_INFO', {
						'title': "{}".format(self.get_os_info())
					}],
					['BUILD_DATE', {
						'title': 'Build Date',
						'value': self.get_build_info()['Timestamp'],
					}],
					['RAM', {
						'title': 'Memory',
						'value': "{} ({}/{})".format(ram_info['usage'],ram_info['used'],ram_info['total'])
					}],
					['SD CARD', {
						'title': 'SD Card',
						'value': "{} ({}/{})".format(sd_info['usage'],sd_info['used'],sd_info['total'])
					}],
					['TEMPERATURE', {
						'title': 'Temperature',
						'value': self.get_temperature()
					}],
					['OVERCLOCKING', {
						'title': 'Overclock',
						'value': os.environ.get('ZYNTHIAN_OVERCLOCKING','Disabled'),
						'url': "/hw-options"
					}]
				])
			}],
			['MIDI', {
				'icon': 'glyphicon glyphicon-music',
				'info': OrderedDict([
					['PROFILE', {
						'title': 'Profile',
						'value': os.path.basename(os.environ.get('ZYNTHIAN_SCRIPT_MIDI_PROFILE',"")),
						'url': "/ui-midi-options"
					}],
					['FINE_TUNING', {
						'title': 'Tuning',
						'value': "{} Hz".format(os.environ.get('ZYNTHIAN_MIDI_FINE_TUNING',"440")),
						'url': "/ui-midi-options"
					}],
					['SINGLE_ACTIVE_CHANNEL', {
						'title': 'Receive Mode',
						'value': self.get_midi_receive_mode(),
						'url': "/ui-midi-options"
					}],
					['ZS3_SUBSNAPSHOTS', {
						'title': 'ZS3 Sub-SnapShots',
						'value': self.bool2onoff(os.environ.get('ZYNTHIAN_MIDI_PROG_CHANGE_ZS3','1')),
						'url': "/ui-midi-options"
					}],
					['MIDI_FILTER_OUTPUT', {
						'title': 'MIDI to Output',
						'value': self.bool2onoff(os.environ.get('ZYNTHIAN_MIDI_FILTER_OUTPUT','1')),
						'url': "/ui-midi-options"
					}],
					['MASTER_CHANNEL', {
						'title': 'Master Channel',
						'value': self.get_midi_master_chan(),
						'url': "/ui-midi-options"
					}]
				])
			}],
			['SOFTWARE', {
				'icon': 'glyphicon glyphicon-random',
				'info': OrderedDict([
					['ZYNCODER', {
						'title': 'zyncoder',
						'value': "%s (%s) %s" % (git_info_zyncoder['branch'], git_info_zyncoder['gitid'][0:7], 'Update available' if git_info_zyncoder['update'] == '1' else ''),
						'url': "https://github.com/zynthian/zyncoder/commit/{}".format(git_info_zyncoder['gitid'])
					}],
					['UI', {
						'title': 'zynthian-ui',
						'value': "{} ({})".format(git_info_ui['branch'], git_info_ui['gitid'][0:7], 'Update available' if git_info_ui['update'] == '1' else ''),
						'url': "https://github.com/zynthian/zynthian-ui/commit/{}".format(git_info_ui['gitid'])
					}],
					['SYS', {
						'title': 'zynthian-sys',
						'value': "{} ({})".format(git_info_sys['branch'], git_info_sys['gitid'][0:7], 'Update available' if git_info_sys['update'] == '1' else ''),
						'url': "https://github.com/zynthian/zynthian-sys/commit/{}".format(git_info_sys['gitid'])
					}],
					['DATA', {
						'title': 'zynthian-data',
						'value': "{} ({})".format(git_info_data['branch'], git_info_data['gitid'][0:7], 'Update available' if git_info_data['update'] == '1' else ''),
						'url': "https://github.com/zynthian/zynthian-data/commit/{}".format(git_info_data['gitid'])
					}],
					['WEBCONF', {
						'title': 'zynthian-webconf',
						'value': "{} ({})".format(git_info_webconf['branch'], git_info_webconf['gitid'][0:7], 'Update available' if git_info_webconf['update'] == '1' else ''),
						'url': "https://github.com/zynthian/zynthian-webconf/commit/{}".format(git_info_webconf['gitid'])
					}]
				])
			}],
			['LIBRARY', {
				'icon': 'glyphicon glyphicon-book',
				'info': OrderedDict([
					['SNAPSHOTS', {
						'title': 'Snapshots',
						'value': str(self.get_num_of_files(os.environ.get('ZYNTHIAN_MY_DATA_DIR')+"/snapshots")),
						'url': "/lib-snapshot"
					}],
					['USER_PRESETS', {
						'title': 'User Presets',
						'value': str(self.get_num_of_presets(os.environ.get('ZYNTHIAN_MY_DATA_DIR')+"/presets")),
						'url': "/lib-presets"
					}],
					['USER_SOUNDFONTS', {
						'title': 'User Soundfonts',
						'value': str(self.get_num_of_files(os.environ.get('ZYNTHIAN_MY_DATA_DIR')+"/soundfonts")),
						'url': "/lib-soundfont"
					}],
					['AUDIO_CAPTURES', {
						'title': 'Audio Captures',
						'value': str(self.get_num_of_files(os.environ.get('ZYNTHIAN_MY_DATA_DIR')+"/capture","*.wav")),
						'url': "/lib-captures"
					}],
					['MIDI_CAPTURES', {
						'title': 'MIDI Captures',
						'value': str(self.get_num_of_files(os.environ.get('ZYNTHIAN_MY_DATA_DIR')+"/capture","*.mid")),
						'url': "/lib-captures"
					}]
				])
			}],
			['NETWORK', {
				'icon': 'glyphicon glyphicon-link',
				'info': OrderedDict([
					['HOSTNAME', {
						'title': 'Hostname',
						'value': self.get_host_name(),
						'url': "/sys-security"
					}],
					['WIFI', {
						'title': 'Wifi',
						'value': zynconf.get_current_wifi_mode(),
						'url': "/sys-wifi"
					}],
					['IP', {
						'title': 'IP',
						'value': self.get_ip(),
						'url': "/sys-wifi"
					}],
					['RTPMIDI', {
						'title': 'RTP-MIDI',
						'value': self.bool2onoff(self.is_service_active("jackrtpmidid")),
						'url': "/ui-midi-options"
					}],
					['QMIDINET', {
						'title': 'QMidiNet',
						'value': self.bool2onoff(self.is_service_active("qmidinet")),
						'url': "/ui-midi-options"
					}]
				])
			}]
		])

		if len(i2c_chips)<=2:
			config['HARDWARE']['info']['CUSTOM_WIRING_PROFILE'] = {
				'title': "Profile",
				'value': os.environ.get('ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE',''),
				'url': "/hw-wiring"
			}
	
		media_usb0_info = self.get_media_info('/media/usb0')
		if media_usb0_info:
			config['SYSTEM']['info']['MEDIA_USB0'] = {
				'title': "USB Storage",
				'value': "{} ({}/{})".format(media_usb0_info['usage'],media_usb0_info['used'],media_usb0_info['total']),
				'url': "/lib-captures"
			}

		if self.is_service_active("touchosc2midi"):
			config['NETWORK']['info']['TOUCHOSC'] = {
				'title': 'TouchOSC',
				'value': 'on',
				'url': "/ui-midi-options"
			}

		super().get("dashboard_block.html", "Dashboard", config, None)


	@staticmethod
	def get_git_info(path, check_updates=False):
		branch = check_output("cd %s; git branch | grep '*'" % path, shell=True).decode()[2:-1]
		gitid = check_output("cd %s; git rev-parse HEAD" % path, shell=True).decode()[:-1]
		if check_updates:
			update = check_output("cd %s; git remote update; git status --porcelain -bs | grep behind | wc -l" % path, shell=True).decode()
		else:
			update = None
		return { "branch": branch, "gitid": gitid, "update": update }


	@staticmethod
	def get_host_name():
		with open("/etc/hostname") as f:
			hostname = f.readline()
			return hostname


	@staticmethod
	def get_os_info():
		return check_output("lsb_release -ds", shell=True).decode()


	@staticmethod
	def get_build_info():
		info = {}
		try:
			zynthian_dir = os.environ.get('ZYNTHIAN_DIR',"/zynthian")
			with open(zynthian_dir + "/build_info.txt", 'r') as f:
				rows = f.read().split("\n")
				f.close()
				for row in rows:
					try:
						k,v = row.split(": ")
						info[k] = v
						logging.debug("Build info => {}: {}".format(k,v))
					except:
						pass
		except Exception as e:
			logging.warning("Can't get build info! => {}".format(e))
			info['Timestamp'] = '???'

		return info


	@staticmethod
	def get_ip():
		#out=check_output("hostname -I | cut -f1 -d' '", shell=True).decode()
		ips = []
		for ip in check_output("hostname -I", shell=True).decode().split(" "):
			# Filter ip6 addresses
			if '.' in ip:
				ips.append(ip)
		return " ".join(ips)


	@staticmethod
	def get_i2c_chips():
		res = []
		out = check_output("gpio i2cd", shell=True).decode().split("\n")
		if len(out) > 3:
			for i in range(1, 8):
				for adr in out[i][4:].split(" "):
					try:
						adr = int(adr, 16)
						if adr>=0x20 and adr<=0x27:
							out1 = check_output("i2cget -y 1 {} 0x01".format(adr), shell=True).decode().strip()
							out2 = check_output("i2cget -y 1 {} 0x10".format(adr), shell=True).decode().strip()
							if out1 == '0x00' and out2 == '0x00':
								res.append("MCP23008@0x{:02X}".format(adr))
							else:
								res.append("MCP23017@0x{:02X}".format(adr))
						elif adr>=0x48 and adr<=0x4B:
							res.append("ADS1115@0x{:02X}".format(adr))
						elif adr>=0x61 and adr<=0x67:
							res.append("MCP4728@0x{:02X}".format(adr))
					except:
						pass
		return res


	@staticmethod
	def get_ram_info():
		out=check_output("free -m | grep 'Mem'", shell=True).decode()
		parts=re.split('\s+', out)
		return { 'total': parts[1]+"M", 'used': parts[2]+"M", 'free': parts[3]+"M", 'usage': "{}%".format(int(100*float(parts[2])/float(parts[1]))) }


	@staticmethod
	def get_temperature():
		try:
			return check_output("/opt/vc/bin/vcgencmd measure_temp", shell=True).decode()[5:-3] + "ºC"
		except:
			return "???"


	@staticmethod
	def get_volume_info(volume='/dev/root'):
		try:
			out=check_output("df -h | grep '{}'".format(volume), shell=True).decode()
			parts=re.split('\s+', out)
			return { 'total': parts[1], 'used': parts[2], 'free': parts[3], 'usage': parts[4] }
		except:
			return { 'total': 'NA', 'used': 'NA', 'free': 'NA', 'usage': 'NA' }


	@staticmethod
	def get_sd_info():
		return DashboardHandler.get_volume_info('/dev/root')


	@staticmethod
	def get_media_info(mpath="/media/usb0"):
		try:
			out=check_output("mountpoint '{}'".format(mpath), shell=True).decode()
			if out.startswith("{} is a mountpoint".format(mpath)):
				return DashboardHandler.get_volume_info(mpath)
			else:
				return None
		except Exception as e:
			#logging.error("Can't get info for '{}' => {}".format(mpath,e))
			pass


	@staticmethod
	def get_num_of_files(path, pattern=None):
		if pattern:
			pattern = "-name \"{}\"".format(pattern)
		else:
			pattern = ""
		try:
			n=int(check_output("find {} -type f -follow {} | wc -l".format(path, pattern), shell=True, stderr=DEVNULL).decode())
		except Exception as e:
			logging.error("Can't get num of files for '{}' => {}".format(path,e))
			n=0
		return n


	@staticmethod
	def get_num_of_presets(path):
		# LV2 presets
		n1 = int(check_output("find {}/lv2 -type f -prune -name manifest.ttl | wc -l".format(path), shell=True).decode())
		logging.debug("LV2 presets => {}".format(n1))
		# Pianoteq presets
		n2 = int(check_output("find {}/pianoteq -type f -prune | wc -l".format(path), shell=True).decode())
		logging.debug("Pianoteq presets => {}".format(n2))
		# Puredata presets
		n3 = int(check_output("find {}/puredata/*/* -type d -prune | wc -l".format(path), shell=True, stderr=DEVNULL).decode())
		logging.debug("Puredata presets => {}".format(n3))
		# ZynAddSubFX presets
		n4 = int(check_output("find {}/zynaddsubfx -type f -name *.xiz | wc -l".format(path), shell=True).decode())
		logging.debug("ZynAddSubFX presets => {}".format(n4))
		return n1 + n2 + n3 + n4


	@staticmethod
	def get_midi_master_chan():
		mmc = os.environ.get('ZYNTHIAN_MIDI_MASTER_CHANNEL',"16")
		if int(mmc)==0:
			return "off"
		else:
			return mmc


	@staticmethod
	def get_midi_receive_mode():
		if os.environ.get('ZYNTHIAN_MIDI_SINGLE_ACTIVE_CHANNEL','0'):
			return "Stage (Omni On)"
		else:
			return "Multi-timbral"


	@staticmethod
	def is_service_active(service):
		cmd="systemctl is-active %s" % service
		try:
			result=check_output(cmd, shell=True).decode('utf-8','ignore')
		except Exception as e:
			result="ERROR: %s" % e
		#print("Is service "+str(service)+" active? => "+str(result))
		if result.strip()=='active': return True
		else: return False


	@staticmethod
	def bool2onoff(b):
		if (isinstance(b, str) and util.strtobool(b)) or (isinstance(b, bool) and b):
			return "On"
		else:
			return "Off"

