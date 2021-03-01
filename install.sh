#!/bin/sh
# Temporary simple install script
CONFIG_HOME=${XDG_CONFIG_HOME:-~/.config}
KONFSAVE_PATH="${CONFIG_HOME}/konfsave"

# Copy files
mkdir -p "${KONFSAVE_PATH}"
cp *.py "${KONFSAVE_PATH}"
chmod +x "${KONFSAVE_PATH}/main.py"

# Link the executable
mkdir -p ~/.local/bin
ln -sf "${KONFSAVE_PATH}/main.py" ~/.local/bin/konfsave
