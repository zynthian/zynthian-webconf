#!/bin/bash

source "$ZYNTHIAN_SYS_DIR/scripts/zynthian_envars_extended.sh"

# 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL
export ZYNTHIAN_LOG_LEVEL=10
export ZYNTHIAN_WEBCONF_LOG_LEVEL=10

./zynthian_webconf.py
