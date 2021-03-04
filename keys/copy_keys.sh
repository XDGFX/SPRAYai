cat navvy_rsa.pub | ssh pi@192.168.0.29 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys"
