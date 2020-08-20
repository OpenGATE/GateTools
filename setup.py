import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gatetools",
    version="0.9.7",
    author="OpenGate collaboration",
    author_email="david.sarrut@creatis.insa-lyon.fr",
    description="Python tools for GATE, see https://github.com/OpenGATE/Gate",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenGATE/GateTools",
    package_dir={ 'gatetools': 'gatetools',
                  'gatetools.phsp': 'gatetools/phsp'},
    packages=['gatetools', 'gatetools.phsp'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'matplotlib',
        'click',
        'numpy',
        'pydicom',
        'tqdm',
        'colored',
        'itk>=5.1.0',
        'uproot',
        'wget',
    ],
    scripts=[
        'bin/gt_gate_info',
        
        'bin/gt_image_uncertainty',
        'bin/gt_image_arithm',
        'bin/gt_image_crop',
        'bin/gt_image_convert',
        'bin/gt_image_statistics',
        'bin/gt_gamma_index',
        'bin/gt_affine_transform',
        'bin/gt_write_dicom',
        'bin/gt_dicom_info',
        'bin/gt_image_gauss',
        'bin/gt_image_resize',
        'bin/gt_dvh',

        'bin/gt_dicom_rt_struct_to_image',
        'bin/gt_dicom_rt_pbs2gate',
        
        'bin/gt_phsp_info',
        'bin/gt_phsp_convert',
        'bin/gt_phsp_merge',
        'bin/gt_phsp_plot',
        'bin/gt_phsp_peaks',
    ]
)


# -----------------------------------------------------------------------------
# Uploading the package on pypi

# Steps
# 1 - change version in setup.py file
# 2 - commit, tag. git push --tags
# 3 - setup: python3 setup.py sdist bdist_wheel
# 4 - twine: see below

# On TEST pypi: 
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# On REAL pyip
# twine upload  dist/*

# test with
# pip uninstall gatetools
# pip3 install --extra-index-url https://test.pypi.org/simple/ gatetools
# https://test.pypi.org/project/gatetools/
