from setuptools import setup, find_packages

setup(
    name="scarab-sim",
    version="1.0.0",
    description="A simulation framework for entity-based, time-stepped simulations.",
    author="Bill Back",
    author_email="billback@mac.com",
    url="https://github.com/billdback/scarab",
    packages=find_packages(),
    install_requires=[
        "aioconsole>=0.8.0",
        "iniconfig>=2.0.0",
        "numpy>=2.1.1",
        "packaging>=24.1",
        "pluggy>=1.5.0",
        "pytest>=8.3.2",
        "setuptools>=74.1.2",
        "sortedcontainers>=2.4.0",
        "toml>=0.10.2",
        "websockets>=13.0.1",
    ],
    python_requires=">=3.7",
)
