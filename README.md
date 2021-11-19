![image](https://user-images.githubusercontent.com/84147256/138106940-dbe34e71-7c07-4912-a418-e549f7892ecc.png)

# mobros - Movai Object Builder for ROS
Python framework to enable building and packaging of MOV.AI ROS components.

**main branch:**

[![Deploy - On branch main/release Push](https://github.com/MOV-AI/mobros-build-system/actions/workflows/DeployOnMergeMain.yml/badge.svg)](https://github.com/MOV-AI/mobros-build-system/actions/workflows/DeployOnMergeMain.yml)

## How to install mobros
Simply execute the following:
```
python3 -m pip install -i https://artifacts.cloud.mov.ai/repository/pypi-edge/simple --extra-index-url https://pypi.org/simple mobros
```

**Warning:** If you see a warning that the installation folder is not on path simply add it to the PATH env var. 


## How to use mobros
To use, simply install the mobros python package, and use as following:

```
mobros <command> <args>
```


*command* can take following values:

- *build*: to build your ROS workspace.    
- *pack*: to generate debian packages based on the configuration found in all package.xml.

### mobros command: build

Example of usage:
```
mobros build
```

mobros build will install the requirements defined in your ROS component's package.xml and execute a catkin build in the working directory where you are executing mobros.

### mobros command: pack

Example of usage:
```
mobros pack --workspace=/opt/mov.ai/user/cache/ros/src
```

mobros pack will drilldown on your workspace looking for package.xmls. For each package.xml it will generate a ros package (.deb). 
If the ROS component has a `metadata` folder close by, it will be included in the debian package.
Then, on installation, the `metadata` will be automatically imported in MOV.AI database

### mobros command: publish

Example of usage:
```
mobros publish
```

mobros publish is used by the CI systems to patch the rosdep source file with the new generated packages. It uses the yaml file generated by the mobros pack, and sends it to the rosdep patcher service.

**Note:** This command is protected by aws credentials, meaning its usage is limited to CI systems. For edge cases contact the Devops team for the following credentials.
Required environment variables:
 - AWS_DEFAULT_REGION
 - AWS_ACCESS_KEY_ID
 - AWS_SECRET_ACCESS_KEY



## Detailed System

### Build

Mobros build simply userspace setup and calls to **rosdep** and **catkin** tools.

First it calls rosdep for him to walkthrough the userspace and install all mentioned projects in the package.xml's.
After all dependencies are installed it moves to the catkin build as you guys are used to.

#### Rosdep 

Rosdep is a tool to install ros dependencies. It achieves his goal through the following:

![Screenshot from 2021-11-19 09-59-05](https://user-images.githubusercontent.com/84720623/142603735-068d1410-1eb0-4c77-b6bd-521f08b5ebd4.png)

You can manually check the result of the translation by executing:
```
rosdep resolve <name_of_dependency>
```

### Packaging

During the packaging the following is being achieved:

- Raising build identifier :
  - read package.xml version
  - add a forth digit for the build ID
  - bump this build ID
- Generation of the debian metadata :
  - automaticaly generates the debian folder based on the CMakelist.txt and package.xml
  - injects the MOV.AI metadata folder into the package
  - injects the install/uninstall methods of MOV.AI metadata into the platform
- Package the deb :
  - compile the sources in release mode (TODO: add debug option)
  - regroup the binaries and all identified artifacts in the package
  - TODO: signing, git changelogs, release notes

#### movai metadata injection

The injection takes in consideration, the relation of the metadata content and the current project being packaged, like detailed in the following diagram:

![Screenshot from 2021-11-19 11-32-25](https://user-images.githubusercontent.com/84720623/142616077-96e4110b-7b02-421c-90e4-2da1e8e14400.png)

If you followed the right structure, during mobros packaging you will see the following log:

![Screenshot from 2021-11-19 11-42-37](https://user-images.githubusercontent.com/84720623/142617267-01fee218-eb5c-4017-9f7e-57c4067c78af.png)


### Get Started - Run locally

In your project copy and execute the following in your terminal:

```
wget -qO - https://movai-scripts.s3.amazonaws.com/ros-build.bash | bash
```
