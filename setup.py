import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="MovaiRosBuildSystem",
    version="0.0.1",
    author="DevOps team",
    author_email="duarte@mov.ai",
    description="Framework to build, raise and package ros and ros movai packages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MOV-AI/movai-ros-build-system",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        'requests==2.24.0'
    ]
)