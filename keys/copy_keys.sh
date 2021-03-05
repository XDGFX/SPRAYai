#!/usr/bin/bash

# Copy public key to new host.
# Argument in the form user@192.168.0.x
# e.g. `./copy_keys.sh nxnx@192.168.0.10`


cat navvy_rsa.pub | ssh $1 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys"
