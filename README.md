# Konfsave

Konfsave is a KDE config manager. That is, it allows you to save, back up, and easily switch between different KDE configurations.
Each configuration is stored as a profile; the script allows you to save the current configuration as a named profile,
and then load profiles by name. Of course, it's also possible to take these profiles somewhere else by just copying their folder.

OK, I lied. Although this is supposed to be a KDE config manager, it can work for pretty much anything that's stored in your home directory. You still have to be on a UNIX-like system, however. Just change the paths in `config.ini` to suit your needs and use '--no-restart' to disable restarting the Plasma shell if you don't care about its configs.

Inspired by https://github.com/Prayag2/konsave.

## Notable features

- Storing the current configuration as a profile
- Optionally following symlinks
- Remembering which profile is active at the moment
- Updating existing profiles
- Switching between profiles
- Listing and configuring paths to save (both files and directories are supported)
- Per-profile configuration of additional paths to save or exclude by default
- Specifying additional paths to include or exclude using command-line arguments
- Archiving (exporting) and importing profiles

## Requirements

Python 3.8+ is required.

## Installation & Usage

The configuration file, `config.ini`, is stored in `${XDG_CONFIG_HOME}/konfsave`.  
Usage instructions can be viewed with `konfsave --help`.

There are 2 installation options:

#### PyPI

Konfsave is on [PyPI](https://pypi.org/project/konfsave/), which means that it can be installed with `pip`:  
	`python -m pip install konfsave`  
After this, you should be able to run Konfsave directly from the terminal. If not, try `python -m konfsave`.

#### The crude way

`__main__.py` can be run as is; just download the repository.
You can also run `install.sh` which will copy files to `.config` and link `__main__.py` to `.local/bin/konfsave`.
Unlike the PyPI method, this will not allow you to easily update the program.

## Future features

Right now, this program is WIP. Although it's useful in its current state, more features are planned, such as storing profiles as Git repositories and printing human-friendly information about which files are saved and what they do.

## License

Copyright (c) 2021 Illia Boiko (selplacei) and contributors. All source code in this repository may only be used under the terms and conditions found in the LICENSE file.
