#!/bin/bash

if [ -f "./zynthian_envars.sh" ]; then
	source "./zynthian_envars.sh"
elif [ -d "$ZYNTHIAN_CONFIG_DIR" ]; then
	source "$ZYNTHIAN_CONFIG_DIR/zynthian_envars.sh"
else
	source "$ZYNTHIAN_SYS_DIR/scripts/zynthian_envars.sh"
fi

./zynthian_webconf.py
