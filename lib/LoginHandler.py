import os
import tornado.web
from collections import OrderedDict

#------------------------------------------------------------------------------
# Login Handler
#------------------------------------------------------------------------------

class LoginHandler(tornado.web.RequestHandler):

	def get(self, errors=None):
		self.render("config.html", body="login_block.html", title="Login", config=None, errors=errors)

	def post(self):
		if self.get_argument("PASSWORD")=="raspberry":
			self.set_secure_cookie("user", "root")
			if self.get_argument("next"):
				self.redirect(self.get_argument("next"))
			else:
				self.redirect("/")
		else:
			self.get({"PASSWORD":"Incorrect Password"})
