import os
import crypt
import logging
import tornado.web
from collections import OrderedDict
from subprocess import check_output

#------------------------------------------------------------------------------
# Login Handler
#------------------------------------------------------------------------------

class LoginHandler(tornado.web.RequestHandler):

	def get(self, errors=None):
		self.render("config.html", body="login_block.html", title="Login", config=None, errors=errors)

	def post(self):
		try:
			root_crypt=check_output("getent shadow root", shell=True).decode("utf-8").split(':')[1]
			rcparts=root_crypt.split('$')
			input_passwd=self.get_argument("PASSWORD")
			input_crypt=crypt.crypt(input_passwd, "$%s$%s" % (rcparts[1],rcparts[2]))
			logging.debug("PASSWD: %s <=> %s" % (root_crypt,input_crypt))
			if input_crypt==root_crypt:
				self.set_secure_cookie("user", "root")
				if self.get_argument("next"):
					self.redirect(self.get_argument("next"))
				else:
					self.redirect("/")
			else:
				self.get({"PASSWORD":"Incorrect Password"})
		except:
				self.get({"PASSWORD":"Authentication Failure"})
