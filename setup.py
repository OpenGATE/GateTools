import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="phsp",
    version="0.0.1",
    author="David Sarrut",
    author_email="david.sarrut@creatis.insa-lyon.fr",
    description="Python tools for GATE phase-space (PHSP) management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dsarrut/phsp",
    package_dir={'':'src'},
    packages=setuptools.find_packages('phsp'),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'tqdm',
        'uproot',
      ],
    scripts=[
        'bin/phsp_convert',
        'bin/phsp_info',
        'bin/phsp_plot',
    ]
)
