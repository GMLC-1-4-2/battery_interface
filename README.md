## Battery Interface

Implementation of Device Models and their Battery Equivalent Interface


## How to contribute

- On Github, “fork” the GMLC-1-4-2 repository to one of your own (if your github registration name is ‘jeff’, you’d fork GMLC-1-4-2/battery_interface to jeff/battery_interface).
- On your own computer, “clone” the github jeff/battery_interface repository to your local disk.
- On your own computer, create your workspace:
    - Create a new directory for your work (e.g, my_fleet or my_service) inside of "fleets" or "services" directory
    - Add/edit/delete files in your workspace  
- Commit and push your edits from your local computer up to jeff/battery_interface on github.
- On Github, send a “pull request” to get your latest jeff/battery_interface changes incorporated into the main GMLC-1-4-2/battery_interface repository.

Notes: If you just want to get the code and test it, then use "clone" the GMLC-1-4-2 repository instead of "fork".


## Setup Work Environment
- Install Python3.5 or higher
- Install pip
- Install all dependencies:

```sh
$ cd battery_interface
$ pip install -r requirements.txt
```

## How to run

To run integration test:

```sh
$ cd battery_interface/src/
$ python test.py
```

To test a service (e.g., Regulation Service):

```sh
$ cd battery_interface/src/services/reg_service/
$ python test.py
```

To test a fleet (e.g., Battery Inverter):

```sh
$ cd battery_interface/src/fleets/battery_inverter_fleet/
$ python test.py
```


## License
The project is private and the license will be added soon.
