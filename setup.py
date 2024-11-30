from setuptools import setup, find_packages

setup(
    name="mta_api",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[line.strip() for line in open("requirements.txt")],
)
