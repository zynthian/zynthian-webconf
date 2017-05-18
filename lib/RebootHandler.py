import os
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Reboot Hadler
#------------------------------------------------------------------------------

class RebootHandler(ZynthianConfigHandler):
	def get(self):
		if self.genjson:
			self.write("REBOOT")
		else:
			self.render("config.html", body="reboot_block.html", config=None, title="Reboot", errors=None)
		check_output("(sleep 1 & reboot)&", shell=True)
