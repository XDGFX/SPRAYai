# Installation
Setting up dependencies for the control server will differ from development to production.

## Development
1. Will run in a virtual environment for simplicity. `pip` and `venv` must both be installed.
```bash
$ sudo apt-get update
$ sudo apt-get upgrade
$ sudo apt-get -y install python3-pip python3-venv
```

2. `cd` into the `control` folder.
```bash
$ python3 -m venv .venv
$ source .venv/bin/activate.fish
$ pip3 install -r requirements.txt
```

3. Create a new `nodeenv` environment.
```bash
$ nodeenv -p; npm install -g npm; npm -v
```

4. Install sass to compile CSS.
```bash
$ npm install sass
```

5. Compile CSS using:
```bash
$ sass --no-source-map app/static/sass/custom_bulma.scss:app/static/css/custom_bulma.css
```