**(Hopefully) useful tools for [GATE](https://github.com/OpenGATE/Gate/) simulations.**

**STILL WORK IN PROGRESS : will be released before end 2019**

Install with : `pip install gatetools` 

Example of usage: 
```
gt_image_convert -i input.dcm -o output.mhd
gt_image_convert -i input.mhd -o output_float.mhd -p float
gt_image_arithm -i *.mhd -o output.mhd -O sum
gt_gamma_index data/tps_dose.mhd result.XYZ/gate-DoseToWater.mhd -o gamma.mhd --dd 2 --dta 2.5 -u "%" -T 0.2
```

Current list of command line tools. Use the flag `-h` to get print the help of each tool.

| Tool  | Comment |
| ------------- | ------------- |
| `gt_gate_info`  | Display info about current Gate/G4 version  |
| `gt_image_arithm`  | Pixel- or voxel-wise arithmetic operations |
| `gt_image_convert` | Convert image file format (**dicom**, mhd, hdr, nfty ... ) |
| `gt_image_uncertainty`| Compute statistical uncertainty|
| `gt_gamma_index`| Compute gamma index between images|
| `gt_phsp_info` | Display information about a phase space file | 
| `gt_phsp_convert` | Convert a phase space file from root to npy| 
| `gt_phsp_merge` | Merge two phase space files (output in npy only) | 
| `gt_phsp_plot` | Plot marginal distributions form a phase space file | 
| `gt_phps_peaks`| Try to detect photopeaks (experimental) | 

All tools are also available to be use within your own Python script with, for example: 
```
import gatetools as gt
gt.image_convert(inputImage, pixeltype)
```

Tests: run `python -m unittest gatetools -v`
           `python -m unittest gatetools.phsp -v`

When developing, install with: `pip install -e .`

Dependencies:
- click: https://click.palletsprojects.com
- uproot: https://github.com/scikit-hep/uproot
- pydicom: https://pydicom.github.io/
- tqdm: https://github.com/tqdm/tqdm
- colored: https://gitlab.com/dslackw/colored
- itk: https://itk.org/
