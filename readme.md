
The **gatetools** gather Python script useful for [GATE](https://github.com/OpenGATE/Gate/) simulation. 

To install : `pip install -e .` (SOON !)

Current list of command line tools:

| Tool  | Comment |
| ------------- | ------------- |
| `gate_info`  | Display info about current Gate/G4 version  |
| `gate_image_arithm`  | TODO  |
| `gate_image_convert` | Convert image file format (mhd, hdr, nfty ... not DICOM) |
| `gate_image_uncertainty`| Compute statistical uncertainty|
| `gate_gamma_index`| Compute gamma index between images|

Tests: run `python –m unittest2 gatetools` or `unit2 gatetools` (according to your python installation)

Dependencies:
- click: https://click.palletsprojects.com
- uproot: https://github.com/scikit-hep/uproot
- pydicom: https://pydicom.github.io/
- tqdm: https://github.com/tqdm/tqdm
- colored: https://gitlab.com/dslackw/colored
- itk: https://itk.org/
- unittest2: https://pypi.org/project/unittest2/




