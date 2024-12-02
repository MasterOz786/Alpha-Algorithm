
import google.generativeai as genai
import json
from datetime import datetime
from collections import Counter
from graphviz import Digraph
from file_handler import extract_text_from_file

# Configure the Generative AI model
genai.configure(api_key="AIzaSyAUL1ydoXAa6de-0ks33CGMhfHuRU9mlfU")
model = genai.GenerativeModel("gemini-1.5-flash")

# Define the path to the file you want to read
# file_path = "description1.txt"  # Customize the path as needed
# User inputs
num_traces = input("Enter the number of traces: ")
amount_noise = input("Enter the amount of noise: ")
freq_uncommon_paths = input("Enter the frequency of uncommon paths: ")
likelihood_missing_events = input("Enter the likelihood of missing events: ")

# Read the process description from the specified file
process_description = extract_text_from_file()

# Prompts for the Generative AI model
task1_prompt_output1 = f"""
    Analyze the given process description and generate event logs such that they can be further used in the creation of Petri Nets and to be added noise and then Alpha Algorithm can be applied on it. Now I want you to give me 3 kinds of output. For output 2 & 3 here are some values:
        process description: {process_description}
        number of traces: {num_traces}
        amount of noise: {amount_noise}
        frequency of uncommon paths: {freq_uncommon_paths}
        likelihood of missing events: {likelihood_missing_events}

    Output 1:
    A singular list of JSON objects that contains for each transition a label (A, B, etc.), name (without a space), pre transitions (which transition comes right before this, like if the current transition is C and the transition immediately before it is B & A), and post transitions (like D). 
    Keep the key named as event_log for consistency. Make sure that data format is as follows: {{"first_event_logs": [{{"trace": [{{"transition": "ABC", "name": "abc", "pre_transitions": ["A"], "post_transitions": ["B", "C"]}}]}}]
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

# make a letter and name dictionary
activities = {}
for t in json.loads(response.text)["first_event_logs"][0]["trace"]:
    activities[t["transition"]] = t["name"]

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
    if "third_event_logs" in response:
        for log in response["third_event_logs"]:
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
        else:  # -relationship is a choice
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

# Flow relation extraction: These are the Flow Relations generated in Step 8
print("\nFlow Relations:")
for relation in flow_relations:
    print(relation)

# Step 10: Visualize Petri Net
# Side Step: Convert the Flow Relations for compatibility with Graphviz Code
flow_relations_format_prompt = f"""
    Output should be a single json object with a key 'flow_relations' and the value as the converted format.
    Only give the output in the array of arrays format and each array should contain 2 elements. Each element should only be a string and not encloded in parenthesis or brackets or anything else. They should be singular characters to represent the flow relations. Make sure no additional flow relation is added. Also make sure that the given flow relations are accurately converted in the format specified.

    Convert the flow relations {flow_relations}.
    Example:
    {{"flow_relations": [[source, dest], [source, dest]]}}
    
"""

messages.append({
    "role": "user",
    "parts": [flow_relations_format_prompt]
})

# Generate the response for the flow relations
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
flow_relations = json.loads(response.text)['flow_relations']

markings_places_format_prompt = f"""
    Only give the output in the array of arrays format and each array should contain 2 elements. Each element should only be a string and not encloded in parenthesis or brackets or anything else. They should be singular characters to represent the places. Make sure no additional flow relation is added. Also make sure that the given places are accurately converted in the format specified. Output should be a single json object with a key 'places' and the value as the converted format.

    Convert the places {places}.
    Example:
    {{"places": [[A, B], [B, C]]}}

    Also add key for initial_markings and final_markings.
"""

messages.append({
    "role": "user",
    "parts": [markings_places_format_prompt]
})

# Generate the response for the places
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
markings_places = json.loads(response.text)

styles = {
    'transition': {
        'shape': 'rectangle',
        'style': 'filled',
        'fillcolor': 'lightgreen',
        'height': '0.6',
        'width': '1.2',
        'fontname': 'Arial'
    },
    'place': {
        'shape': 'circle',
        'style': 'filled',
        'fillcolor': 'lightblue',
        'height': '0.6',
        'width': '0.6',
        'fontname': 'Arial'
    },
    'initial_place': {
        'shape': 'circle',
        'style': 'filled',
        'fillcolor': 'lightgray',
        'height': '0.6',
        'width': '0.6',
        'peripheries': '2',
        'fontname': 'Arial'
    },
    'final_place': {
        'shape': 'circle',
        'style': 'filled',
        'fillcolor': 'lightpink',
        'height': '0.6',
        'width': '0.6',
        'peripheries': '2',
        'fontname': 'Arial'
    }
}

print("\nSTEP10: Visualize Petri Net")
print("-" * 50)

petri_net = {
    "places": markings_places['places'],
    "transitions": transitions,
    "initial_markings": markings_places['initial_markings'],
    "final_markings": markings_places['final_markings'],
    "flow_relations": flow_relations
}

""" Replace letters with actual activity names """
# for i, place in enumerate(petri_net['places']):
#     petri_net['places'][i] = [activities[p] for p in place]

# for i, t in enumerate(petri_net['transitions']):
#     petri_net['transitions'][i] = activities[t]

# for i, m in enumerate(petri_net['initial_markings']):
#     petri_net['initial_markings'][i] = activities[m]

# for i, m in enumerate(petri_net['final_markings']):
#     petri_net['final_markings'][i] = activities[m]

# for i, f in enumerate(petri_net['flow_relations']):
#     print(i, f)
#     # petri_net['flow_relations'][i] = [activities[f[0]], activities[f[1]]]



dot = Digraph(comment='Petri Net Visualization')
dot.attr(rankdir='LR')  # Left to Right layout
dot.attr('node', fontsize='12')
dot.attr('edge', fontsize='10')

# Add initial place
dot.node('start', '', styles['initial_place'])

# Add final place
dot.node('end', '', styles['final_place'])

# Add transitions
for t in petri_net['transitions']:
    """  DONT UNCOMMENT! The code blasts on labeling transitions  """ 
    # t = activities[t]
    dot.node(f"T_{t}", t, styles['transition'])
    
# Add places for each flow relation
seen_places = set()
for source, target in petri_net["flow_relations"]:
    place_id = f"P_{source}_{target}"
    if place_id not in seen_places:
        dot.node(place_id, '', styles['place'])
        seen_places.add(place_id)

# Add edges for initial transitions
for t in petri_net['initial_markings']:
    dot.edge('start', f"T_{t}")
    
# Add edges for final transitions
for t in petri_net['final_markings']:
    dot.edge(f"T_{t}", 'end')
    
# Add edges for flow relations
for source, target in petri_net["flow_relations"]:
    place_id = f"P_{source}_{target}"
    dot.edge(f"T_{source}", place_id)
    dot.edge(place_id, f"T_{target}")

# Add a legend
legend = Digraph('cluster_legend')
legend.attr(label='Legend', labeljust='l')

# Add legend items
legend.node('L_trans', 'Activity', **styles['transition'])
legend.node('L_place', 'Place', **styles['place'])
legend.node('L_init', 'Start', **styles['initial_place'])
legend.node('L_final', 'End', **styles['final_place'])

# Arrange legend items vertically
legend.attr(rankdir='TB')

combined = Digraph()
combined.attr(rankdir='LR')

with combined.subgraph(name='cluster_main') as main:
    main.attr(label='Process Model')
    for line in dot.body:
        main.body.append(line)

with combined.subgraph(name='cluster_legend') as leg:
    for line in legend.body:
        leg.body.append(line)

# Save with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"graph_{timestamp}"

# Render in multiple formats
combined.render(output_filename, format='png', cleanup=True)
combined.render(output_filename, format='pdf', cleanup=True)

print(f"Visualization saved as '{output_filename}.png' and '{output_filename}.pdf'")
print("-" * 50)
