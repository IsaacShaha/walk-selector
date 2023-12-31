import configparser
import hashlib
import os
import pickle
import random
import subprocess
import sys
from decimal import Decimal

import folium
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import overpy
import smopy
from geopy import Point, distance

# Constants

# Ways with these tags will not be included for path finding.
BANNED_WAY_TAGS = (
    ("building",),
    ("footway",),
    ("highway", "service"),
    ("landuse", "grass"),
    ("leisure", "pitch"),
    ("service", "parking_aisle"),
)
FILES_TO_HASH = (
    "config.ini",
    "find-routes.py",
)
CACHE_FILES = (
    "plot_background.pkl",
    "result.pkl",
    "walks.pkl",
)
REQUIRED_WAY_TAGS = (("highway",),)

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


def get_angle(direction1, direction2):
    angle = direction2 - direction1
    if angle > np.pi:
        angle -= 2 * np.pi
    elif angle < -np.pi:
        angle += 2 * np.pi
    return angle


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


def get_direction(node1, node2):
    lat1 = float(node1["latitude"])
    lon1 = float(node1["longitude"])
    lat2 = float(node2["latitude"])
    lon2 = float(node2["longitude"])
    return np.arctan2(lat2 - lat1, lon2 - lon1)


def get_distance_between_nodes(node1, node2):
    return distance.distance(
        (node1["latitude"], node1["longitude"]), (node2["latitude"], node2["longitude"])
    ).meters


def get_expanded_path(graph, nodes):
    expanded_path = [nodes[0]]
    for i in range(len(nodes) - 1):
        current_node = nodes[i]
        next_node = nodes[i + 1]
        if "inner_path" in graph[current_node][next_node]:
            inner_path = graph[current_node][next_node]["inner_path"]
            reverse = inner_path[0] == next_node
            expanded_path += (list(reversed(inner_path)) if reverse else inner_path)[1:]
        else:
            expanded_path.append(next_node)
    return expanded_path


def get_file_hash(filename, hash_function=hashlib.sha256):
    file_hash = hash_function()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def get_files_hash(filenames, hash_function=hashlib.sha256):
    files_hash = hash_function()
    for filename in filenames:
        files_hash.update(get_file_hash(filename, hash_function).encode())
    return files_hash.hexdigest()


def get_non_backtracking_walks(
    graph,
    max_distance,
    path,
    target,
    consumed_edges=[],
    direction=None,
    follow=False,
    path_angle=0,
    path_distance=0,
    repeatable_edges=[],
):
    # Just Started
    if len(path) == 0:
        if not follow:
            try:
                with open("walks.pkl", "rb") as f:
                    walks = pickle.load(f)
                return walks
            except FileNotFoundError:
                pass

        walks = get_non_backtracking_walks(
            graph=graph,
            max_distance=max_distance,
            path=[target],
            target=target,
            consumed_edges=consumed_edges,
            direction=direction,
            follow=follow,
            path_angle=path_angle,
            path_distance=path_angle,
            repeatable_edges=repeatable_edges
            + get_repeatable_edges(
                graph=graph,
                start_node=target,
            ),
        )
        with open("walks.pkl", "wb") as f:
            pickle.dump(walks, f)
        return walks
    else:
        current_node = path[-1]
        # Continuing Path
        if (
            len(path) == 1
            or current_node != target
            and (
                path_distance
                + get_distance_between_nodes(
                    graph.nodes[current_node], graph.nodes[target]
                )
                < max_distance
            )
        ):
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
                    home_node=target,
                    max_distance=max_distance,
                    legal_neighbors=legal_neighbors,
                    manual_pause=True,
                )
            paths = [
                get_non_backtracking_walks(
                    graph=graph,
                    max_distance=max_distance,
                    path=path + [legal_neighbors[i]],
                    target=target,
                    consumed_edges=consumed_edges
                    + (
                        [graph[current_node][legal_neighbors[i]]]
                        if not reference_in(
                            graph[current_node][legal_neighbors[i]], repeatable_edges
                        )
                        else []
                    ),
                    direction=get_direction(
                        graph.nodes[current_node], graph.nodes[legal_neighbors[i]]
                    ),
                    follow=follow,
                    path_angle=(
                        path_angle
                        + abs(
                            get_angle(
                                direction,
                                get_direction(
                                    graph.nodes[current_node],
                                    graph.nodes[legal_neighbors[i]],
                                ),
                            )
                        )
                        if direction is not None
                        else path_angle
                    ),
                    path_distance=(
                        path_distance
                        + graph[current_node][legal_neighbors[i]]["weight"]
                    ),
                    repeatable_edges=repeatable_edges,
                )
                for i in range(len(legal_neighbors))
            ]
            paths = sum(paths, [])
            paths = list(filter(lambda path: path[0][-1] == target, paths))
            return sorted(paths, key=lambda path: path[1])

        # Finished
        else:
            return [[path, path_angle / path_distance]]


def get_overpass_visualisation_query(graph, path):
    path = get_expanded_path(graph, path)
    query_node = lambda node: f"node({node});"
    query_nodes = lambda nodes: "\n  ".join([query_node(node) for node in nodes])
    overpass_query = f"(\n  {query_nodes(path)}\n);\nout;"
    return overpass_query


def get_path_length(graph, path):
    return sum([graph[path[i]][path[i + 1]]["weight"] for i in range(len(path) - 1)])


def get_plot_background(center_point, max_distance):
    # Map for plotting route.
    try:
        with open("plot_background.pkl", "rb") as f:
            plot_background = pickle.load(f)
    except FileNotFoundError:
        corner_distance = max_distance / 2**0.5
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


def get_repeatable_edges(graph, start_node):
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


def get_walk_constraints():
    config = configparser.ConfigParser()
    config.read("config.ini")
    home_node = int(config["DEFAULT"]["HomeNode"])
    max_distance = int(config["DEFAULT"]["MaxDistance"])
    num_walks = int(config["DEFAULT"]["NumWalks"])
    return home_node, max_distance, num_walks


def plot_map(
    graph,
    path,
    home_node,
    max_distance,
    legal_neighbors=[],
    manual_pause=False,
    disconnected=False,
    marker_size=10,
):
    global cache
    center_point = Point(
        graph.nodes[home_node]["latitude"], graph.nodes[home_node]["longitude"]
    )
    plot_background = get_plot_background(
        center_point=center_point,
        max_distance=max_distance,
    )
    path = get_expanded_path(graph, path)
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
    angles = [
        np.arctan2(path_y[i + 1] - path_y[i], path_x[i + 1] - path_x[i])
        for i in range(len(path_x) - 1)
    ]
    if disconnected:
        ax.plot(path_x, path_y, "ro", markersize=marker_size)
    else:
        ax.plot(path_x[:-1], path_y[:-1], "r-", linewidth=2)
        ax.plot(path_x[-2:], path_y[-2:], "b-", linewidth=2)
        ax.plot(path_x[-1], path_y[-1], "g-", linewidth=2)
        for i in range(len(path_x)):
            ax.text(path_x[i] - len(path_x) * 2 / 3 + i, path_y[i], str(i), fontsize=20)

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
    plt.pause(0.01)
    if manual_pause:
        input("Press enter to continue...")
    plt.cla()


def reduce_segment(graph, nodes, home_node, start_node_index=None, end_node_index=None):
    if start_node_index == None:
        # Way is a cycle.
        if nodes[0] == nodes[-1]:
            nodes.pop()
            # Find an external entrypoint to the cycle, and re-order the cycle so that it is the first node.
            for i in range(len(nodes)):
                if len(tuple(graph.neighbors(nodes[i].id))) > 2:
                    nodes = nodes[i:] + nodes[: i + 1]
                    break
        reduce_segment(
            graph=graph,
            nodes=nodes,
            home_node=home_node,
            start_node_index=0,
            end_node_index=1,
        )
    elif (
        end_node_index < len(nodes) - 1
        and len(tuple(graph.neighbors(nodes[end_node_index].id))) == 2
        and nodes[end_node_index].id != home_node
    ):
        reduce_segment(
            graph=graph,
            nodes=nodes,
            home_node=home_node,
            start_node_index=start_node_index,
            end_node_index=end_node_index + 1,
        )
    elif (
        end_node_index == len(nodes) - 1
        or len(tuple(graph.neighbors(nodes[end_node_index].id))) != 2
        or nodes[end_node_index].id == home_node
    ):
        distance = sum(
            graph[nodes[i].id][nodes[i + 1].id]["weight"]
            for i in range(start_node_index, end_node_index)
        )
        for i in range(start_node_index, end_node_index):
            graph.remove_edge(nodes[i].id, nodes[i + 1].id)
        inner_path = [node.id for node in nodes[start_node_index : end_node_index + 1]]
        graph.add_edge(
            nodes[start_node_index].id,
            nodes[end_node_index].id,
            inner_path=inner_path,
            weight=distance,
        )
        if end_node_index < len(nodes) - 1:
            reduce_segment(
                graph=graph,
                nodes=nodes,
                home_node=home_node,
                start_node_index=end_node_index,
                end_node_index=end_node_index + 1,
            )
        else:
            return


def reduce_segments(graph, ways, home_node):
    for way in ways:
        reduce_segment(
            graph=graph,
            nodes=way.nodes,
            home_node=home_node,
        )
    return graph


def reference_in(object, iterable):
    for item in iterable:
        if item is object:
            return True
    return False


def save_map(graph, path, map_number=None):
    path = get_expanded_path(graph, path)
    tuple_nodes = [
        (graph.nodes[node]["latitude"], graph.nodes[node]["longitude"]) for node in path
    ]
    nodes = [graph.nodes[node] for node in path]
    m = folium.Map(
        location=tuple_nodes[0],
        zoom_start=14,
    )
    folium.Marker(location=tuple_nodes[0], popup="Home").add_to(m)
    folium.PolyLine(locations=tuple_nodes).add_to(m)
    # Draw arrows.
    for i in range(1, len(tuple_nodes)):
        if len(tuple(graph.neighbors(path[i]))) > 2:
            folium.RegularPolygonMarker(
                location=tuple_nodes[i],
                fill_color="#000000",
                number_of_sides=3,
                radius=10,
                rotation=180 - np.rad2deg(get_direction(nodes[i - 1], nodes[i])),
            ).add_to(m)
    map_number_representation = f"-{map_number}" if map_number is not None else ""
    m.save(f"maps/walk{map_number_representation}.html")


def update_files_hash(file_names, hash_function=hashlib.sha256):
    files_hash = get_files_hash(file_names, hash_function)
    with open("hash.sha256", "w") as f:
        f.write(files_hash)


def verify_files_hash(file_names, hash_function=hashlib.sha256):
    try:
        with open("hash.sha256", "r") as f:
            previous_hash = f.read()
        files_hash = get_files_hash(file_names, hash_function)
    except FileNotFoundError:
        update_files_hash(file_names, hash_function)
        return False
    if previous_hash != files_hash:
        update_files_hash(file_names, hash_function)
        return False
    return True


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
    if not verify_files_hash(FILES_TO_HASH):
        for file in CACHE_FILES:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
    home_node, max_distance, num_walks = get_walk_constraints()
    args = sys.argv
    follow = "--follow" in args or "-f" in args
    gallery = "--gallery" in args or "-g" in args
    overpass = "--overpass" in args or "-o" in args
    randomize = "--random" in args or "-r" in args
    save = "--save" in args or "-s" in args
    result = get_api_result(home_node)
    ways = tuple(filter(way_filter, result.ways))
    graph = build_graph(ways)
    reduce_segments(
        graph=graph,
        ways=ways,
        home_node=home_node,
    )
    if follow:
        plt.show(block=False)
    walks = get_non_backtracking_walks(
        graph=graph,
        max_distance=max_distance,
        path=[],
        target=home_node,
        follow=follow,
    )
    # Take the walks with the num_walks-lowest path angle/distance.
    walks = sorted(walks, key=lambda walk: walk[1])[:num_walks]
    if randomize:
        walks = random.sample(walks, len(walks))
    print(f"Found {len(walks)} walks.")
    if gallery:
        for i in range(len(walks)):
            walk = walks[i]
            print(f"Walk {i+1}")
            plot_map(
                graph=graph,
                path=walk[0],
                home_node=home_node,
                max_distance=max_distance,
                manual_pause=True,
            )
    if overpass:
        for walk in walks:
            save_map(graph, walk[0])
            print(
                get_overpass_visualisation_query(graph=graph, path=walk[0]),
            )
    if save:
        for i in range(len(walks)):
            walk = walks[i]
            save_map(graph, walk[0], i + 1)


if __name__ == "__main__":
    main()
