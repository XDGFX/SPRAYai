cat navvy_rsa.pub | ssh ubuntu@192.168.1.161 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys"