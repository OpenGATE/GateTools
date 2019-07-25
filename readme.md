
The **gatetools** gather Python script useful for [GATE](https://github.com/OpenGATE/Gate/) simulation. 

To install : `pip install -e .` (TEMPORARY)
To install : `pip install gatetools` (SOON !)


Current list of command line tools. Use the flag `-h` to get print the help of each tool.

| Tool  | Comment |
| ------------- | ------------- |
| `gate_info`  | Display info about current Gate/G4 version  |
| `gate_image_arithm`  | Pixel- or voxel-wise arithmetic operations |
| `gate_image_convert` | Convert image file format (mhd, hdr, nfty ... not DICOM) |
| `gate_image_uncertainty`| Compute statistical uncertainty|
| `gate_gamma_index`| Compute gamma index between images|

Tests: run `python -m unittest gatetools`

Dependencies:
- click: https://click.palletsprojects.com
- uproot: https://github.com/scikit-hep/uproot
- pydicom: https://pydicom.github.io/
- tqdm: https://github.com/tqdm/tqdm
- colored: https://gitlab.com/dslackw/colored
- itk: https://itk.org/





