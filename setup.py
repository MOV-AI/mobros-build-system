import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="movros-build-system",
    version='1.0.8-8-1-1',
    author="DevOps team",
    author_email="devops@mov.ai",
    description="Mov(ai) Ros, The framework to build, raise and package ros and ros movai packages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MOV-AI/movai-ros-build-system",
    packages=setuptools.find_packages(),
    include_package_data=True ,
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    install_requires=[],
     entry_points={
        'console_scripts': [
            'movros-build-system = MovaiRosBuildSystem.handler:handle'
        ]
    }

)