import google.generativeai as genai
import typing_extensions as typing
from file_handler import extract_text_from_file

# Configure the Generative AI model
genai.configure(api_key="AIzaSyBS-Y7NDy3dErTDszUFsHLOXxN8XX0X9d0")
model = genai.GenerativeModel("gemini-1.5-flash")

# Ask the user for input values
num_traces = input("Enter the number of traces: ")
amount_noise = input("Enter the amount of noise: ")
freq_uncommon_paths = input("Enter the frequency of uncommon paths: ")
likelihood_missing_events = input("Enter the likelihood of missing events: ")

# Create the prompt with the user-provided values
task1_prompt = f"""Analyze the given process description and generate event logs such that they can be further used in the creation of Petri Nets and to be added noise and then Alpha Algorithm can be applied on it. Now i want you to give me 2 kinds of output. for output 2 here are some values:
number of traces: {num_traces}
amount of noise: {amount_noise}
frequency of uncommon paths: {freq_uncommon_paths}
likelihood of missing events: {likelihood_missing_events}

Output 1:
A singular list of JSON objects that contains for each transition a label (A, B etc), a description (which transition is this), pre transitions (which transition comes right before this like if the current transition is C and the transition immediately before it is B & A), post transitions (like D).

Output 2:
a list of JSON objects that contain all possible event logs like [{A, B, C, D}, {A, C, B, D}] etc. each even log should contain a tag like (Valid or Invalid). Because i want you to generate invalid logs as well like [{A,D}, {A, C, D}] and mention the frequency of each log. Keep the above mentioned parameters in mind (number of traces, amount of noise, frequency of uncommon paths,
and likelihood of missing events)

Return both outputs
"""

# Extract the process description from a file
process_description = extract_text_from_file()
messages = [{
    "role": "user",
    "parts": [task1_prompt + "Here is the process description: " + process_description]
}]

# Generate content based on the prompt
response = model.generate_content(
    messages, 
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )                              
)

# Append and print the response
messages.append({
    "role": "model", 
    "parts": [response.text]
})
print(response.text)
