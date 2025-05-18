import tkinter as tk
from tkinter import ttk, messagebox
import os
import hashlib
import send2trash
import threading

def setup_cleanup_tab(frame):
    # Temporary Files
    ttk.Label(frame, text="Temporary Files", font=('Helvetica', 14, 'bold')).grid(row=0, column=0, sticky='w', padx=10, pady=10)
    temp_size_label = ttk.Label(frame, text="Size: 0 MB")
    temp_size_label.grid(row=0, column=1, padx=10, pady=10)
    scan_button = ttk.Button(frame, text="Scan", command=lambda: threading.Thread(target=scan_temp_files, args=(temp_size_label, scan_button)).start())
    scan_button.grid(row=0, column=2, padx=10, pady=10)
    delete_button = ttk.Button(frame, text="Delete", command=lambda: threading.Thread(target=delete_temp_files, args=(temp_size_label, delete_button)).start())
    delete_button.grid(row=0, column=3, padx=10, pady=10)

    # Duplicate Files
    ttk.Label(frame, text="Duplicate Files", font=('Helvetica', 14, 'bold')).grid(row=1, column=0, sticky='w', padx=10, pady=10)
    dup_dir_entry = ttk.Entry(frame, width=50)
    dup_dir_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10)
    browse_button = ttk.Button(frame, text="Browse", command=lambda: browse_dup_dir(dup_dir_entry))
    browse_button.grid(row=1, column=3, padx=10, pady=10)
    scan_dup_button = ttk.Button(frame, text="Scan", command=lambda: threading.Thread(target=scan_dup_files, args=(dup_dir_entry, dup_tree, scan_dup_button)).start())
    scan_dup_button.grid(row=2, column=0, padx=10, pady=10)
    dup_tree = ttk.Treeview(frame, columns=('Size',), selectmode='extended', height=10)
    dup_tree.grid(row=3, column=0, columnspan=3, padx=10, pady=10)
    dup_tree.heading('#0', text='File Path')
    dup_tree.heading('Size', text='Size (MB)')
    delete_dup_button = ttk.Button(frame, text="Delete Selected", command=lambda: delete_selected_dup(dup_tree))
    delete_dup_button.grid(row=3, column=3, padx=10, pady=10)

def scan_temp_files(temp_size_label, scan_button):
    scan_button.config(state='disabled')
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp') if os.name == 'nt' else '/tmp')
    total_size = 0
    if os.path.exists(temp_dir):
        for root, _, files in os.walk(temp_dir):
            for file in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                except (OSError, PermissionError):
                    continue
    temp_size_label.config(text=f"Size: {total_size / (1024*1024):.2f} MB")
    scan_button.config(state='normal')

def delete_temp_files(temp_size_label, delete_button):
    delete_button.config(state='disabled')
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp') if os.name == 'nt' else '/tmp')
    if os.path.exists(temp_dir):
        for root, _, files in os.walk(temp_dir):
            for file in files:
                try:
                    send2trash.send2trash(os.path.join(root, file))
                except (OSError, PermissionError):
                    continue
    scan_temp_files(temp_size_label, delete_button)
    delete_button.config(state='normal')

def browse_dup_dir(dup_dir_entry):
    dir_path = tk.filedialog.askdirectory()
    if dir_path:
        dup_dir_entry.delete(0, tk.END)
        dup_dir_entry.insert(0, dir_path)
        messagebox.showinfo("Selected", f"Selected directory: {dir_path}")

def scan_dup_files(dup_dir_entry, dup_tree, scan_dup_button):
    scan_dup_button.config(state='disabled')
    dir_path = dup_dir_entry.get()
    if not dir_path or not os.path.exists(dir_path):
        messagebox.showerror("Error", "Please select a valid directory.")
        scan_dup_button.config(state='normal')
        return
    for item in dup_tree.get_children():
        dup_tree.delete(item)
    file_hashes = {}
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash in file_hashes:
                    file_hashes[file_hash].append(file_path)
                else:
                    file_hashes[file_hash] = [file_path]
            except (OSError, PermissionError):
                continue
    for file_hash, paths in file_hashes.items():
        if len(paths) > 1:
            for path in paths:
                size = os.path.getsize(path) / (1024*1024)
                dup_tree.insert('', 'end', text=path, values=(f"{size:.2f}",))
    scan_dup_button.config(state='normal')

def delete_selected_dup(dup_tree):
    selected = dup_tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "No duplicates selected.")
        return
    if messagebox.askyesno("Confirm", "Delete selected duplicates?"):
        for item in selected:
            file_path = dup_tree.item(item, 'text')
            try:
                send2trash.send2trash(file_path)
                dup_tree.delete(item)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {file_path}: {str(e)}")