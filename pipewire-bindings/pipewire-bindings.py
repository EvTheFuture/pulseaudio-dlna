#!/usr/bin/python3
#

import ctypes as c
import enum
import signal
import sys
import threading

# TODO, FIXME
lib = c.CDLL("./libpipewire-bindings.so")

class spa_dict_item(c.Structure):
    pass

spa_dict_item._fields_ = [
        ("key", c.c_char_p),
        ("value", c.c_char_p)
    ]

class spa_dict(c.Structure):
    pass

spa_dict._fields_ = [
        ("flags", c.c_uint32),
        ("n_items", c.c_uint32),
        ("items", c.POINTER(spa_dict_item)),
    ]

class EventType(enum.Enum):
    ADDED = 0
    REMOVED = 1
    EXISTING = 2

class CoreStatus(enum.Enum):
    CORE_DONE = 0
    CORE_ERROR = 1

class PWObject():
    class Type(enum.Enum):
        Client            = enum.auto()
        ClientEndpoint    = enum.auto()
        ClientNode        = enum.auto()
        ClientSession     = enum.auto()
        Core              = enum.auto()
        Device            = enum.auto()
        Endpoint          = enum.auto()
        EndpointLink      = enum.auto()
        EndpointStream    = enum.auto()
        Factory           = enum.auto()
        Link              = enum.auto()
        Metadata          = enum.auto()
        Module            = enum.auto()
        Node              = enum.auto()
        Port              = enum.auto()
        Profiler          = enum.auto()
        Registry          = enum.auto()
        Session           = enum.auto()

    ports = {}
    connections = {}

    def __init__(self, object_id, type, properties):
        self.type = type

        self.id = object_id
        self.items = {}

        self.property_flags = properties.flags
        self.property_items = []

        for i in range(0, properties.n_items):
            k = str(properties.items[i].key, "UTF-8")
            v = str(properties.items[i].value, "UTF-8")

            self.items[k] = v

        if type == PWObject.Type.Node:
            print(f"Creating object: {object_id} -> {self.type}: {self.items}")

    def __str__(self):
        return f"{self.id}, {self.type} {self.items}"

    def __repr__(self):
        return self.__str__()

    def name(self):
        return str(self.id)


class Client(PWObject):
    def name(self):
        if "application.name" in self.items:
            return self.items["application.name"]

        return super().name()

class Node(PWObject):
    def name(self):
        if "node.name" in self.items:
            return self.items["node.name"]

        return super().name()

class Port(PWObject):
    def name(self):
        if "port.name" in self.items:
            return self.items["port.name"]

        return super().name()

class Link(PWObject):
    pass


def create_object(object_id, object_type, properties):
    type_str = str(object_type, 'UTF-8')
    type = PWObject.Type(PWObject.Type[type_str[19:]])

    if type is PWObject.Type.Client:
        return Client(object_id, type, properties)
    if type is PWObject.Type.Node:
        return Node(object_id, type, properties)
    if type is PWObject.Type.Port:
        return Port(object_id, type, properties)
    if type is PWObject.Type.Link:
        return Link(object_id, type, properties)

    return PWObject(object_id, type, properties)


# Dict with PWObjects. Object ID is the dict key
objects = {}

def connect_objects(objects, object):
    match object.type:
        case PWObject.Type.Port:
            if "node.id" in object.items:
                object_id = int(object.items["node.id"])
            elif "client.id" in object.items:
                object_id = int(object.items["client.id"])
            else:
                object_id = -1

            if object_id in objects:
                other_object = objects[object_id]
                other_object.ports[object.id] = object

#                print(f"===== Will connect port '{object.name()}' to '{other_object.name()}'...")

        case PWObject.Type.Link:
            for i in ("link.input.port", "link.output.port", "link.input.node", "link.output.node"):
                if i in object.items:
                    object_id = int(object.items[i])
                    if object_id in objects:
                        other_object = objects[object_id]
                        other_object.connections[object.id] = object

#                        print(f"===== Connected Link '{object.name()}' to '{other_object.name()}'...")



@c.CFUNCTYPE(None, c.c_int)
def core_callback(a):
    print(f"Core Callback: Msg Value: {CoreStatus(a)}");

@c.CFUNCTYPE(None, c.c_int, c.c_uint32, c.c_char_p, spa_dict)
def object_change_callback(et, object_id, object_type, spa_dict):

    event_type = EventType(et)

    if event_type == EventType.REMOVED:
        object = objects.pop(object_id, None)
        print(f"Removing: {object}")

    else:
        object = create_object(object_id, object_type, spa_dict)
        objects[object.id] = object

        object.name()
        connect_objects(objects, object)

#        print(f"Adding: {object}")
#        print(f"{event_type} Type: {str(object_type, 'utf-8')}, id: {object_id}, {spa_dict.flags}{concat}")

def signal_handler(signal, frame):
    print("Singal received...")
    print("Cleaning up...")
    lib.quit()
    sys.exit(0)


if __name__ == "__main__":
    # Install signal handler
    print("Installing singal handler")
    signal.signal(signal.SIGINT, signal_handler)

    lib.connect() 

    print("Initializing...");
    ret = lib.init("testing-client", core_callback, object_change_callback); 
 
    print(f"Pipewire init result: {ret}");

    print("Starting main loop");
    lib.main_loop_run();

    #time.sleep(50)
    print("After main loop");


