import os
import json

from littlechef import runner, lib, chef
from logbook import Logger, MonitoringFileHandler

from kitchen.settings import DEBUG, REPO, REPO_BASE_PATH, KITCHEN_DIR, LOG_FILE


file_log_handler = MonitoringFileHandler(LOG_FILE, bubble=DEBUG)
file_log_handler.push_application()
log = Logger('kitchen.lib')


def _check_kitchen():
    current_dir = os.getcwd()
    os.chdir(KITCHEN_DIR)
    in_a_kitchen, missing = runner._check_appliances()
    os.chdir(current_dir)
    if not in_a_kitchen:
        missing_str = lambda m: ' and '.join(', '.join(m).rsplit(', ', 1))
        log.error("Couldn't find {0}. ".format(missing_str(missing)))
        return False
    else:
        return True


def build_node_data_bag():
    """Tell LittleChef to build the node data bag"""
    current_dir = os.getcwd()
    os.chdir(KITCHEN_DIR)
    try:
        chef._build_node_data_bag()
    except SystemExit as e:
        log.error(e)
    finally:
        os.chdir(current_dir)


def load_data(data_type):
    """Load the kitchen's node files"""
    if not _check_kitchen():
        return []
    current_dir = os.getcwd()
    os.chdir(KITCHEN_DIR)
    nodes = []
    if data_type not in ["nodes", "roles"]:
        log.error("Unsupported data type '{0}'".format(data_type))
        return nodes
    try:
        nodes = getattr(lib, "get_" + data_type)()
    except SystemExit as e:
        log.error(e)
    finally:
        os.chdir(current_dir)
    return nodes


def load_extended_node_data():
    """Load JSON node files from node databag, which has merged attributes"""
    data_bag_path = os.path.join(KITCHEN_DIR, "data_bags", "node")
    if not os.path.exists(data_bag_path):
        log.error("Node data bag has not yet been built")
        return [{"error": "Node data bag has not yet been built"}]

    nodes = load_data("nodes")
    data = []
    for node in nodes:
        filename = os.path.join(data_bag_path,
                                node['name'].replace(".s", "_") + ".json")
        if not os.path.exists(filename):
            log.error("Node data bag is missing {0}".format(filename))
            return [{"error": "Node data bag is missing some node files"}]
        with open(filename, 'r') as f:
            try:
                data.append(json.loads(f.read()))
            except json.JSONDecodeError as e:
                msg = 'LittleChef found the following error in'
                msg += ' "{0}":\n                {1}'.format(node_path, str(e))
    if len(data) != len(nodes):
        error = "The node data bag doesn't have the same number of nodes as "
        error += "there are node files: {0} => {1}".format(
            len(data), len(nodes))
        log.error(error)
        return [{"error": error}]
    return data


def get_nodes_extended():
    return load_extended_node_data()


def get_nodes():
    return load_data("nodes")


def get_roles():
    return load_data("roles")
