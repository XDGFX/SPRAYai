This folder contains all the program code for the main control server.

- `static` and `templates` contain web files required to build the UI (more information can be found inside their respective `README.mds`).
- `__init__.py` starts the control server, and handles all web and UI related tasks.
- `logs.py` handles all logging and custom handlers, e.g. for Redis log caching.
- `settings.default.json` contains all the default persistent settings. On first run, `settings.json` is created from this, and stores any updates made (which is handled with `settings.py`). 
- `util.py` is a general utilities module, but currently only houses the custom live updater code for the UI.
