
## Wrapper for double clickable :

import sys
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import threading

# Import your processing function
from bom_processor import process_images

def select_folder():
    root = tk.Tk()
    root.withdraw()  # Hide main window
    folder_path = filedialog.askdirectory(title="Select folder with images")
    root.destroy()
    return folder_path

def run_processing(input_folder):
    try:
        # Update status in GUI (must use .after from main thread)
        window.after(0, lambda: status_label.config(text="Processing... Please wait."))

        # Find model path near the executable or script
        model_path = os.path.join(os.path.dirname(sys.executable), 'my_yolo_model_1.pt')
        if not os.path.exists(model_path):
            model_path = os.path.join(os.path.dirname(__file__), 'my_yolo_model_1.pt')

        # Call the actual processing
        process_images(input_folder, model_path)

        # After processing, update GUI status
        result_path = os.path.join(input_folder, 'cropped_bom')
        msg = f"✅ Processing complete!\nResults saved in:\n{result_path}"
        window.after(0, lambda: status_label.config(text=msg))

    except Exception as e:
        # In case of errors, show in GUI
        window.after(0, lambda: status_label.config(text=f"❌ Error: {str(e)}"))

def process_button_click():
    input_folder = select_folder()
    if input_folder:
        status_label.config(text=f"Selected folder:\n{input_folder}")
        thread = threading.Thread(target=run_processing, args=(input_folder,))
        thread.start()
    else:
        status_label.config(text="⚠️ No folder selected.")

# GUI setup
window = tk.Tk()
window.title("BOM Table Extractor")
window.geometry("450x250")

title_label = tk.Label(window, text="📄 Table Detection & Extraction", font=("Arial", 16))
title_label.pack(pady=15)

process_button = tk.Button(window, text="📂 Select Images Folder", command=process_button_click, height=2, width=25)
process_button.pack(pady=10)

status_label = tk.Label(window, text="Ready to process images", font=("Arial", 10), wraplength=400, justify="center")
status_label.pack(pady=10)

window.mainloop

