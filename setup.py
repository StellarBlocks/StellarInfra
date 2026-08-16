import setuptools

with open("./README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
  name="StellarInfra",
  version="0.0.9",
  author="Powerfulbean",
  author_email="powerfulbean@gmail.com",
  description="An python infrastructure of StellarBlocks's software",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/StellarBlocks/StellarInfra",
  packages=setuptools.find_packages(),
  classifiers=[
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
  ],
  install_requires=[
      "numpy",
      "scipy",
      "pandas",
      "mat73",
      "keyboard",
      "PyYAML"
  ],
)
