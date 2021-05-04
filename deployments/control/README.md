This is the deployment for main system control. This code runs on the Jetson Xavier.

All the files in this folder are for helping setup or installation of the environment, including the `Dockerfile` to create a Docker image, `INSTALL.md` which contains instructions for setting up the development environment, the Python pip `requirements.txt`, and a bash file to `update_sass.sh` files, to save typing the command whenever a stylesheet needs to be recompiled.

`app` contains all the actual code which this deployment runs with.
