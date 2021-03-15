import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ARBSMapDo", # Replace with your own username
    version="0.4.0",
    author="Eric 'Luux' Schölzel",
    author_email="luux-pypi@luux.dev",
    description="Advanced Ranked BeatSaber Map Downloader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Luux/ARBSMapDo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
)