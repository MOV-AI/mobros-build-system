
class PackageMeta(type):
    """A Package metaclass that will be used for the dependency evaluation
    """
    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass):
        return (hasattr(subclass, 'get_dependencies') and 
                callable(subclass.get_dependencies) and 
                hasattr(subclass, 'get_name') and 
                callable(subclass.get_name))


class PackageInterface(metaclass=PackageMeta):
    """This interface is used for concrete package classes to inherit from. """
    pass