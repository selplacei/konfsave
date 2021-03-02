#!/bin/sh
# Temporary simple install script
CONFIG_HOME=${XDG_CONFIG_HOME:-~/.config}
KONFSAVE_PATH="${CONFIG_HOME}/konfsave"

# Copy files
mkdir -p "${KONFSAVE_PATH}"
cp konfsave/*.py "${KONFSAVE_PATH}"
cp konfsave/default_config.ini "${KONFSAVE_PATH}"
chmod +x "${KONFSAVE_PATH}/__main__.py"

# Link the executable
mkdir -p ~/.local/bin
ln -sf "${KONFSAVE_PATH}/__main__.py" ~/.local/bin/konfsave
