# Opentrons_Code
----------------
A repository containing code used to replicate reactions performed on the Opentron platform.



## Guide to Using Opentrons Code
--------------------------------

A typical Opentrons run can be conducted using three files: `move_commands.json`, `opentron_script.py`, and `substance_locations.json`.

In `substance_locations.json`, the locations of plate (1-9) and the well plate numbers are specified for each substance, in addition to the amount in each well and the substance name.
The amount value is specified so the Opentrons knows to move onto the next well with the same substance.

`move_commands.json` contains the commands to move the Opentrons to the specified locations. Each move must contain the following information:
- `substance`: The name of the substance to be moved.
- `amount`: The amount of the substance to be moved in µL.
- `plate`: The plate number to be moved to on the deck.
- `location`: The well location on the plate to be moved to. Mulptiple locations can be specified from the same plate.

Once these files are created, the Opentrons script can be run using the `opentron_script.py` file using the command `python opentron_script.py`.

It it highly recommended to run the script from the Opentrons app to ensure that the calibration is correct. The files `move_command.json` and `substance_locations.json` must be copied over to the Opentrons before executing the script from the Opentrons app and the variables `move_path` and `substance_path` in the `opentron_script.py` file must be changed to reflect the locations of the files.

Example files can be found in the `Example` folder.

## Opentrons Parameters
-----------------------

Parameters selected for the Opentrons were carefully chosen based on performing a benchmark aspirating and dispensing different volumes of solvent around the system.
For each new solvent system, a benchmark should be performed prior to running experiments to investigate the optimal parameter for each solvent system.
Otherwise, issues the users may face include pipette dripping and incorrect aspirate and dispensing amounts.

The main parameters to control the Opentrons, alongside their default values used, include:
- Gantry speed - the speed in which the robot moves. Default value: 100 mm/s. This should not exceed 400 mm/s, however, a slower speed will generally result in less dripping occuring.
- Plunger flow rates speed - controls the speed at which liquuids are aspirated and dispensed at. Default values: 40 uL/ for the 300 uL pipette, and 3.86 uL/s for the 20 uL pipette. Generally, a slower aspirate rate will ensure fewer air bubbles appear in the pipette and more accurate aspirating/dispensing occurs.
- Air gap - Aspirating an air gap of 15 uL has been found to reduce chance of the robot dripping in chlorinated solvent, and is included by default for each movement in the example script.
- Max aspiration volume - Controls the maximum amount aspirating in the pipette, not including the air gap. Default values: 220 uL for the 300 pipette to minimise the amount of dripping that occurs.

These parameters have been validated on chloroform, acetonitrile, and DMSO, but a optimal settings may not be translatable to different solvent systems.