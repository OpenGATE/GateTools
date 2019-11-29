import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gatetools",
    version="0.8.2",
    author="OpenGate collaboration",
    author_email="david.sarrut@creatis.insa-lyon.fr",
    description="Python tools for GATE, see https://github.com/OpenGATE/Gate",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenGATE/GateTools",
    packages=['gatetools'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'uproot',
        'matplotlib',
        'click',
        'numpy',
        'pydicom',
        'tqdm',
        'colored',
        'itk>=5',
        'uproot',
    ],
    scripts=[
        'bin/gt_gate_info',
        
        'bin/gt_image_uncertainty',
        'bin/gt_image_arithm',
        'bin/gt_image_crop',
        'bin/gt_image_convert',
        'bin/gt_gamma_index',

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
# 2 - commit, tag
# 3 - setup/twine (see below)


# pip uninstall gatetools
# python3 setup.py sdist bdist_wheel
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# test with
# pip3 install --index-url https://test.pypi.org/simple/ gatetools
