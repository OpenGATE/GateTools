[![Build status](https://github.com/OpenGATE/GateTools/actions/workflows/main.yml/badge.svg)](https://github.com/OpenGATE/GateTools/actions/workflows/main.yml)
[![PyPI](https://img.shields.io/pypi/v/gatetools)](https://pypi.org/project/gatetools/)

**Tools for [GATE](https://github.com/OpenGATE/Gate/) simulations.**

Install with : `pip install gatetools`

Clone the repository with `git clone --recursive https://github.com/OpenGATE/GateTools.git`
(or `git submodule update --init` to update)
then `cd GateTools`, then `pip install -e .`

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
| `gt_affine_transform`         | Resample (resize, rotate) an image                        |
| `gt_dicom_info`               | Print tag values of a dicom file                          |
| `gt_dicom_rt_pbs2gate`        | Convert Dicom RT proton plan for Gate                     |
| `gt_dicom_rt_struct_to_image` | Turn Dicom RT Struct contours into mask image             |
| `gt_dvh`                      | Create Dose Volume Histogram                              |
| `gt_gamma_index`              | Compute gamma index between images                        |
| `gt_gate_info`                | Display info about current Gate/G4 version                |
| `gt_hausdorff`                | Compute Hausdorff distance                                |
| `gt_image_arithm`             | Pixel- or voxel-wise arithmetic operations                |
| `gt_image_convert`            | Convert image file format (**dicom**, mhd, hdr, nii ... ) |
| `gt_image_crop`               | Crop an image                                             |
| `gt_image_gauss`              | Blur an image using gaussian filter                       |
| `gt_image_resize`             | Resize an image                                           |
| `gt_image_statistics`         | Statistics of an image                                    |
| `gt_image_to_dicom_rt_struct` | Convert mask image to Dicom RTStruct                      |
| `gt_image_uncertainty`        | Compute statistical uncertainty                           |
| `gt_merge_root`               | Merge root files                                          |
| `gt_morpho_math`              | Compute morphological operation                           |
| `gt_phsp_convert`             | Convert a phase space file from root to npy               |
| `gt_phsp_info`                | Display information about a phase space file              |
| `gt_phsp_merge`               | Merge two phase space files (output in npy only)          |
| `gt_phps_peaks`               | Try to detect photopeaks (experimental)                   |
| `gt_phsp_plot`                | Plot marginal distributions form a phase space file       |
| `gt_write_dicom`              | Convert image (mhd, nii, ...) to dicom                    |

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
