
#!/usr/bin/env python3
import sys
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import threading

# Import your processing function
from bom_processor import process_images

def select_folder():
    input_folder = filedialog.askdirectory(title="Select folder")
    print('.....................................................')
    print("Selected folder:", input_folder)
    return input_folder

def run_processing(input_folder, model_path):

    # Call the actual processing
    process_images(input_folder, model_path)

def on_click():
    input_folder = select_folder()
    # Find model path near the executable or script
    model_path = os.path.join(os.path.dirname(sys.executable), 'my_yolo_model_1.pt')
    if not os.path.exists(model_path):
        model_path = os.path.join(os.path.dirname(__file__), 'my_yolo_model_1.pt')
    # Run processing in a background thread to avoid GUI freezing
    thread = threading.Thread(target=run_processing, args=(input_folder, model_path))
    thread.start()

window = tk.Tk()
window.title("Test GUI")
window.geometry("300x150")

button = tk.Button(window, text="Pick Folder", command=on_click)
button.pack(pady=30)

window.mainloop()
