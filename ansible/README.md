Ansible is used for simple deployment of various systems (inference, control, and vision) to many devices at once (e.g. one Jetson and N Raspberry Pis).

- `hosts.ini` contains the devices Ansible will try to connect to. It only has a few default devices currently, but this would be updated to include all the devices for a particular deployment. For example there might be 10 pis, labelled pi0 through pi9.
- `playbook-[device].yaml` contains the instructions for Ansible to go through when deploying to each device. There is a list of 'tasks' which are read from top to bottom, where each will contain a number of commands or processes Ansible must execute in order to meet an objective. The `name` indicates what the task is supposed to do.
- `templates` is just used to store configuration files which are to be copied to the devices, such as the Jetson access point configuration file, `SPRAYai_ap`.
