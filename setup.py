from setuptools import setup, find_packages

setup(
    name="credstack",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-sqlalchemy",
        "pyyaml",
        "requests",
    ],
    author="WADELABS",
    description="A privacy-first credit utilization optimizer.",
    license="MIT",
)
