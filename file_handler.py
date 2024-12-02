import tkinter as tk
from tkinter import filedialog
import os

# Function to read file content based on file type
def read_file_content(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    content = ""
    
    # Check file type and read accordingly
    if ext == ".txt":
        with open(filepath, 'r') as file:
            content = file.read()
    elif ext == ".md":
        with open(filepath, 'r') as file:
            content = file.read()
    else:
        raise ValueError("Unsupported file format.")
    return content

# Open file dialog to select a file
def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[("Text files", "*.txt"), ("Word documents", "*.docx"), ("Markdown files", "*.md")]
    )
    
    if file_path:
        return file_path
    else:
        print("No file selected.")
        return None


def extract_text_from_file():
    # Ask user to select a file
    file_path = select_file()
    if file_path:
        # Read file content
        task1_prompt = read_file_content(file_path)
        return task1_prompt
    
    return None

if __name__ == "__main__":
    extract_text_from_file()
