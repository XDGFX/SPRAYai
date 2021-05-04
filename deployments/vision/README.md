This is the code designed to run on the Raspberry Pis. It's the only deployment which doesn't make use of Docker, as some aspects such as hardware GPIO and use of the camera are more complex to get working within a container, and the benefits of containerisation were not worth the extra complications.

- `host.py` is the main run file, which is started automatically as soon as the Pi boots up.
- The other files contain modules used to help the code to run, such as `logs.py` to handle all logging, or `vision.py` for anything related to the camera.
- `smallFirmata` is the custom firmata code needed to fit onto the ATMega168.
