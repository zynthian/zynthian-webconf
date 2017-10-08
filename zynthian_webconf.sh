#!/bin/bash

if [ -f "./zynthian_envars.sh" ]; then
	source "./zynthian_envars.sh"
elif [ -d "$ZYNTHIAN_CONFIG_DIR" ]; then
	source "$ZYNTHIAN_CONFIG_DIR/zynthian_envars.sh"
else
	source "$ZYNTHIAN_SYS_DIR/scripts/zynthian_envars.sh"
fi

export PYTHONPATH="${PYTHONPATH}:$ZYNTHIAN_UI_DIR"
echo $PYTHONPATH

./zynthian_webconf.py
