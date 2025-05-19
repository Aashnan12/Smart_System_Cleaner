import tkinter as tk
from tkinter import ttk, messagebox
import os
import hashlib
import send2trash
import threading
from collections import defaultdict

def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_duplicate_files(paths):
    """Find files with same content but different names."""
    hash_map = defaultdict(list)
    for path in paths:
        try:
            file_hash = calculate_file_hash(path)
            hash_map[file_hash].append(path)
        except (OSError, PermissionError):
            continue
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

def find_same_name_files(base_path, filename):
    """Find all files with the same name across directories."""
    same_name_files = []
    for root, _, files in os.walk(base_path):
        if filename in files:
            same_name_files.append(os.path.join(root, filename))
    return same_name_files

def setup_cleanup_tab(frame):
    # Temporary Files section
    temp_frame = ttk.LabelFrame(frame, text="Temporary Files", padding=10)
    temp_frame.grid(row=0, column=0, columnspan=4, sticky='nsew', padx=10, pady=5)
    
    temp_size_label = ttk.Label(temp_frame, text="Size: 0 MB")
    temp_size_label.grid(row=0, column=1, padx=10, pady=5)
    scan_button = ttk.Button(temp_frame, text="Scan", command=lambda: threading.Thread(target=scan_temp_files, args=(temp_size_label, scan_button)).start())
    scan_button.grid(row=0, column=2, padx=10, pady=5)
    delete_button = ttk.Button(temp_frame, text="Delete", command=lambda: threading.Thread(target=delete_temp_files, args=(temp_size_label, delete_button)).start())
    delete_button.grid(row=0, column=3, padx=10, pady=5)

    # Duplicate Files section
    dup_frame = ttk.LabelFrame(frame, text="Duplicate Files", padding=10)
    dup_frame.grid(row=1, column=0, columnspan=4, sticky='nsew', padx=10, pady=5)
    
    dup_dir_entry = ttk.Entry(dup_frame, width=50)
    dup_dir_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
    browse_button = ttk.Button(dup_frame, text="Browse", command=lambda: browse_dup_dir(dup_dir_entry))
    browse_button.grid(row=0, column=2, padx=10, pady=5)
    
    # Tree view for duplicate files
    dup_tree = ttk.Treeview(dup_frame, columns=('Size', 'Hash'), selectmode='extended', height=10)
    dup_tree.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=10, pady=5)
    dup_tree.heading('#0', text='File Path')
    dup_tree.heading('Size', text='Size (MB)')
    dup_tree.heading('Hash', text='Content Hash')
    dup_tree.column('Size', width=100)
    dup_tree.column('Hash', width=200)

    # Buttons frame
    btn_frame = ttk.Frame(dup_frame)
    btn_frame.grid(row=2, column=0, columnspan=3, pady=5)
    
    scan_dup_button = ttk.Button(btn_frame, text="Scan", 
                                command=lambda: threading.Thread(target=scan_dup_files, 
                                                              args=(dup_dir_entry, dup_tree, scan_dup_button)).start())
    scan_dup_button.pack(side='left', padx=5)
    
    find_same_name_button = ttk.Button(btn_frame, text="Find Same Names", 
                                      command=lambda: find_same_name_matches(dup_dir_entry, dup_tree))
    find_same_name_button.pack(side='left', padx=5)
    
    delete_dup_button = ttk.Button(btn_frame, text="Delete Selected", 
                                  command=lambda: delete_selected_files(dup_tree))
    delete_dup_button.pack(side='left', padx=5)
    
    keep_unique_button = ttk.Button(btn_frame, text="Keep Unique", 
                                   command=lambda: keep_unique_files(dup_tree))
    keep_unique_button.pack(side='left', padx=5)

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

    # Collect all files
    all_files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                file_hash = calculate_file_hash(file_path)
                all_files.append((file_path, file_size, file_hash))
            except (OSError, PermissionError):
                continue

    # Group by hash
    hash_groups = defaultdict(list)
    for file_path, size, file_hash in all_files:
        hash_groups[file_hash].append((file_path, size))

    # Display duplicates
    for file_hash, files in hash_groups.items():
        if len(files) > 1:
            parent = dup_tree.insert('', 'end', text=f"Hash: {file_hash[:8]}...", values=('', file_hash))
            for file_path, size in files:
                dup_tree.insert(parent, 'end', text=file_path, 
                              values=(f"{size / (1024*1024):.2f}", file_hash))

    scan_dup_button.config(state='normal')

def find_same_name_matches(dup_dir_entry, dup_tree):
    selected = dup_tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a file first")
        return

    dir_path = dup_dir_entry.get()
    if not dir_path or not os.path.exists(dir_path):
        messagebox.showerror("Error", "Please select a valid directory.")
        return

    file_path = dup_tree.item(selected[0], 'text')
    if not os.path.exists(file_path):
        messagebox.showerror("Error", "Selected file does not exist.")
        return

    filename = os.path.basename(file_path)
    same_name_files = find_same_name_files(dir_path, filename)

    # Clear existing items and show same-name files
    for item in dup_tree.get_children():
        dup_tree.delete(item)

    parent = dup_tree.insert('', 'end', text=f"Files named: {filename}", values=('', ''))
    for path in same_name_files:
        try:
            size = os.path.getsize(path)
            file_hash = calculate_file_hash(path)
            dup_tree.insert(parent, 'end', text=path, 
                          values=(f"{size / (1024*1024):.2f}", file_hash))
        except (OSError, PermissionError):
            continue

def delete_selected_files(dup_tree):
    selected = dup_tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select files to delete")
        return

    if messagebox.askyesno("Confirm", "Delete selected files? This action cannot be undone."):
        for item in selected:
            file_path = dup_tree.item(item, 'text')
            if os.path.exists(file_path):
                try:
                    send2trash.send2trash(file_path)
                    dup_tree.delete(item)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {file_path}: {str(e)}")

def keep_unique_files(dup_tree):
    hash_groups = defaultdict(list)
    for item in dup_tree.get_children():
        for child in dup_tree.get_children(item):
            file_path = dup_tree.item(child, 'text')
            file_hash = dup_tree.item(child, 'values')[1]
            hash_groups[file_hash].append((child, file_path))

    if messagebox.askyesno("Confirm", "Keep only one file from each duplicate group?"):
        for hash_group in hash_groups.values():
            if len(hash_group) > 1:
                # Keep the first file, delete the rest
                for item_id, file_path in hash_group[1:]:
                    try:
                        send2trash.send2trash(file_path)
                        dup_tree.delete(item_id)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete {file_path}: {str(e)}")