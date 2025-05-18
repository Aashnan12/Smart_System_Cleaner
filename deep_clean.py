import tkinter as tk
from tkinter import ttk, messagebox
import os
from utils import secure_delete
import threading

def setup_deep_clean_tab(frame):
    ttk.Label(frame, text="Select File or Folder for Deep Cleaning", font=('Helvetica', 14, 'bold')).pack(pady=10)
    path_entry = ttk.Entry(frame, width=60)
    path_entry.pack(pady=5)
    browse_frame = ttk.Frame(frame)
    browse_frame.pack(pady=5)
    ttk.Button(browse_frame, text="Browse File", command=lambda: browse_file(path_entry)).grid(row=0, column=0, padx=5)
    ttk.Button(browse_frame, text="Browse Folder", command=lambda: browse_folder(path_entry)).grid(row=0, column=1, padx=5)
    deep_clean_button = ttk.Button(frame, text="Start Deep Clean", command=lambda: threading.Thread(target=start_deep_clean, args=(path_entry, deep_clean_button, progress)).start())
    deep_clean_button.pack(pady=10)

    progress = ttk.Progressbar(frame, length=300, mode='indeterminate')
    progress.pack(pady=5)

def browse_file(path_entry):
    file_path = tk.filedialog.askopenfilename()
    if file_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, file_path)
        messagebox.showinfo("Selected", f"Selected file: {file_path}")

def browse_folder(path_entry):
    dir_path = tk.filedialog.askdirectory()
    if dir_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, dir_path)
        messagebox.showinfo("Selected", f"Selected folder: {dir_path}")

def start_deep_clean(path_entry, deep_clean_button, progress):
    path = path_entry.get()
    if not path or not os.path.exists(path):
        messagebox.showerror("Error", "Please select a valid file or folder.")
        return
    if messagebox.askyesno("Confirm", f"Permanently erase {path}? This is irreversible."):
        deep_clean_button.config(state='disabled')
        progress.start()
        try:
            secure_delete(path)
            messagebox.showinfo("Success", "Deep cleaning completed.")
        except Exception as e:
            messagebox.showerror("Error", f"Deep cleaning failed: {str(e)}")
        finally:
            progress.stop()
            deep_clean_button.config(state='normal')