import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gatetools",
    version="0.0.1",
    author="OpenGate collaboration",
    author_email="david.sarrut@creatis.insa-lyon.fr",
    description="Tools for GATE ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.in2p3.fr/dsarrut/syd",
    packages=['gatetools'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'uproot',
        'pydicom',
        'tqdm',
        'colored',
        'itk',
        'SimpleITK'
      ],
    scripts=[
        'bin/gate_info',
        'bin/gate_image_uncertainty',
        ]
)
