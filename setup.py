"""
ORVSD Central
"""
from setuptools import setup, find_packages

setup(
    name="orvsd-central",
    description="The central hub for ORVSD",
    long_description=open('README.txt').read(),
    version="0.1.0",
    url="https://orvsd.org",
    author="OSUOSL",
    author_email="support@osuosl.org",
    packages=find_packages(),
)
