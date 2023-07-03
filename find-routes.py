import configparser
import math
import pickle
import subprocess
from decimal import Decimal

import folium
import matplotlib.pyplot as plt
import networkx as nx
import overpy
import smopy
from geopy import distance

# Constants

BANNED_WAY_TAGS = (
    ("service", "parking_aisle"),
    ("highway", "service"),
)

config = configparser.ConfigParser()
config.read("walk.ini")
HOME_NODE = int(config["DEFAULT"]["HomeNode"])

# Maximum distance of a walk in meters.
MAX_DISTANCE = 1000


def filter_ways(ways):
    return [
        way
        for way in ways
        if not any(
            [
                (tag, way.tags[tag]) in BANNED_WAY_TAGS
                for tag in way.tags
                if way.tags[tag] is not None
            ]
        )
    ]


def get_api_result(home_node):
    try:
        with open("result.pkl", "rb") as f:
            result = pickle.load(f)
    except FileNotFoundError:
        api = overpy.Overpass()
        result = api.query(
            f"""
            node({home_node});
            (way(around:500););
            (._;>;);
            out;
            """
        )
        with open("result.pkl", "wb") as f:
            pickle.dump(result, f)
    finally:
        return result


def get_distance(node1, node2):
    return distance.distance(
        (node1["latitude"], node1["longitude"]), (node2["latitude"], node2["longitude"])
    ).meters


def get_non_backtracking_walk(
    graph,
    path,
    path_distance,
    target,
    max_distance,
    repeatable_edges=[],
    consumed_edges=[],
):
    if len(path) > 0:
        plot_map(graph, path)
    # Just Started
    if len(path) == 0:

        def get_repeatable_edges(start_node):
            current_node_index = 0
            repeatable_edge_nodes = [start_node]
            repeatable_edges = []
            while current_node_index < len(repeatable_edge_nodes):
                current_node = repeatable_edge_nodes[current_node_index]
                current_node_index += 1
                if len(tuple(graph.neighbors(current_node))) > 2:
                    continue
                for neighbor in graph.neighbors(current_node):
                    if neighbor not in repeatable_edge_nodes:
                        repeatable_edge_nodes.append(neighbor)
                        repeatable_edges.append(graph[current_node][neighbor])
            return repeatable_edges

        return get_non_backtracking_walk(
            graph=graph,
            path=[target],
            path_distance=0,
            target=target,
            max_distance=max_distance,
            repeatable_edges=get_repeatable_edges(target),
            consumed_edges=[],
        )
    else:
        current_node = path[-1]
        # Continuing Path
        if len(path) == 1 or current_node != target and path_distance < max_distance:
            neighbors = list(graph.neighbors(current_node))
            try:
                backtrack_node = path[-2]
                neighbors.remove(backtrack_node)
            except IndexError:
                pass
            costs = [
                graph[current_node][neighbor]["weight"]
                + get_distance(graph.nodes[current_node], graph.nodes[neighbor])
                for neighbor in neighbors
            ]
            neighbors_sorted = [
                neighbor for _, neighbor in sorted(zip(costs, neighbors))
            ]
            paths = [
                get_non_backtracking_walk(
                    graph=graph,
                    path=path + [neighbors_sorted[i]],
                    path_distance=path_distance
                    + graph[current_node][neighbors_sorted[i]]["weight"],
                    target=target,
                    max_distance=max_distance,
                    repeatable_edges=repeatable_edges,
                    consumed_edges=consumed_edges
                    + (
                        [graph[current_node][neighbors_sorted[i]]]
                        if not reference_in(
                            graph[current_node][neighbors_sorted[i]], repeatable_edges
                        )
                        else []
                    ),
                )
                for i in range(len(neighbors))
                if not reference_in(
                    graph[current_node][neighbors_sorted[i]], consumed_edges
                )
            ]
            paths = sum(paths, [])
            paths = list(filter(lambda path: path[0][-1] == target, paths))
            return sorted(paths, key=lambda path: path[1])

        # Finished
        else:
            return [[path, path_distance]]


def get_overpass_visualisation_query(path):
    query_node = lambda node: f"node({node});"
    query_nodes = lambda nodes: "\n  ".join([query_node(node) for node in nodes])
    overpass_query = f"(\n  {query_nodes(path)}\n);\nout;"
    return overpass_query


def get_path_length(graph, path):
    return sum([graph[path[i]][path[i + 1]]["weight"] for i in range(len(path) - 1)])


def plot_map(graph, path):
    map = smopy.Map(min_latitude, min_longitude, max_latitude, max_longitude)
    x, y = map.to_pixels(center_latitude, center_longitude)
    ax = map.show_mpl(figsize=(8, 8))
    ax.plot(x, y, "or", ms=10, mew=2)
    plt.plot(
        [graph.nodes[node]["longitude"] for node in path],
        [graph.nodes[node]["latitude"] for node in path],
        "ro-",
    )
    plt.show()
    input()
    exit()


def reference_in(object, iterable):
    for item in iterable:
        if item is object:
            return True
    return False


def save_map(graph, path):
    locations = [
        (graph.nodes[node]["latitude"], graph.nodes[node]["longitude"]) for node in path
    ]
    m = folium.Map(
        location=locations[0],
        zoom_start=15,
    )
    folium.Marker(location=locations[0], popup="Home").add_to(m)
    folium.PolyLine(locations=locations).add_to(m)
    m.save("map.html")


def main():
    result = get_api_result(HOME_NODE)
    ways = filter_ways(result.ways)
    graph = nx.Graph()
    for way in ways:
        for node_index in range(len(way.nodes)):
            node = way.nodes[node_index]
            graph.add_node(node.id, latitude=node.lat, longitude=node.lon)
            if node_index > 0:
                previous_node = way.nodes[node_index - 1]
                graph_node = graph.nodes[node.id]
                graph_previous_node = graph.nodes[previous_node.id]
                graph.add_edge(
                    node.id,
                    previous_node.id,
                    weight=get_distance(graph_node, graph_previous_node),
                )
    walks = get_non_backtracking_walk(
        graph=graph,
        path=[],
        path_distance=0,
        target=home_node,
        max_distance=MAX_DISTANCE,
    )
    for walk in walks:
        save_map(graph, walk[0])
        print(get_overpass_visualisation_query(walk[0]))


if __name__ == "__main__":
    main()
