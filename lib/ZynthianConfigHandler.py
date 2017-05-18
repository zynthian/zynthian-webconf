import os
import tornado.web
from subprocess import check_output

#------------------------------------------------------------------------------
# Zynthian Config Handler
#------------------------------------------------------------------------------

class ZynthianConfigHandler(tornado.web.RequestHandler):

	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass

	def update_config(self, config):
		# Get config file content
		fpath=os.environ.get('ZYNTHIAN_SYS_DIR')+"/scripts/zynthian_envars.sh"
		if not os.path.isfile(fpath):
			fpath="./zynthian_envars.sh"
		with open(fpath) as f:
			lines = f.readlines()

		# Find and replace lines to update
		pattern=re.compile("^export ([^\s]*?)=")
		for i,line in enumerate(lines):
			res=pattern.match(line)
			if res:
				varname=res.group(1)
				if varname in config:
					value=config[varname][0].replace("\n", "\\n")
					value=value.replace("\r", "")
					os.environ[varname]=value
					lines[i]="export %s=\"%s\"\n" % (varname,value)
					logging.info(lines[i],end='')

		# Write updated config file
		with open(fpath,'w') as f:
			f.writelines(lines)

		# Update System Configuration
		try:
			check_output(os.environ.get('ZYNTHIAN_SYS_DIR')+"/scripts/update_zynthian_sys.sh", shell=True)
		except Exception as e:
			logging.error("Updating Sytem Config: %s" % e)
