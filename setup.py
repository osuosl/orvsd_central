"""
ORVSD Central
"""
from setuptools import setup, find_packages

setup(
    name="orvsd-central",
    description="The central hub for ORVSD",
    long_description=open('README.txt').read(),
    version="0.0.1",
    url="https://orvsd.org",
    author="OSUOSL",
    author_email="support@osuosl.org",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'orvsd-central = orvsd_central.wsgi:app',
        ],
    },
)
