
## Wrapper for double clickable :

import tkinter as tk
from tkinter import filedialog

def select_folder():
    root = tk.Tk()
    root.withdraw()  # Don't show the empty main window
    folder_selected = filedialog.askdirectory(title="Select folder with images")
    root.destroy()
    return folder_selected

# Test it
folder_path = select_folder()
print("You selected:", folder_path)