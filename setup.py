import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mobros",
    version="1.0.1-6",
    author="DevOps team",
    author_email="devops@mov.ai",
    description="Movai Object Builder for Ros, The framework to build, raise and package ros and ros movai packages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MOV-AI/movai-ros-build-system",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    install_requires=["boto3", "ruamel.yaml"],
    entry_points={"console_scripts": ["mobros = mobros.handler:handle"]},
)
