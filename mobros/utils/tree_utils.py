from anytree import PreOrderIter , LevelOrderGroupIter, Node

def overwrite_node_in_global_map(tree_map, node_name, parent_name, new_node):

    for e in tree_map[node_name]:
        if e.parent.name == parent_name:
            tree_map[node_name].remove(e)
    
    tree_map[node_name].append(new_node)

def clone_subtree(tree_map, tree_holder, new_node):
    local_map={}
    for layers in LevelOrderGroupIter(tree_holder, filter_=lambda n: n.name != tree_holder.name):
        for layer in layers:
            if layer.parent.name == new_node.name:
                local_map[layer.name] = Node(layer.name, new_node)
            else:
                local_map[layer.name] = Node(layer.name, local_map[layer.parent.name])
            overwrite_node_in_global_map(tree_map, layer.name, layer.parent.name, local_map[layer.name])

            
def remove_node_from_lost(node_map, package_name, lost_nodes_root):
    for e in node_map[package_name]:
        if e.parent == lost_nodes_root:
            e.parent = None
            node_map[package_name].remove(e)