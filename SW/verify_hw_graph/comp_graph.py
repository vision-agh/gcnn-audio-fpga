import json

# Function to load JSON data from a file
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to compare two JSON datasets
def compare_edges(file1, file2):
    # Load JSON data
    data1 = load_json(file1)
    data2 = load_json(file2)

    # Check if the number of events matches
    if len(data1) != len(data2):
        print(f"Number of events mismatch: {len(data1)} (file1) vs {len(data2)} (file2)")
        return

    total_edges_file1 = 0
    total_edges_file2 = 0
    matching_edges = 0
    mismatched_edges = 0

    # Compare events and edges
    for i, (event1, event2) in enumerate(zip(data1, data2)):
        # Compare pos_item
        if event1["pos_item"] != event2["pos_item"]:
            print(f"Event {i} pos_item mismatch: {event1['pos_item']} vs {event2['pos_item']}")
            continue  # Skip comparison for this event if pos_item mismatches

        # Compare edges count
        edges1 = event1["edges"]
        edges2 = event2["edges"]
        total_edges_file1 += len(edges1)
        total_edges_file2 += len(edges2)

        if len(edges1) != len(edges2):
            print(f"Event {i} edges count mismatch: {len(edges1)} (file1) vs {len(edges2)} (file2)")

        # Compare edge details
        edges1_set = {frozenset(edge.items()) for edge in edges1}
        edges2_set = {frozenset(edge.items()) for edge in edges2}
        common_edges = edges1_set.intersection(edges2_set)
        mismatches = edges1_set.symmetric_difference(edges2_set)

        matching_edges += len(common_edges)
        mismatched_edges += len(mismatches)

        if mismatches:
            print(f"Event {i} mismatched edges:")
            for mismatch in mismatches:
                mismatch_dict = dict(mismatch)
                # Analyze the reason for mismatch
                if mismatch_dict not in edges1 and mismatch_dict in edges2:
                    print(f"Extra edge in file2: {mismatch_dict}")
                elif mismatch_dict in edges1 and mismatch_dict not in edges2:
                    print(f"Missing edge in file2: {mismatch_dict}")
                else:
                    print(f"Edge mismatch due to unknown reason: {mismatch_dict}")

    # Summary of comparison
    print("\nComparison Summary:")
    print(f"Total edges in file1: {total_edges_file1}")
    print(f"Total edges in file2: {total_edges_file2}")
    print(f"Matching edges: {matching_edges}")
    print(f"Mismatched edges: {mismatched_edges}")

# Paths to the two JSON files
file1_path = "sw_graph.json"
file2_path = "hw_graph.json"

# Run the comparison
compare_edges(file1_path, file2_path)
