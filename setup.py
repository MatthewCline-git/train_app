from setuptools import setup, find_packages

setup(
    name="mta_api",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "mta_api": ["data/*.csv"]
    },
    install_requires=[line.strip() for line in open("requirements.txt")],
)
