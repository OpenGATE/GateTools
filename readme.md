
Install with : `pip install gatetools`

This module provides Python tools useful for [GATE](https://github.com/OpenGATE/Gate/) simulation. 

Current list of command line tools. Use the flag `-h` to get print the help of each tool.

| Tool  | Comment |
| ------------- | ------------- |
| `gate_info`  | Display info about current Gate/G4 version  |
| `gate_image_arithm`  | Pixel- or voxel-wise arithmetic operations |
| `gate_image_convert` | Convert image file format (dicom, mhd, hdr, nfty ... ) |
| `gate_image_uncertainty`| Compute statistical uncertainty|
| `gate_gamma_index`| Compute gamma index between images|

All tools are also available to be use within your own Python script with, for example: 
```
import gatetools as gt
gt.image_convert(inputImage, pixeltype)
```

Tests: run `python -m unittest gatetools`

When developing, install with: `pip install -e .`

Dependencies:
- click: https://click.palletsprojects.com
- uproot: https://github.com/scikit-hep/uproot
- pydicom: https://pydicom.github.io/
- tqdm: https://github.com/tqdm/tqdm
- colored: https://gitlab.com/dslackw/colored
- itk: https://itk.org/





