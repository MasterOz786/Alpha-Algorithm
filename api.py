import google.generativeai as genai
import os
import typing_extensions as typing
from file_handler import extract_text_from_file

genai.configure(api_key=os.getenv("API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")
# model = genai.GenerativeModel("gemini-pro")
# chat = model.start_chat()

messages = []
task1_prompt = "Analyze the given process description and generate event logs such that thecy can be further used in the creation of Petri Nets and to be added noise and then Alpha Algorithm can be applied on it. Make sure that you generate the output in the form of events labeled as A, B, etc. Also, separate the events and label them with their process descriptions. Make the events atomic. Establish concurrency and dependencies between events based on the process description. The response should generate a list of JSON objects, each containing an event, its description, casual relations with other elements. Make sure that the transitions are well covered and highlighted in the response."

process_description = extract_text_from_file()
messages.append({
    "role": "user",
    "parts": [task1_prompt + "Here is the process description: " + process_description]
})

class EventLog(typing.TypedDict):
    event: str
    description: str
    
response = model.generate_content(
    messages, 
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json", response_schema=list[EventLog]
    )                              
)

messages.append({
    "role": "model", 
    "parts": [response.text]
})

print("Model:", response.text)