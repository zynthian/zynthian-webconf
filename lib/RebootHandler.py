import os
import logging
import tornado.web
from subprocess import check_output
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Reboot Hadler
#------------------------------------------------------------------------------

class RebootHandler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self):
		if self.genjson:
			self.write("REBOOT")
		else:
			self.render("config.html", body="reboot_block.html", config=None, title="Reboot", errors=None)
		try:
			check_output("(sleep 1 & reboot)&", shell=True)
		except Exception as e:
			logging.error("Updating Sytem Config: %s" % e)
