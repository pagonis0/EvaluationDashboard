import plotly.graph_objects as go
import networkx as nx
import json

from RecommendationSystem.makeNetworks import section_path, get_diff, get_step


def _path_traces(graph):
    # get edge positions
    edge_x = []
    edge_y = []
    for edge in graph.edges:
        x0, y0 = graph.nodes[edge[0]]['pos']
        x1, y1 = graph.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=3, color='#888'),
        hoverinfo='none',
        showlegend=False,
        mode='markers+lines',
        marker=dict(
            symbol="arrow",
            color="#888",
            size=16,
            angleref="previous",
            standoff=8,
            )
    )

    # get section positions
    node_x = []
    node_y = []
    for node in graph.nodes():
        if graph.nodes[node]['type'] == "section":
            x, y = graph.nodes[node]['pos']
            node_x.append(x)
            node_y.append(y)

    node_trace_sections = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            reversescale=True,
            color=[],
            size=12,
            colorbar=dict(
                thickness=15,
                title='Mastery',
                xanchor='left',
                titleside='right'
            ),
            cmin=0,
            cmax=1,
            line_width=2)
    )

    # get ln positions
    node_x = []
    node_y = []
    for node in graph.nodes():
        if graph.nodes[node]['type'] == "ln":
            x, y = graph.nodes[node]['pos']
            node_x.append(x)
            node_y.append(y)

    node_trace_lns = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color="white",
            size=14,
            line_width=2)
    )
    return node_trace_sections, node_trace_lns, edge_trace


def _diff_traces(diff, t_0, end_0, end_1):

    diffs = []
    for change in diff.edges.data():
        if change[2]["type"] == "add":
            empty = diff.nodes[change[0]]
            added = diff.nodes[change[1]]

            scope_0 = 0.1 if empty["pos"][0] <= end_0["pos"][0] else (empty["pos"][0] - end_0["pos"][0])-0.2
            scope_1 = 0.1 if added == end_1 else 0.9

            x0 = added["pos"][0]-0.1
            x1 = empty["pos"][0]-scope_0
            x2 = added["pos"][0]+scope_1
            y0 = added["pos"][1]-0.1
            y1 = added["pos"][1]+0.1
            y2 = empty["pos"][1]-0.1
            y3 = empty["pos"][1]
            change_trace = go.Scatter(
                x=[x0,x0,x1,x1,x1,x2,x2,x0],
                y=[y0,y1,y2,y3,y2,y1,y0,y0],
                fill='toself', fillcolor='lightgreen',
                line_color='lightgreen', mode="lines",
                showlegend=False
            )
        elif change[2]["type"] == "remove":
            removed = diff.nodes[change[0]]
            empty = diff.nodes[change[1]]

            scope_0 = 0.1 if removed == end_0 else 0.9
            scope_1 = 0.1 if empty["pos"][0] <= end_1["pos"][0] else (empty["pos"][0] - end_1["pos"][0]) - 0.2

            x0 = removed["pos"][0]-0.1
            x1 = empty["pos"][0]-scope_1
            x2 = removed["pos"][0]+scope_0
            y0 = removed["pos"][1]+0.1
            y1 = removed["pos"][1]-0.1
            y2 = empty["pos"][1]+0.1
            y3 = empty["pos"][1]
            change_trace = go.Scatter(
                x=[x0, x0, x1, x1, x1, x2, x2, x0],
                y=[y0, y1, y2, y3, y2, y1, y0, y0],
                fill='toself', fillcolor='lightsalmon',
                line_color='lightsalmon', mode="lines",
                showlegend=False
            )
        elif change[2]["type"] == "change":
            old = diff.nodes[change[0]]
            new = diff.nodes[change[1]]

            scope_0 = 0.1 if change[0] == end_0 else 0.9
            scope_1 = 0.1 if change[1] == end_1 else 0.9

            x0 = old["pos"][0]-0.1
            x1 = new["pos"][0]-0.1
            x2 = new["pos"][0]+scope_1
            x3 = old["pos"][0]+scope_0
            y0 = old["pos"][1]+0.1
            y1 = old["pos"][1]-0.1
            y2 = new["pos"][1]+0.1
            y3 = new["pos"][1]-0.1
            change_trace = go.Scatter(
                x=[x0, x0, x1, x1, x2, x2, x3, x3, x0],
                y=[y0, y1, y2, y3, y3, y2, y1, y0, y0],
                fill='toself', fillcolor='skyblue',
                line_color='skyblue', mode="lines",
                showlegend=False
            )
        else:
            raise ValueError(f"Unexpected change type: {change[2]['type']}")
        diffs.append(change_trace)

    return diffs


def _step_traces(step_from):

    step_trace = []
    if nx.is_empty(step_from):
        print(step_from.nodes.values())
        step = list(step_from.nodes.values())[0]
        t_section_1 = None
    else:
        section = step_from.nodes[list(step_from.edges().keys())[0][0]]
        print("section", section)
        step = step_from.nodes[list(step_from.edges().keys())[0][1]]
        print("step", step)

        mid_y = section['pos'][1] + (step['pos'][1] - section['pos'][1])/2

        t_section_0 = go.Scatter(
            x=(section['pos'][0], section['pos'][0], 0),
            y=(section['pos'][1], mid_y, mid_y),
            line=dict(width=2, color='black'),
            hoverinfo='none',
            showlegend=False,
            mode='lines'
        )
        t_section_1 = go.Scatter(
            x=(0, 0),
            y=(mid_y, step['pos'][1]),
            line=dict(width=2, color='black'),
            hoverinfo='none',
            showlegend=False,
            mode='markers+lines',
            marker=dict(
                symbol="arrow",
                color="black",
                size=16,
                angleref="previous",
                standoff=8,
            )
        )

    t_step = go.Scatter(
        x=(0, 0), y=(step['pos'][1]+1, step['pos'][1]),
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        showlegend=False,
        mode='markers+lines',
        marker=dict(
            symbol="arrow",
            color="#888",
            size=16,
            angleref="previous",
            standoff=8,
        )
    )
    step_trace.append(t_step)
    if t_section_1:
        step_trace.append(t_section_0)
        step_trace.append(t_section_1)

    return step_trace


def go_plot(graphs, diffs, course, steps_from):

    traces = []

    # create diff figures
    for t in range(len(graphs)-1):
        end_0 = graphs[t].nodes[
            [node for node in graphs[t].nodes() if graphs[t].out_degree(node)==0 and node.startswith("S")][0]]
        end_1 = graphs[t+1].nodes[
            [node for node in graphs[t+1].nodes() if graphs[t+1].out_degree(node)==0 and node.startswith("S")][0]]
        diff_traces = _diff_traces(diffs[t], t, end_0, end_1)
        traces.extend(diff_traces)
        step_traces = _step_traces(steps_from[t])
        traces.extend(step_traces)

    # create recommendation path figures
    for graph in graphs:
        node_trace_sections, node_trace_lns, edge_trace = _path_traces(graph)

        # node labels and color
        ln_text = []
        section_text = []
        section_mastery = []
        for node in graph.nodes.data():
            if node[1]['type'] == "section":
                section_text.append(f"S_ID: {node[0][2:]}<br>Name: {node[1]['name']}<br>Mastery: {node[1]['mastery']}")
                section_mastery.append(node[1]['mastery'])
            elif node[1]['type'] == "ln":
                ln_text.append(f"LN_ID: {node[0][2:]}<br>Name: {node[1]['name']}<br>Grade:{node[1]['grade']}")

        node_trace_lns.text = ln_text
        node_trace_sections.text = section_text
        node_trace_sections.marker.color = section_mastery

        # add edges before nodes, so the nodes are plotted 'above' the edges
        traces.append(edge_trace)
        traces.append(node_trace_sections)
        traces.append(node_trace_lns)

    # create graph
    fig = go.Figure(data=traces,
                    layout=go.Layout(
                        # title=course,
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    return fig


def default_fig():
    fig = go.Figure(
        layout=go.Layout(
            annotations=[
                go.layout.Annotation(
                    text='<b>There is no path to display (yet).</b>',
                    align='center',
                    bordercolor='black',
                    borderwidth=2,
                    font=dict(
                        color="black",
                        size=40
                    ),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )
    return fig


if __name__ == "__main__":

    steps = ["S_26", "S_27", "S_0", "S_19", "S_138"]
    graphs = []
    diffs = []
    steps_from = []
    prev_path = None
    for t in range(5):

        with open(f"../sample_rec_{t}.json", "r") as jf:
            j = json.load(jf)

        course = j["courses"][0]["course"]["name"]
        path = j["courses"][0]["section_path"]

        step = {"id": t, "name": f"step_{t}", "grade": 0, "section": steps[t]}

        current = section_path(path, t=t, step=step)
        graphs.append(current)

        if prev_path:
            diff = get_diff(prev_path, current)
            diffs.append(diff)
            step_from = get_step(prev_path, step, t)
            steps_from.append(step_from)
        prev_path = current

    #go_plot(graphs, diffs, course, steps_from)
    fig = default_fig()
    fig.show()
