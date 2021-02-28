# Konfsave

Konfsave is a KDE config manager. That is, it allows you to save, back up, and easily switch between different KDE configurations. Each configuration is stored as a profile; the script allows you to save the current configuration as a named profile, and then load profiles by name. Of course, it's also possible to take these profiles somewhere else by just copying the folder.

OK, I lied. Although this is supposed to be a KDE config manager, it can work for pretty much anything that's stored in your home directory. You still have to be on a UNIX-like system, however. Just change the paths in `config.py` to suit your needs.

## Future features

Right now, this program is WIP; although you could find it useful in its current state, it's incomplete. Specifically, planned features include storing profiles as Git repositories and archiving/compressing them.

## Requirements

Python 3.9+ is required.

## License

Copyright (c) 2021 Illia Boiko (selplacei). All source code in this repository may only be used under the terms and conditions found in the LICENSE file.
