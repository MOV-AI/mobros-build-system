"""Module that contains utilitary functions to deal with apt releated operations"""
import sys
from mobros.utils.version_utils import order_dpkg_versions
import mobros.utils.logger as logging
from mobros.utils.utilitary import execute_shell_command
from mobros.constants import OPERATION_TRANSLATION_TABLE
from mobros.types.apt_cache_singleton import AptCache

def is_virtual_package(deb_name):
    cache = AptCache().get_cache()
    return cache.is_virtual_package(deb_name) 

def inspect_package(deb_name, deb_version):
    cache = AptCache().get_cache()


    package_dependencies={}
    package=cache.get(deb_name)
    if package is not None:
        if deb_version == "":
            deb_version = get_package_avaiable_versions(deb_name)[0]

        specific_pkg_version =package.versions.get(deb_version)

        for dependency in specific_pkg_version.dependencies:
            dep = dependency[0]
#            for dep in dependency.or_dependencies:
            if dep.rawtype == "Depends":
                if cache.is_virtual_package(dep.name):
                    logging.debug("Dependency "+dep.name+" is a virtual package. Skipping it")
                    continue

                if dep.name not in package_dependencies:
                    package_dependencies[dep.name] = []
                
                package_dependencies[dep.name].append(
                    {
                        "operator": OPERATION_TRANSLATION_TABLE[str(dep.relation)],
                        "version": dep.version,
                        "from": deb_name + "=" + deb_version
                    }
                )

        # --------------------------------------
    
    else:
        logging.error("Package " + deb_name + " not found in apt cache.")
        logging.error("Tip: Check if mobros was able to update your apt cache (apt update)! Either run mobros with sudo or execute 'apt update' beforehand")
        sys.exit(1)    
    
    #     for dependency in specific_pkg_version.dependencies:
    #         print(dependency.or_dependencies)
    #         for dep in dependency.or_dependencies:
    #             print(dep)
    #             if dep.rawtype == "Depends":
    #                 if is_virtual_package(dep.name):
    #                     logging.warning("Dependency "+dep.name+" is a virtual package. Skipping it")
    #                     continue
    #                 if dep.name not in package_dependencies:
    #                     package_dependencies[dep.name] = []
                    
    #                 package_dependencies[dep.name].append(
    #                     {
    #                         "operator": OPERATION_TRANSLATION_TABLE[str(dep.relation)],
    #                         "version": dep.version,
    #                         "from": deb_name + "=" + deb_version
    #                     }
    #                 )
    # end = time.time()
    # logging.info("[APT_UTILS -  inspect package] i took "+str(end - start))

    # -------------------------------





    # for package in cache:
    #     if package is not None:
    #         specific_pkg_version =package.versions.get(deb_version)
            

    #         for dependency in specific_pkg_version.dependencies:
    #             for dep in dependency.or_dependencies:
    #                 if dep.rawtype == "Depends":
    #                     if is_virtual_package(dep.name):
    #                         logging.warning("Dependency "+dep.name+" is a virtual package. Skipping it")
    #                         continue
    #                     if dep.name not in package_dependencies:
    #                         package_dependencies[dep.name] = []
                        
    #                     package_dependencies[dep.name].append(
    #                         {
    #                          "operator": OPERATION_TRANSLATION_TABLE[str(dep.relation)],
    #                          "version": dep.version,
    #                          "from": deb_name + "=" + deb_version
    #                         }
    #                     )

    return package_dependencies

def is_package_already_installed(deb_name, version=None):
    cache = AptCache().get_cache()
    package=cache.get(deb_name)
    if version:
        return package.is_installed and package.installed.version==version
    else:
        return package.is_installed
    

def get_package_installed_version(deb_name):
    cache = AptCache().get_cache()
    package=cache.get(deb_name)
    if package.is_installed:
        return package.installed.version
    return None

def get_package_avaiable_versions(deb_name):
    """function that gathers all installed .deb packages in an environment from a specific repository"""
    cache = AptCache().get_cache()
    package=cache.get(deb_name)

    if package is not None:
        return clean_apt_versions(package.versions)
    
    return []


# def install_package(deb_name, version):
# cache = apt.Cache()
# cache.update()
# cache.open()
# pkg = cache[deb_name]

# candidate = pkg.versions.get(version)
# pkg.candidate = candidate
# pkg.mark_install()
# cache.commit()


def install_package(deb_name, version=None, simulate=False):
    """Function to install a debian package name

    Args:
        deb_name (str): debian package name to be installed
        version (str, optional): version to be installed. Defaults to None.
        simulate (bool, optional): defines if install should be printed only or executed. Defaults to False.
    """
    candidate = deb_name
    if version:
        candidate += "=" + version
    logging.info("Installing " + candidate)
    if not simulate:
        execute_shell_command(
            ["sudo", "apt-get", "install", "-y", "--allow-downgrades", candidate],
            stop_on_error=True,
            log_output=True
        )


def clean_apt_versions(version_list):
    """Function that orders and strips the versions from the list returned by apt cache.

    Args:
        version_list (list): list of versions from the apt cache in the cache format

    Returns:
        list: ordered list of versions from the apt cache
    """
    clean_versions = []
    for version in version_list:
        clean_versions.append(str(version).split("=")[1])

    order_dpkg_versions(clean_versions, reverse=True)
    return clean_versions
