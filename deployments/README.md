This is where most of the projects code is stored. `deployments` indicates these are the modules which will be deployed to specific devices in order to run the SPRAYai system.

- `control` is the main SPRAYai control system. It handles hosting the WebUI, receiving spray commands, communication with all Raspberry Pis, centralised logging, storing and retrieval of settings, and a handful of other jobs.
- `detector` is the machine learning inference server. All it does it wait for requests in the form of an image, and when it receives one it'll perform inference and then return the results.
- `vision` is the software which runs on the Raspberry Pis. It handles all camera capture, as well as managing image queues and caches, communication with the `detector` for inference, as well as anything related to mechanical control of the system. This includes communication with an Arduino for servo and solenoid output.

`control` and `detector` are both designed to run as Docker containers. More information is available inside their respective folders.
