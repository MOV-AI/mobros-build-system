![image](https://user-images.githubusercontent.com/84147256/138106940-dbe34e71-7c07-4912-a418-e549f7892ecc.png)

# mobros - Movai Object Builder for ROS
Python framework to enable building and packaging of MOV.AI ROS components.



**main branch:**

[![Deploy - On branch main/release Push](https://github.com/MOV-AI/mobros-build-system/actions/workflows/DeployOnMergeMain.yml/badge.svg)](https://github.com/MOV-AI/mobros-build-system/actions/workflows/DeployOnMergeMain.yml)

# Table of Contents
1. [Installation](#install)
2. [Getting started](#getting-started)
3. [How to use](#how-to-use)
    1. [Build command](#cmd-build)
    2. [Pack command](#cmd-pack)
    3. [Publish command](#cmd-publish)
    4. [Install command](#cmd-install)
        1. [Conflict reporting](#cmd-install-conflict-report)
        2. [Conflict handling](#cmd-install-conflict-handling)
    6. [install build dependencies](#cmd-install-build-deps)
    7. [Rosdep Dependency rules](#rosdep-dep-rules)
4. [Commands in depth](#system-detail)
    1. [Building](#system-detail-build)
        1. [Rosdep](#system-detail-build-rosdep)
        2. [Ros Meta-Packages](#system-detail-build-ros-metapkg)
    2. [Packaging](#system-detail-pkging)
        1. [Movai metadata injection](#system-detail-pkging-meta-injection)
    3. [Installing](#system-detail-installing)


## How to install mobros <a id="install"/>
Simply execute the following:
```
python3 -m pip install -i https://artifacts.cloud.mov.ai/repository/pypi-edge/simple --extra-index-url https://pypi.org/simple mobros
```

**Warning:** If you see a warning that the installation folder is not on path simply add it to the PATH env var. 

## Get Started - Run locally <a id="getting-started"/>

In your project copy and execute the following in your terminal:

```
wget -qO - https://movai-scripts.s3.amazonaws.com/ros-build2.bash | bash
```

## How to use mobros <a id="how-to-use"/>
To use, simply install the mobros python package, and use as following:

```
mobros <command> <args>
```


*command* can take following values:

- *build*: to build your ROS workspace.    
- *pack*: to generate debian packages based on the configuration found in all package.xml.
- *install*: to install the inputed packages and evaluate conflicts in their dependency tree.
- *install-build-dependencies*: to install build dependencies of the ros workspace. 

### Mobros command: install-build-dependencies <a id="cmd-install-build-deps"/>

`Requires escalated privileges`

Example of usage:
```
mobros install-build-dependencies
```
This command to replaces and completes `rosdep install`.

Just because apt is unable to deal with complex dependency trees on packages installations, and so does rosdep (which relies on apt), `mobros install-build-dependencies` is enhancing the research algorithm on dependent packages list.
Also `rosdep` is unable to tell `apt` which version of the dependencies mentioned in the `package.xml` should be installed. This command evaluates the `package.xml` available in the ROS workspace and after using `rosdep resolver` to translate the rosdep keys, it forwards internally the call to `mobros install` with the list of the dependencies and their versions.

### Usage: Rosdep Dependencies <a id="rosdep-dep-rules"/>

This rules are specified in the package.xml of your ros package.

You can have two type of dependencies specified:
- Build dependencies (build_depend): Dependencies installed before the compilation.
- Runtime dependencies (exec_depend): Dependencies that will be set in your package as install time dependencies of you package.
To specify a dependency for both use <depend>.

The dependencies version rules go as follows:

- version_eq="VERSION" (optional): The dependency to the package is restricted to a version equal than the stated version number.
- version_lte/version_lt="VERSION" (optional): The dependency to the package is restricted to versions less or equal than the stated version number.
- version_gte/version_gt="VERSION" (optional): The dependency to the package is restricted to versions greater or equal than the stated version number.

Keep in mind that mobros will consider a candidate the top version within the specified rules.

For more details, check the following link: https://ros.org/reps/rep-0149.html#build-depend-multiple

### Mobros command: build <a id="cmd-build"/>

Example of usage:
```
mobros build
```

mobros build will install the requirements defined in your ROS component's package.xml and execute a catkin build in the working directory where you are executing mobros.

### Mobros command: pack <a id="cmd-pack"/>

Example of usage:
```
mobros pack --workspace=/opt/mov.ai/user/cache/ros/src
```

mobros pack will drilldown on your workspace looking for package.xmls. For each package.xml it will generate a ros package (.deb). 
If the ROS component has a `metadata` folder close by, it will be included in the debian package.
Then, on installation, the `metadata` will be automatically imported in MOV.AI database

Generated artifacts:
- Generates a folder in the root of the repository called "packages" with all the generated .deb packages.

### Mobros command: publish <a id="cmd-publish"/>

Example of usage:
```
mobros publish
```

mobros publish is used by the CI systems to patch the rosdep source file with the new generated packages. It uses the yaml file generated by the mobros pack, and sends it to the rosdep patcher service.

**Note:** This command is protected by aws credentials, meaning it's usage is limited to CI systems. For edge cases contact the Devops team for the following credentials.
Required environment variables:
 - AWS_DEFAULT_REGION
 - AWS_ACCESS_KEY_ID
 - AWS_SECRET_ACCESS_KEY


### Mobros command: install <a id="cmd-install"/>

`Requires escalated privileges`

Example of usage:
```
mobros install --pkg_list package_1=0.0.0-0 package_2 package_3=1.1.0-4
```

mobros install is used to install complex dependency trees of debian packages. Before installing packages, mobros scans the dependency of the requested packages, calculates candidates for installation and in the case of version conflicts, it produces reports for the user to make decisions.

Generated artifacts:
- Generates a file called "tree.mobtree" where the command was executed, with a resume'd dependency tree of what the packages the user requested.

#### Conflict Reporting <a id="cmd-install-conflict-report"/>

![image](https://user-images.githubusercontent.com/84720623/231483118-44587cbf-3e3f-46fe-9f9c-c1a5329ed1a9.png)

Mobros analyses the dependency tree, and takes in consideration the packages that are installed. The purpose is to have a cautious upgrade of the environment packages, reducing possible impact to a minimum.
To further troubleshoot where this clash is coming from, it's sugested to analyze the tree.mobtree file.

#### Conflict Handling <a id="cmd-install-conflict-handling"/>

Now that you are facing a conflict in the dependency tree, you need to take a decision and provide it to mobros.
To understand how to solve you must first understand what mobros expects from the inputs he receives:
- Package with a version (package_name=package_version): Mobros assumes that the user really wants this specific version, upgrading/downgrading it if it's installed. Version has to be the complete x.y.z-b version. No wildcards or expressions suported.
- Package without a version: Mobros considers the installation of the latest version available of the package.

Knowing this, if you find yourself in conflicts throughout the tree between the packages, or between what is installed and the dependency rules, you can add your decisions into the inputs mobros receives.  Mobros will adapt the dependency tree based on the inputs you give it. 


## Commands in depth <a id="system-detail"/>

### Build <a id="system-detail-build"/>

Mobros build simply userspace setup and calls to **rosdep** and **catkin** tools.

First it calls rosdep for him to walkthrough the userspace and install all mentioned projects in the package.xml's.
After all dependencies are installed it moves to the catkin build as you guys are used to.

#### Rosdep <a id="system-detail-build-rosdep"/>

Rosdep is a tool to install ros dependencies. It achieves his goal through the following:

![Screenshot from 2021-11-19 09-59-05](https://user-images.githubusercontent.com/84720623/142603735-068d1410-1eb0-4c77-b6bd-521f08b5ebd4.png)

You can manually check the result of the translation by executing:
```
rosdep resolve <name_of_dependency>
```

#### Ros Metapackages <a id="system-detail-build-ros-metapkg"/>

Another important thing to take in consideration is that, in a project that has a vertical structure, you need to define ros metapackages through the layers for the rosdep to be able to "crawl through" and find all package dependencies it needs to install.
Metapackages, are empty ros packages that points to all other packages next to it. For instance:

![Screenshot from 2021-11-19 16-53-59](https://user-images.githubusercontent.com/84720623/142661573-f6f006f6-cc36-46d5-ab36-0822b5435e60.png)

The package.xml must contain the metapackage attribute:

```
  <export>
    <metapackage/>
  </export>
```


Good example of a ros project, that contains a vertical arquitecture:
https://github.com/uwrobotics/uwrt_mars_rover/tree/49afe9d20655aa8f3ccd6bf2e69fef878a9eef8f



### Packaging <a id="system-detail-pkging"/>

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

#### movai metadata injection <a id="system-detail-pkging-meta-injection"/>

The injection takes in consideration, the relation of the metadata content and the current project being packaged, like detailed in the following diagram:

![Screenshot from 2021-11-19 11-32-25](https://user-images.githubusercontent.com/84720623/142616077-96e4110b-7b02-421c-90e4-2da1e8e14400.png)

If you followed the right structure, during mobros packaging you will see the following log:

![Screenshot from 2021-11-19 11-42-37](https://user-images.githubusercontent.com/84720623/142617267-01fee218-eb5c-4017-9f7e-57c4067c78af.png)


### Installing packages <a id="system-detail-installing"/>

Motivation: As ros component packaging is debian, it has the necessities of dependency relationing and dependency treeing as a normal programming language, like mentioning a certain version, even if new versions are available. APT (debian's package manager) has the purpose of keeping operating system packages updated, with the intent of installing latest versions possible, preventing the capability of multi-release lines of a component, or frozen dependencies between ros components.

Mobros fullfills this need by calculating the dependency tree of the inputed packages, before giving an ordered list of packages with their candidate versions to apt for it to install them.

Mobros already does some automatic conflict handling.
The current automatic conflict resolutions done are:
-  if the dependency conflict is with an installed version, and their difference is simply in the build identifier (4 digit of the deb package version), it ignores the installed version. The rationale is that build versions are considered security/bugfixes.

