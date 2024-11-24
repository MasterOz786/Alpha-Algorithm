import google.generativeai as genai
from file_handler import read_file_content
import json
from collections import Counter
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyArrowPatch

# Configure the Generative AI model
genai.configure(api_key="AIzaSyBS-Y7NDy3dErTDszUFsHLOXxN8XX0X9d0")
model = genai.GenerativeModel("gemini-1.5-flash")

# Define the path to the file you want to read
file_path = "H:/5th Semester/Process Mining/PM/Alpha-Algorithm/description1.txt"  # Customize the path as needed

# User inputs
num_traces = input("Enter the number of traces: ")
amount_noise = input("Enter the amount of noise: ")
freq_uncommon_paths = input("Enter the frequency of uncommon paths: ")
likelihood_missing_events = input("Enter the likelihood of missing events: ")

# Read the process description from the specified file
process_description = read_file_content(file_path)

# Prompts for the Generative AI model
task1_prompt_output1 = f"""
    Analyze the given process description and generate event logs such that they can be further used in the creation of Petri Nets and to be added noise and then Alpha Algorithm can be applied on it. Now I want you to give me 3 kinds of output. For output 2 & 3 here are some values:
        process description: {process_description}
        number of traces: {num_traces}
        amount of noise: {amount_noise}
        frequency of uncommon paths: {freq_uncommon_paths}
        likelihood of missing events: {likelihood_missing_events}

    Output 1:
    A singular list of JSON objects that contains for each transition a label (A, B, etc.), a description (which transition is this), pre transitions (which transition comes right before this, like if the current transition is C and the transition immediately before it is B & A), and post transitions (like D). 
    Keep the key named as event_log for consistency. Make sure that data format is as follows: {{"first_event_logs": [{{"trace": [{{"transition": "ABC", "description": "abc", "pre_transitions": ["A"], "post_transitions": ["B", "C"]}}]}}]
"""

task1_prompt_output2 = f"""
    Generate a list of JSON objects representing *all possible valid event logs* for the E-Commerce Order Fulfillment process described below. Each event log should contain:
      - A trace key, which is an ordered list of transitions (e.g., ["A", "B", "C", "D"]).
      - A tag key with the value "Valid".
      - A frequency key indicating how often this trace occurs.

    Requirements:
      - Each log must be formatted clearly, for example:
        {{
          "trace": ["A", "B", "C", "D"],
          "tag": "Valid",
          "frequency": x  => a number
        }},
        {{
          "trace": ["A", "C", "B", "D"],
          "tag": "Valid",
          "frequency": y  => a number
        }}

    Use the key second_event_logs as the container for the output. Ensure consistent formatting and valid sequences based on the transitions provided in the process description.
"""


task1_prompt_output3 = """
    Output 3:
    A list of JSON objects that contain only invalid event logs like [{D, B, C, A}, {A, D, B, D}] etc. Each event log should contain a tag like (Invalid) and mention the frequency of each log. Keep the above-mentioned parameters in mind (number of traces, amount of noise, frequency of uncommon paths,
    and likelihood of missing events).
    Make sure that the response is as follows: {{"third_event_logs": [{{"trace": [{{"transition": "ABC", "tag": "Invalid", "frequency": 2}}]}}]}}
"""

# Construct the message with the process description
messages = []
responses = []

messages.append({
    "role": "user",
    "parts": [task1_prompt_output1 + "\nHere is the process description:\n" + process_description]
})

# Generate the first response
response = model.generate_content(
    messages, 
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )                              
)

# Append the model's response to messages and responses
messages.append({
    "role": "model", 
    "parts": [response.text]
})
responses.append(response.text)

# Second user prompt for output 2
messages.append({
    "role": "user",
    "parts": [task1_prompt_output2]
})

# Generate the second response
response = model.generate_content(
    messages, 
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )                              
)
messages.append({
  "role": "model", 
  "parts": [response.text]
})
responses.append(response.text)

# Second user prompt for output 3
messages.append({
  "role": "user",
  "parts": [task1_prompt_output3]
})

# Generate the second response
response = model.generate_content(
    messages, 
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )                              
)
responses.append(response.text)

expanded_logs = []

# Filter and display only valid logs
for response in responses:
    response = json.loads(response)
    if "second_event_logs" in response:
        for log in response["second_event_logs"]:
            expanded_logs.extend([", ".join(log["trace"])] * log["frequency"])

# STEP1: Display Final Log (L) with Correct Format
print("STEP1: ")
print("-" * 50)
print("Final Log (L)")
print("-" * 50)
print("{")
# Step 1: Convert logs to unique traces with their frequencies
unique_traces = Counter(expanded_logs)
for trace, frequency in unique_traces.items():
    # Display each trace as a list (formatted as per requirement)
    print(f"    {list(trace.split(', '))}, Frequency: {frequency}")
print("}")
print("-" * 50)

# STEP2: Extract and Sort Unique Events (TL), Initial Events (TI), and Final Events (TO)
# Extract all unique events (TL) and sort them alphabetically
all_events = set()
for trace in unique_traces:
    for event in trace.split(", "):
        all_events.add(event)

all_events = sorted(list(all_events))  # Sort alphabetically

# Initial Events (TI): First event in the sorted unique events
TI = [all_events[0]]  # First event in the sorted list

# Final Events (TO): Last event in the sorted unique events
TO = [all_events[-1]]  # Last event in the sorted list

# Display STEP2 Output
print("STEP2: ")
print("-" * 50)
print("Unique Events (TL):", all_events)
print("Initial Events (TI):", TI)
print("Final Events (TO):", TO)
print("-" * 50)





# Step 3: Determining Relationships (Causal, Parallel, Choice)
print("\nSTEP3: Determining Relationships")
print("-" * 50)

# Updated helper function to check if event 'x' directly precedes event 'y' in a trace
def precedes_directly(trace, x, y):
    events = trace.split(", ")
    try:
        x_index = events.index(x)
        return x_index + 1 < len(events) and events[x_index + 1] == y  # Check y directly follows x
    except ValueError:
        return False  # If x or y not in trace

# Initialize relationships dictionaries
causal_relationships = {}
parallel_relationships = {}
choice_relationships = {}

for event1 in all_events:
    for event2 in all_events:
        if event1 != event2:
            causal_found, parallel_found = False, False
            for trace in expanded_logs:
                if precedes_directly(trace, event1, event2):
                    causal_found = True
                if precedes_directly(trace, event2, event1):
                    parallel_found = True
            
            if causal_found and not parallel_found:
                causal_relationships.setdefault(event1, []).append(event2)
            elif parallel_found and causal_found:
                parallel_relationships.setdefault(event1, []).append(event2)
            elif not causal_found and not parallel_found:
                choice_relationships.setdefault(event1, []).append(event2)

# Display Relationships
print("Causal Relationships:")
for event, related_events in causal_relationships.items():
    for related_event in related_events:
        print(f"{event} -> {related_event}")  # Display each relationship on a new line

print("\nParallel Relationships:")
seen_pairs = set()  # To track displayed pairs and avoid redundant relationships

for event1, related_events in parallel_relationships.items():
    for event2 in related_events:
        if (event1, event2) not in seen_pairs and (event2, event1) not in seen_pairs:
            # Print both directions of the relationship
            print(f"{event1} || {event2}")
            print(f"{event2} || {event1}")
            # Mark the pair as seen
            seen_pairs.add((event1, event2))
            seen_pairs.add((event2, event1))


print("\nChoice Relationships:")
for event, related_events in choice_relationships.items():
    for related_event in related_events:
        print(f"{event} # {related_event}")  # Display each relationship on a new line

print("-" * 50)







# Step 4: Footprint Matrix
print("\nSTEP4: Footprint Matrix")
print("-" * 50)

# Create the footprint matrix (a dictionary of dictionaries)
footprint_matrix = {}
for event1 in sorted(all_events):  # Sort events alphabetically
    footprint_matrix[event1] = {}
    for event2 in sorted(all_events):  # Sort events alphabetically
        footprint_matrix[event1][event2] = ""

# Fill in the matrix based on the relationships
for event1 in sorted(all_events):
    for event2 in sorted(all_events):
        if event1 != event2:
            if event2 in causal_relationships.get(event1, []):
                # Only add "->" if NOT a parallel relationship
                if event1 not in parallel_relationships.get(event2, []): 
                    footprint_matrix[event1][event2] = "->"
                    footprint_matrix[event2][event1] = "<-"  # Add reverse causal relationship
            elif event2 in parallel_relationships.get(event1, []):
                footprint_matrix[event1][event2] = "||"
            elif event2 in choice_relationships.get(event1, []):
                footprint_matrix[event1][event2] = "#"
        else:  # Self-relationship is a choice
            footprint_matrix[event1][event2] = "#"

# Display the Footprint Matrix with vertical dash lines to separate columns
print("-" * 50)
print("   |", end="")  # Add extra space for column header with initial separator
for event in sorted(all_events):  # Sort events alphabetically for column header
    print(f" {event} |", end="")  # Add '|' after each header element
print()
print("-" * 50)

for event1 in sorted(all_events):
    print(f"{event1} |", end="")  # Start each row with the event name and '|'
    for event2 in sorted(all_events):
        print(f" {footprint_matrix[event1][event2]} |", end="")  # Add '|' after each matrix cell
    print()  # Move to the next line after each row
    print("-" * 50)  # Row separator
    



# Step 5: Generate Pair Sets of Causal Relationships Only
print("\nSTEP5: Causal Pair Sets")
print("-" * 50)

# Collect and display causal pairs in the required notation
causal_pairs = []
for event, related_events in causal_relationships.items():
    for related_event in related_events:
        causal_pairs.append(f"({{{event}, {related_event}}})")

# Display each causal pair set on a new line
for pair in causal_pairs:
    print(pair)
print("-" * 50)


# Step 6: Displaying Maximal Relationship Pairs
print("\nSTEP6: Maximal Relationship Pairs")
print("-" * 50)

# Collect both maximal 
all_causal_pairs = []

# Helper function to add causal pairs to the list
def add_causal_pair(causal_dict):
    for event, related_events in causal_dict.items():
        if len(related_events) > 1:  # Maximal causal relationship
            all_causal_pairs.append(f"({{{event}}}, {{{', '.join(related_events)}}})")
        else:  # Non-maximal causal relationship
            for related_event in related_events:
                all_causal_pairs.append(f"({{{event}}}, {{{related_event}}})")

# Add all pairs from causal relationships
add_causal_pair(causal_relationships)

# Display each causal pair in the required format, including both maximal and non-maximal
for pair in all_causal_pairs:
    print(pair)
print("-" * 50)




# Step 7: Place Set (PL) for Maximal Causal Pairs
print("\nSTEP7: Place Set (PL) Maximal Causal Pairs")
print("-" * 50)

# Collect and display Place Sets for non-maximal causal pairs
non_maximal_pairs = []

# Check non-maximal relationships and generate place sets
for event, related_events in causal_relationships.items():
    if len(related_events) > 1:  # Skip maximal pairs, only non-maximal pairs
        # Non-maximal relationships that have more than one related event
        non_maximal_pairs.append(f"P({{{event}}}, {{{', '.join(related_events)}}})")
    else:  # Handle individual non-maximal relationships (i.e., only one event related)
        for related_event in related_events:
            non_maximal_pairs.append(f"P({{{event}}}, {{{related_event}}})")

# Display each place set in the required format
for place_set in non_maximal_pairs:
    print(place_set)

print("-" * 50)




# Step 8: Flow Relation for Maximal Causal Pairs
print("\nSTEP8: Flow Relation for Maximal Causal Pairs")
print("-" * 50)

# Generate and display Flow Relation
flow_relations = []

# Iterate through maximal causal pairs generated in STEP7
for pair in all_causal_pairs:
    # Extract the source and target parts of each causal pair
    pair = pair.replace("(", "").replace(")", "").replace("{", "").replace("}", "").split(", ")
    source = pair[0]
    targets = pair[1:]

    # First, add the direct flow from the source to the place set
    place_set = f"P({source}, {{ {', '.join(targets)} }})"
    flow_relations.append(f"({source}, {place_set})")

    # Then, add flows from the place set to each target
    for target in targets:
        flow_relations.append(f"({place_set}, {target})")

# Display each flow relation in the required format
for relation in flow_relations:
    print(relation)

print("-" * 50)



# Step 9: Extract Transitions, Places, and Flow Relations
print("\nSTEP9: Extract Transitions, Places, and Flow Relations")
print("-" * 50)

# Transition extraction: These are the unique events we extracted in Step 2 (all_events)
transitions = all_events
print("Transitions:")
print(transitions)

# Place extraction: These are the Place Sets derived in Step 7
places = non_maximal_pairs
print("\nPlaces:")
for place in places:
    print(place)

# Reusing flow relations from Step 8
print("\nFlow Relations:")
for flow in flow_relations:
    print(flow)

print("-" * 50)



# Step 10: Visualize Petri Net
print("\nSTEP10: Visualize Petri Net")
print("-" * 50)

# Create the graph for Petri Net visualization
G = nx.DiGraph()

# Define transitions and places as you already did
transitions = list(all_events)  # transitions (events)
places = []  # will store places as (pre, post) pairs
for event1 in all_events:
    for event2 in all_events:
        if event1 != event2 and event2 in causal_relationships.get(event1, []):
            places.append((event1, event2))  # Place between event1 and event2

# Add transitions and places to the graph
for transition in transitions:
    G.add_node(transition, shape='rectangle')

for place in places:
    place_name = f"P({{{place[0]}}}, {{{place[1]}}})"
    G.add_node(place_name, shape='circle')

# Add edges between places and transitions
for event1 in all_events:
    for event2 in all_events:
        if event1 != event2 and event2 in causal_relationships.get(event1, []):
            place_name = f"P({{{event1}}}, {{{event2}}})"
            G.add_edge(event1, place_name)
            G.add_edge(place_name, event2)

# Generate positions for the nodes using a spring layout
pos = nx.spring_layout(G, seed=42)

# Draw the Petri Net with custom node shapes and labels
plt.figure(figsize=(10, 8))

# Draw transitions (rectangles)
transition_nodes = [node for node in G.nodes if G.nodes[node]['shape'] == 'rectangle']
nx.draw_networkx_nodes(G, pos, nodelist=transition_nodes, node_shape='s', node_color='skyblue', node_size=2000, label="Transitions")

# Draw places (circles)
place_nodes = [node for node in G.nodes if G.nodes[node]['shape'] == 'circle']
nx.draw_networkx_nodes(G, pos, nodelist=place_nodes, node_shape='o', node_color='lightgreen', node_size=3000, label="Places")

# Draw edges
nx.draw_networkx_edges(G, pos, width=2, alpha=0.6, edge_color='black')

# Draw node labels
labels = {node: node for node in G.nodes}
nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold')

# Add the legend
plt.legend(loc='upper left', fontsize=10)

# Display the plot
plt.title("Petri Net Representation")
plt.axis('off')
plt.show()