# GMLC 1.4.2. Definitions, Standards and Test Procedures for Grid Services from Devices

This overarching goal of this project is to enable and spur the deployment of a broad range of distributed energy resource (DER) devices with the ability to provide much of the flexibility required for operating a clean and reliable power grid at reasonable cost. The required flexibility, expressed in the form of a growing number of increasingly valuable services at the bulk system and local distribution levels, is largely embodied in grid services that are provided by power plants and substations today. However, it is also increasingly reflected in wholesale market products or utility programs in which DERs participate. The project’s objectives address the primary barriers that limit the ability of grid operational and planning tools to assess the ability of such devices to provide these services, at scale, in the future power grid.

## Battery Interface

Implementation of Device Models and their Battery Equivalent Interface


## List of fully functional code

A list of all the devices and services which classes are fully functional is shown in the following table:

|            Device\Service            | Peak Load Management | Autonomous Frequency Response | Capacity Market Dispatch | Traditional Frequency Regulation | Spinning Reserve | Dynamic Frequency Regulation | Autonomous Distribution Voltage Response | Wholesale Market Price Response |
|:------------------------------------:|:--------------------:|:-----------------------------:|:------------------------:|:--------------------------------:|:----------------:|:----------------------------:|:----------------------------------------:|:-------------------------------:|
|           **Water Heaters**          |       &#x2611;       |            &#x2611;           |         &#x2612;         |             &#x2611;             |     &#x2611;     |           &#x2611;           |                 &#x2611;                 |          *Needs update*         |
|           **PV Inverters**           |   *Trivial result*   |            &#x2611;           |         &#x2612;         |             &#x2611;             | *Trivial result* |           &#x2611;           |                 &#x2611;                 |         *Trivial result*        |
|         **Battery Inverters**        |    *Needs update*    |         *Needs update*        |         &#x2612;         |          *Needs update*          |  *Needs update*  |        *Needs update*        |              *Needs update*              |          *Needs update*         |
|         **Electric Vehicles**        |       &#x2611;       |            &#x2611;           |         &#x2612;         |             &#x2611;             |     &#x2611;     |           &#x2611;           |                 &#x2611;                 |             &#x2611;            |
|            **Fuel Cells**            |       &#x2611;       |            &#x2612;           |         &#x2612;         |             &#x2611;             |     &#x2611;     |           &#x2611;           |                 &#x2612;                 |             &#x2612;            |
|           **Electrolyzers**          |       &#x2611;       |            &#x2611;           |         &#x2612;         |             &#x2611;             |     &#x2611;     |           &#x2611;           |                 &#x2611;                 |             &#x2611;            |
|         **Air Conditioners**         |       &#x2611;       |            &#x2612;           |         &#x2612;         |             &#x2611;             |     &#x2611;     |           &#x2611;           |                 &#x2612;                 |             &#x2612;            |
| **Commercial Refrigeration Systems** |       &#x2611;       |            &#x2612;           |         &#x2612;         |             &#x2611;             |     &#x2611;     |           &#x2611;           |                 &#x2612;                 |             &#x2612;            |


## List of initial contributors and corresponding contacts

### - Integrators and software support
1. [Hung Ngo](https://github.com/hlngo) (PNNL)
2. [Ebony Mayhorn](https://github.com/emayhorn) (PNNL)
3. [David Winiarski](https://github.com/DavidWiniarski-pnnl) (PNNL)
4. [Hayden Reeve](https://github.com/Hayden-Reeve) (PNNL) 

### - Grid services
1. [Peak Load Management](src/services/peak_managment_service): [Ebony Mayhorn](https://github.com/emayhorn) (PNNL)
2. [Autonomous Frequency Response (Artificial Inertia)](src/services/artificial_inertia_service): [Yuan Liu](https://github.com/yliu250) (PNNL)
3. Capacity Market Dispatch: [Jingjing Liu](https://github.com/jingjingliu2018) (LBNL)
4. [Traditional Frequency Regulation](src/services/reg_service): [Jingjing Liu](https://github.com/jingjingliu2018) (LBNL) 
5. [Spinning Reserve](src/services/reg_service): [Jingjing Liu](https://github.com/jingjingliu2018) (LBNL) & [Peter Schwartz](https://github.com/rhosbach) (LBNL) 
6. [Dynamic Frequency Regulation](src/services/reg_service): [Jingjing Liu](https://github.com/jingjingliu2018 ) (LBNL) 
7. [Autonomous Distribution Voltage Response](src/services/distribution_voltage_regulation): [Rasel Mahmud](https://github.com/raselmahmud02) (NREL) 
8. [Wholesale Market Price Response](src/services/energy_market_service): [Tom Edmunds](https://github.com/TomEdmunds) (LLNL)  & [Can Huang](https://github.com/can7huang) (LLNL)

### - DERs
1. [Water Heaters](src/fleets/water_heater_fleet): [Jeff Maguire](https://github.com/jmaguire1) (NREL)
2. [PV Inverters](src/fleets/PV): [Rasel Mahmud](https://github.com/raselmahmud02) (NREL)
3. [Battery Inverters](src/fleets/battery_inverter_fleet): [David Rosewater](https://github.com/DavidRosewater) (SNL)
4. [Electric Vehicles](src/fleets/electric_vehicles_fleet): [Alejandro Fernandez Canosa](https://github.com/afernandezcanosa) (ANL) & Michael Duoba (ANL)
5. [Fuel Cells](src/fleets/fuel_cell_fleet): [Julian Osorio-Ramirez](https://github.com/xtrememenace) (INL) & [Rahul Kadavil](https://github.com/rkadavil) (INL)
6. [Electrolyzers](src/fleets/electrolyzer_fleet): [Julian Osorio-Ramirez](https://github.com/xtrememenace) (INL) & [Rahul Kadavil](https://github.com/rkadavil) (INL)
7. [Air Conditioners](src/fleets/HVAC_fleet): [Jin Dong](https://github.com/ORNLJD) (ORNL)
8. [Commercial Refrigeration Systems](src/fleets/Refridge_fleet): [Jin Dong](https://github.com/ORNLJD) (ORNL)

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
- Install Python3.6 or higher
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


# How to update your local repository before creating a new pull request
- Recall that you first fork the code from the project repository (let's call it A: https://github.com/GMLC-1-4-2/battery_interface). That creates ONE repository copy for yourself and the copy resides on Github cloud (let's call it B). Next, you clone B to your local computer, thus, creates another repository copy (let's call it C). 
- As other people's pull request got merged in A, both your github (B) and your local copy (C) become obsolete. So before you start working or making a new pull request, you need to update both B and C. 
- Follow steps below to update B and C:
    - Add the remote, call it "upstream": 
    ```sh
    $ cd battery_interface
    $ git remote add upstream https://github.com/GMLC-1-4-2/battery_interface.git
    ```
    - Fetch all the branches of that remote into remote-tracking branches, such as upstream/master: 
    ```sh
    git fetch upstream
    ``` 
    - Make sure that you're on your master branch: 
    ```sh
    git checkout master
    ```
    - Rewrite your master branch so that any commits of yours that aren't already in upstream/master are replayed on top of that other branch (update C): 
    ```sh
    git rebase upstream/master
    ```
    - Force the push in order to push it to your own forked repository on GitHub (update B): 
    ```sh
    git push -f origin master
    ```
    - Go to your github page and create a new pull request as usual
(Ref: https://stackoverflow.com/a/7244456/858931)

Notes: If you don't want to use command line (CLI), I suggest to use Sourcetree, which can basically do the same thing.


# How to test a pull request
- Download GIT if you don't have it from https://git-scm.com/downloads
- Create a new folder "battery_interface" for the code
- Go to command prompt (on Windows) or terminal (Unix/Linux/Mac)
- Change directory to the folder created above
- Clone to your local: git clone https://github.com/GMLC-1-4-2/battery_interface.git
- Check out a new branch: git checkout -b **your_new_branch_name**
- Pull the pull request to the branch created above: git pull origin pull/**the_PR_id_from_github**/head
- You should see the new service or device in the project folder


## License
battery_interface is released under the [MIT license](LICENSE). 

<img src="http://acep.uaf.edu/media/244211/gmlc-logo-2-203x300.png" width="225"> </img> <img src="https://cdn-images-1.medium.com/max/1600/1*C87EjxGeMPrkTuVRVWVg4w.png" width="225"></img>


