import configparser
import pickle
import subprocess
import sys
from decimal import Decimal

import folium
import matplotlib.pyplot as plt
import networkx as nx
import overpy
import smopy
from geopy import Point, distance

# Constants

# Ways with these tags will not be included for path finding.
BANNED_WAY_TAGS = (
    ("building",),
    ("highway", "service"),
    ("landuse", "grass"),
    ("leisure", "pitch"),
    ("service", "parking_aisle"),
)
REQUIRED_WAY_TAGS = (("highway",),)

# Start / end node of the walk.
config = configparser.ConfigParser()
config.read("walk.ini")
HOME_NODE = int(config["DEFAULT"]["HomeNode"])

# Maximum distance of a walk in meters.
MAX_DISTANCE = int(config["DEFAULT"]["MaxDistance"])

# Globals
cache = {}


def build_graph(ways):
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
                    weight=get_distance_between_nodes(graph_node, graph_previous_node),
                )
    return graph


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


def get_distance_between_nodes(node1, node2):
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
    follow=False,
):
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
            follow=follow,
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
                + get_distance_between_nodes(
                    graph.nodes[current_node], graph.nodes[neighbor]
                )
                for neighbor in neighbors
            ]
            neighbors_sorted = [
                neighbor for _, neighbor in sorted(zip(costs, neighbors))
            ]
            costs_sorted = sorted(costs)
            legal_neighbors = [
                neighbor
                for neighbor in neighbors_sorted
                if not reference_in(graph[current_node][neighbor], consumed_edges)
            ]
            if follow:
                plot_map(
                    graph=graph,
                    path=path,
                    legal_neighbors=legal_neighbors,
                )
            paths = [
                get_non_backtracking_walk(
                    graph=graph,
                    path=path + [legal_neighbors[i]],
                    path_distance=path_distance
                    + graph[current_node][legal_neighbors[i]]["weight"],
                    target=target,
                    max_distance=max_distance,
                    repeatable_edges=repeatable_edges,
                    consumed_edges=consumed_edges
                    + (
                        [graph[current_node][legal_neighbors[i]]]
                        if not reference_in(
                            graph[current_node][legal_neighbors[i]], repeatable_edges
                        )
                        else []
                    ),
                    follow=follow,
                )
                for i in range(len(legal_neighbors))
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


def get_plot_background(center_point):
    # Map for plotting route.
    try:
        with open("plot_background.pkl", "rb") as f:
            plot_background = pickle.load(f)
    except FileNotFoundError:
        corner_distance = MAX_DISTANCE / 2**0.5
        top_left_point = distance.geodesic(meters=corner_distance).destination(
            center_point, 315
        )
        bottom_right_point = distance.geodesic(meters=corner_distance).destination(
            center_point, 135
        )
        plot_background = smopy.Map(
            top_left_point[0],
            top_left_point[1],
            bottom_right_point[0],
            bottom_right_point[1],
            z=19,
        )
        with open("plot_background.pkl", "wb") as f:
            pickle.dump(plot_background, f)
    return plot_background


def plot_map(graph, path, legal_neighbors=[], manual_pause=False):
    global cache
    # cache["iteration"] = cache.get("iteration", -1) + 1
    # if cache["iteration"] % 10 != 0:
    #     return
    center_point = Point(
        graph.nodes[HOME_NODE]["latitude"], graph.nodes[HOME_NODE]["longitude"]
    )
    plot_background = get_plot_background(center_point)
    path_pixels = [
        plot_background.to_pixels(
            float(graph.nodes[node]["latitude"]), float(graph.nodes[node]["longitude"])
        )
        for node in path
    ]
    path_x, path_y = zip(*path_pixels)
    if cache.get("first_plot", True):
        ax = plot_background.show_mpl()
        cache["first_plot"] = False
    else:
        ax = plt.gca()
        ax.imshow(plot_background.img)
    ax.plot(path_x[:-1], path_y[:-1], "ro-", linewidth=2, markersize=1)
    ax.plot(path_x[-2:], path_y[-2:], "b-", linewidth=1, markersize=1)
    ax.plot(path_x[-1], path_y[-1], "bo", linewidth=1, markersize=3)

    for neighbor in legal_neighbors:
        neighbor_pixel = plot_background.to_pixels(
            float(graph.nodes[neighbor]["latitude"]),
            float(graph.nodes[neighbor]["longitude"]),
        )
        ax.plot(
            (path_x[-1], neighbor_pixel[0]),
            (path_y[-1], neighbor_pixel[1]),
            "go-",
            linewidth=1,
            markersize=2,
        )
    neighbor_pixels = [
        plot_background.to_pixels(
            float(graph.nodes[neighbor]["latitude"]),
            float(graph.nodes[neighbor]["longitude"]),
        )
        for neighbor in legal_neighbors
    ]
    try:
        neighbor_x, neighbor_y = zip(*neighbor_pixels)
    except ValueError:
        neighbor_x = tuple()
        neighbor_y = tuple()
    all_x = path_x + neighbor_x
    all_y = path_y + neighbor_y
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)
    data_width = max_x - min_x
    data_height = max_y - min_y
    plot_margin = max(1, max((data_width, data_height)) * 0.1)
    plt.axis(
        (
            min_x - plot_margin,
            max_x + plot_margin,
            max_y + plot_margin,
            min_y - plot_margin,
        )
    )
    plt.draw()
    if manual_pause:
        input("Press enter to continue...")
    else:
        plt.pause(0.01)
    plt.cla()


def reduce_segment(graph, nodes, start_node_index=None, end_node_index=None):
    if start_node_index == None:
        reduce_segment(
            graph=graph,
            nodes=nodes,
            start_node_index=0,
            end_node_index=1,
        )
    elif (
        end_node_index < len(nodes) - 1
        and len(tuple(graph.neighbors(nodes[end_node_index].id))) == 2
        and nodes[end_node_index].id != HOME_NODE
    ):
        reduce_segment(
            graph=graph,
            nodes=nodes,
            start_node_index=start_node_index,
            end_node_index=end_node_index + 1,
        )
    elif (
        end_node_index == len(nodes) - 1
        or len(tuple(graph.neighbors(nodes[end_node_index].id))) != 2
        or nodes[end_node_index].id == HOME_NODE
    ):
        distance = sum(
            graph[nodes[i].id][nodes[i + 1].id]["weight"]
            for i in range(start_node_index, end_node_index)
        )
        for node in nodes[start_node_index + 1 : end_node_index]:
            graph.remove_node(node.id)
        graph.add_edge(
            nodes[start_node_index].id, nodes[end_node_index].id, weight=distance
        )
        if end_node_index < len(nodes) - 1:
            reduce_segment(
                graph=graph,
                nodes=nodes,
                start_node_index=end_node_index,
                end_node_index=end_node_index + 1,
            )
        else:
            return


def reduce_segments(graph, ways):
    for way in ways:
        reduce_segment(graph, way.nodes)
    return graph


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


def way_filter(way):
    for tag in BANNED_WAY_TAGS:
        if len(tag) == 1:
            if way.tags.get(tag[0], None) is not None:
                return False
        elif len(tag) == 2:
            if way.tags.get(tag[0], None) == tag[1]:
                return False
    for tag in REQUIRED_WAY_TAGS:
        if len(tag) == 1:
            if way.tags.get(tag[0], None) is None:
                return False
    return True


def main():
    args = sys.argv
    follow = "--follow" in args or "-f" in args
    gallery = "--gallery" in args or "-g" in args
    result = get_api_result(HOME_NODE)
    ways = tuple(filter(way_filter, result.ways))
    graph = build_graph(ways)
    reduce_segments(graph, ways)
    removed_nodes = [node for node in graph.nodes if graph.nodes[node] == {}]
    if follow:
        plt.show(block=False)
    walks = get_non_backtracking_walk(
        graph=graph,
        path=[],
        path_distance=0,
        target=HOME_NODE,
        max_distance=MAX_DISTANCE,
        follow=follow,
    )
    if gallery:
        for walk in walks:
            plot_map(graph, walk[0], manual_pause=True)
    for walk in walks:
        save_map(graph, walk[0])
        print(get_overpass_visualisation_query(walk[0]))


if __name__ == "__main__":
    main()
