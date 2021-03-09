# Konfsave

Konfsave is a config manager. That is, it allows you to save, back up, and easily switch between different (per-user) system configurations.
Each configuration is stored as a profile; the script allows you to save the current configuration as a named profile,
and then load them by name. It's also possible to take these profiles somewhere else by exporting or importing them, or just copying their folder.

By default, Konfsave manages your KDE configuration - specifically, its appearance and workspace settings. This can be easily changed in `config.ini`.
If you'd like to learn more about how to adjust the configuration, see the [wiki](https://github.com/selplacei/konfsave/wiki).

Inspired by https://github.com/Prayag2/konsave.

## Notable features

- Storing the current configuration as a profile
- Adding extra info to profiles, e.g. a description
- Optionally following symlinks
- Remembering which profile is active at the moment
- Updating existing profiles
- Listing and configuring paths or groups of paths to save
- Specifying additional paths to include or exclude using command-line arguments
- Archiving (exporting) and importing profiles (with adjustable compression level and type)

## Requirements

Python 3.8+ is required.

## Installation & Usage

The configuration file, `config.ini`, is stored in `$XDG_CONFIG_HOME/konfsave` (usually it's `~/.config/konfsave`).  
Usage instructions can be viewed with `konfsave --help`.

There are 2 installation options:

#### PyPI

Konfsave is on [PyPI](https://pypi.org/project/konfsave/), which means that it can be installed with `pip`:  
	`python -m pip install konfsave`  
After this, you should be able to run Konfsave directly from the terminal. If not, try `python -m konfsave`.

#### The crude way

This method is not recommended unless you're debugging or rewriting Konfsave.  
`__main__.py` can be run as is; just download the repository.
You can also run `install.sh` which will copy files to `.config` and link `__main__.py` to `.local/bin/konfsave`.
Unlike the PyPI method, this will not allow you to easily update the program.

## Future features

- Specifying a profile type - for example, a profile of type 'gtk' will only save and load GTK configs by default - this will extend Konfsave beyond KDE
- Optionally storing profiles as Git repositories

## License

Copyright (c) 2021 Illia Boiko (selplacei) and contributors. All source code in this repository may only be used under the terms and conditions found in the LICENSE file.
