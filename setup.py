import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="json-editor",
    version="0.00.01",
    author="Richard Brenick",
    author_email="RichardBrenick@gmail.com",
    description="qt tool template",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rBrenick/json-editor",
    packages=setuptools.find_packages(exclude=["tests"]),
    package_data={'': ['*.*']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)



