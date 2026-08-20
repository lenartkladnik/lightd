#!/bin/bash
AMPY="$(getent passwd "${SUDO_USER:-$(logname)}" | cut -d: -f6)/.local/bin/ampy"
"$AMPY" --port /dev/$1 $2
