"""setup module."""

import re
from pathlib import Path

from setuptools import find_packages, setup

name = "mse_home"

version = re.search(
    r"""(?x)
    __version__
    \s=\s
    \"
    (?P<number>.*)
    \"
    """,
    Path(f"{name}/__init__.py").read_text(),
)

setup(
    name=name,
    version=version["number"],
    url="https://cosmian.com",
    license="MIT",
    project_urls={
        "Documentation": "https://docs.cosmian.com",
        "Source": "https://github.com/Cosmian/mse-home-cli",
    },
    author="Cosmian Tech",
    author_email="tech@cosmian.com",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8.0",
    description="Python CLI for MicroService Encryption Home",
    packages=find_packages(),
    zip_safe=True,
    install_requires=[
        "cryptography>=41.0.1,<42.0.0",
        "docker>=6.0.1,<7.0.0",
        "intel-sgx-ra==2.0a11",
        "jinja2>=3.0,<3.1",
        "mse-cli-core==0.1a8",
        "mse-lib-crypto>=1.3,<1.4",
        "pydantic>=1.10.2,<2.0.0",
        "requests>=2.31.0,<3.0.0",
        "toml>=0.10.2,<0.11.0",
    ],
    entry_points={
        "console_scripts": ["msehome = mse_home.main:main"],
    },
    package_data={"mse_home": ["template/*", "template/**/*"]},
    tests_require=["pytest>=7.2.0,<7.3.0"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
