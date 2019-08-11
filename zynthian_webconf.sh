#!/bin/bash

if [ -f "./zynthian_envars.sh" ]; then
	source "./zynthian_envars.sh"
elif [ -d "$ZYNTHIAN_CONFIG_DIR" ]; then
	source "$ZYNTHIAN_CONFIG_DIR/zynthian_envars.sh"
else
	source "$ZYNTHIAN_SYS_DIR/scripts/zynthian_envars.sh"
fi

# 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL
export ZYNTHIAN_WEBCONF_LOG_LEVEL=10

./zynthian_webconf.py
