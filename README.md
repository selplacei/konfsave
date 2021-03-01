# Konfsave

Konfsave is a KDE config manager. That is, it allows you to save, back up, and easily switch between different KDE configurations.
Each configuration is stored as a profile; the script allows you to save the current configuration as a named profile,
and then load profiles by name. Of course, it's also possible to take these profiles somewhere else by just copying their folder.

OK, I lied. Although this is supposed to be a KDE config manager, it can work for pretty much anything that's stored in your home directory. You still have to be on a UNIX-like system, however. Just change the paths in `config.py` to suit your needs and use '--no-restart' to disable restarting the Plasma shell if you don't care about its configs.

## Notable features

- Storing the current configuration as a profile
- Remembering which profile is active at the moment
- Updating profiles with new configuration
- Switching between profiles
- Listing and configuring paths to save (both files and directories are supported)
- Per-profile configuration of additional paths to save or exclude by default
- Specifying additional paths to include or exclude using command-line arguments
- Optionally following symlinks when saving paths

Other minor features can be discovered through the help messages and/or `config.py`.

## Requirements

Python 3.8+ is required.

## Installation & Usage

`main.py` can be run as is, but Konfsave expects its `config.py` to be in `${XDG_CONFIG_HOME}/konfsave`.
You can use the `install.sh` script to properly install Konfsave for the current user.

Usage instructions can be viewed with `konfsave --help`.

## Future features

Right now, this program is WIP. Although you could find it useful in its current state, more features are planned, such as storing profiles as Git repositories and archiving/compressing them.

## License

Copyright (c) 2021 Illia Boiko (selplacei). All source code in this repository may only be used under the terms and conditions found in the LICENSE file.
