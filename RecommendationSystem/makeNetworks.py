import networkx as nx
import numpy as np


def section_path(path, t=0, step=None):

    graph = nx.DiGraph()

    last = None
    # add LN in history that leads to this state:
    step = {"id": t, "name": f"step_{t}", "grade": 0} if not step else step
    graph.add_node("H_"+str(step["id"]), name=step["name"], ln_id=step["id"],
                   grade=step["grade"], pos=(0, -t), type="ln", t=t)
    # add sections
    for x, section in enumerate(path):
        current = "S_"+str(section["resp_id"])
        graph.add_node(current,
                       name=section["name"],
                       s_id=section["resp_id"],
                       mastery=np.round(section["exp"], 2),
                       link=section["section_anchor"],
                       ln_path=section["learning_nuggets"],
                       pos=(x+1, -t),
                       type="section"
                       )
        if last:
            graph.add_edge(last, current, type="next")
        last = current

    return graph


def get_diff(graph_0, graph_1):

    diff = nx.compose(graph_0, graph_1)
    joined = list(diff.nodes.keys())
    for node in joined:
        if diff.nodes[node]["type"] == "ln":
            diff.remove_node(node)
        elif node not in graph_0.nodes:  # added node
            attr = diff.nodes[node]
            x_pos = get_previous_x(node, graph_1, graph_0)
            diff.add_node(node.replace("S", "X"),
                          name=attr["name"],
                          s_id=attr["s_id"],
                          mastery=attr["mastery"],
                          link=attr["link"],
                          ln_path=attr["ln_path"],
                          pos=(x_pos, attr["pos"][1]+1),
                          type="section",
                          change="added"
                          )
            diff.add_edge(node.replace("S", "X"), node, type="add")
        elif node not in graph_1.nodes:  # removed node
            attr = diff.nodes[node]
            x_pos = get_previous_x(node, graph_0, graph_1)
            diff.add_node(node.replace("S", "X"),
                          name=attr["name"],
                          s_id=attr["s_id"],
                          mastery=attr["mastery"],
                          link=attr["link"],
                          ln_path=attr["ln_path"],
                          pos=(x_pos, attr["pos"][1]-1),
                          type="section",
                          change="removed"
                          )
            diff.add_edge(node, node.replace("S", "X"), type="remove")
        elif graph_0.nodes[node]["ln_path"] != graph_1.nodes[node]["ln_path"]:
            attr = graph_0.nodes[node]
            diff.add_node(node.replace("S", "X"),
                          name=attr["name"],
                          s_id=attr["s_id"],
                          mastery=attr["mastery"],
                          link=attr["link"],
                          ln_path=attr["ln_path"],
                          pos=(attr["pos"][0], attr["pos"][1]),
                          type="section",
                          change="changed"
                          )
            diff.add_edge(node.replace("S", "X"), node, type="change")
        else:
            diff.remove_node(node)
    to_remove = []
    for edge in diff.edges.data():
        if edge[2]["type"] == "next":
            to_remove.append((edge[0], edge[1]))
    diff.remove_edges_from(to_remove)

    return diff


def get_previous_x(node, graph_a, graph_b):

    node_attr = graph_a.nodes[node]
    if node_attr["pos"][0] == 1:
        return 1

    current_node = node
    while node_attr["pos"][0] > 1:

        previous_node = list(graph_a.in_edges(current_node))[0][0]
        node_attr = graph_a.nodes[previous_node]

        if previous_node in graph_b.nodes:
            return graph_b.nodes[previous_node]["pos"][0] + 1
        current_node = previous_node

    return 1


def get_step(graph, step, t):

    step_from = nx.DiGraph()

    step_from.add_node("H_" + str(step["id"]), pos=(0, -t), t=t)
    section = step["section"]
    if section in graph.nodes.keys():
        attr = graph.nodes[section]
        step_from.add_node(section, pos=(attr["pos"][0], attr["pos"][1]))
        step_from.add_edge(section, "H_" + str(step["id"]), type="step_from")

    return step_from
