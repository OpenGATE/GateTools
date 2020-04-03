**Tools for [GATE](https://github.com/OpenGATE/Gate/) simulations.**
[![Build Status](https://travis-ci.org/OpenGATE/GateTools.svg?branch=master)](https://travis-ci.org/OpenGATE/GateTools)

Install with : `pip install gatetools`

Example of usage:
```
gt_gate_info
gt_image_convert -i input.dcm -o output.mhd
gt_image_convert -i input.mhd -o output_float.mhd -p float
gt_image_arithm -i *.mhd -o output.mhd -O sum
gt_gamma_index dose.mhd gate-DoseToWater.mhd -o gamma.mhd --dd 2 --dta 2.5 -u "%" -T 0.2
```

Use the flag `-h` to get print the help of each tool. Here is the current list of command line tools.

| Tool                          | Comment                                                   |
| -------------                 | -------------                                             |
| `gt_dicom_rt_pbs2gate`        | Convert Dicom RT proton plan for Gate                     |
| `gt_dicom_rt_struct_to_image` | Turn Dicom RT Struct contours into mask image             |
| `gt_gamma_index`              | Compute gamma index between images                        |
| `gt_gate_info`                | Display info about current Gate/G4 version                |
| `gt_image_arithm`             | Pixel- or voxel-wise arithmetic operations                |
| `gt_image_convert`            | Convert image file format (**dicom**, mhd, hdr, nii ... ) |
| `gt_image_crop`               | Crop an image                                             |
| `gt_image_uncertainty`        | Compute statistical uncertainty                           |
| `gt_affine_transform`         | Resample (resize, rotate) an image                        |
| `gt_phsp_convert`             | Convert a phase space file from root to npy               |
| `gt_phsp_info`                | Display information about a phase space file              |
| `gt_phsp_merge`               | Merge two phase space files (output in npy only)          |
| `gt_phps_peaks`               | Try to detect photopeaks (experimental)                   |
| `gt_phsp_plot`                | Plot marginal distributions form a phase space file       |

All tools are also available to be use within your own Python script with, for example:
```
import gatetools as gt
gt.image_convert(inputImage, pixeltype)
```

Tests: run
```
python -m unittest gatetools -v
python -m unittest gatetools.phsp -v
```

Classes and function documentation. Use the following command to open a browser for documentation (it is still not very convenient ; will be improved later).
```
pydoc -b
```

For developers, please have a look at the [readme_dev.md](readme_dev.md) file.
