## Turbidity Monitoring using Computer Vision

Experimental Setup

A Raspberry Pi 4 Desktop was connected to a web camera (Microsoft LifeCam HD-3000) and was used to run the computer vision script. A reference sample of the reaction solvent (1 mL, CHCl3) in a 2 mL vial was positioned within the 3D printed 2-vial holder found in (`3D-printing`). Each reaction mixture vial from the `48-well reaction plate` was transferred into the adjacted vial position next to the reference.  

Measurement

- The Python script `detect_turbidity_solubility.py` was used to execute the script.
- A normalisation region was selected of an area that was not the reference or reaction mixture vials. 
- A region of interest (ROI) was selected for each the reference and reaction vial. 
- Each selection was written to `vision_selection.json`. This was selected as a path for all proceeding measurements of the reaction plate to accelerate data curation.
- The script look a measurement for turbidity of the reference vial in the ROI and then monitored the ROI in the reaction mixture vial.
- The script monitored the sample for a maximum period of two minutes and terminated when an outcome of 'dissolved' or 'stable' (equilibrium reached but not dissolved)

Output

A new folder was written for each measurement as `solubility_study_X` where X was the formulation number (position in plate) 
Each folder contained:

- a folder of images taken `solubility_study_X_images`
- a video of the monitoring `solubility_study_X_turbidity_video`
- an image of the vision selections `vision_selection` and the corresponding vision selection json `vision_selection.json`
- a json file of the measured turbidity, including the reference turbidity, with timestamps `turbidity_data.json`
- a csv file with the timestamp of measurement and the measured turbidity `turbidity_data.csv`
