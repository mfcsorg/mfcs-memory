"""
MFCS Memory - A smart conversation memory management system
"""

from setuptools import setup, find_packages

# Read version from __init__.py
with open("src/mfcs_memory/__init__.py", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            VERSION = line.split("=")[1].strip().strip('"')
            break

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mfcs-memory",
    version=VERSION,
    author="shideqin",
    author_email="shisdq@gmail.com",
    description="A smart conversation memory management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mfcsorg/mfcs-memory",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pymongo",
        "python-dotenv",
        "qdrant-client",
        "openai==1.86.0",
        "sentence-transformers"
    ],
) 