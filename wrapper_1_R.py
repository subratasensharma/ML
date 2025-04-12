
## Wrapper for double clickable :

import os
import sys
import tkinter as tk
from tkinter import filedialog
import threading
from bom_processor import process_images

def select_folder():
    folder = filedialog.askdirectory(title="Select folder with images")
    return folder

def run_processing(input_folder, model_path):
    try:
        process_images(input_folder, model_path)
        status_label.config(text=f"✅ Processing complete!\nResults saved in:\n{os.path.join(input_folder, 'cropped_bom')}")
    except Exception as e:
        status_label.config(text=f"❌ Error: {str(e)}")

def process_button_click():
    status_label.config(text="🔄 Processing... Please wait.")
    window.update()

    input_folder = select_folder()
    if not input_folder:
        status_label.config(text="⚠️ No folder selected.")
        return

    # Find the model path relative to executable or script
    model_path = os.path.join(os.path.dirname(sys.executable), 'my_yolo_model_1.pt')
    if not os.path.exists(model_path):
        model_path = os.path.join(os.path.dirname(__file__), 'my_yolo_model_1.pt')

    # Run processing in a background thread to avoid GUI freezing
    thread = threading.Thread(target=run_processing, args=(input_folder, model_path))
    thread.start()

# GUI setup
window = tk.Tk()
window.title("BOM Table Extractor")
window.geometry("420x250")
"""
title_label = tk.Label(window, text="🧾 Table Detection & Extraction", font=("Arial", 16))
title_label.pack(pady=20)
"""
process_button = tk.Button(window, text="Select Images Folder", command=process_button_click, height=2, width=25)
process_button.pack(pady=10)

status_label = tk.Label(window, text="Ready to process images", font=("Arial", 11))
status_label.pack(pady=15)

window.mainloop()
