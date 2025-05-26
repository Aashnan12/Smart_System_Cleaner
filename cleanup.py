import tkinter as tk
from tkinter import ttk, messagebox
import os
import hashlib
import send2trash
import threading
from collections import defaultdict

def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except PermissionError:
        messagebox.showwarning("Permission Denied", f"Cannot access file: {file_path}\nPlease check file permissions.")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to calculate hash for {file_path}: {str(e)}")
        return None

def find_duplicate_files(paths):
    """Find files with same content but different names."""
    hash_map = defaultdict(list)
    for path in paths:
        file_hash = calculate_file_hash(path)
        if file_hash:  # Only add if hash calculation succeeded
            hash_map[file_hash].append(path)
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

def find_same_name_files(base_path, filename):
    """Find all files with the same name across directories."""
    same_name_files = []
    for root, _, files in os.walk(base_path):
        if filename in files:
            file_path = os.path.join(root, filename)
            try:
                # Test file accessibility
                with open(file_path, 'rb'):
                    same_name_files.append(file_path)
            except PermissionError:
                messagebox.showwarning("Permission Denied", 
                    f"Cannot access file: {file_path}\nSkipping this file.")
            except Exception as e:
                messagebox.showwarning("Access Error", 
                    f"Cannot access file: {file_path}\nError: {str(e)}")
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
    
    # Tree view for duplicate files with multiple selection enabled
    dup_tree = ttk.Treeview(dup_frame, columns=('Size', 'Hash', 'Status'), selectmode='extended', height=10)
    dup_tree.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=10, pady=5)
    dup_tree.heading('#0', text='File Path')
    dup_tree.heading('Size', text='Size (MB)')
    dup_tree.heading('Hash', text='Content Hash')
    dup_tree.heading('Status', text='Status')
    dup_tree.column('Size', width=100)
    dup_tree.column('Hash', width=200)
    dup_tree.column('Status', width=100)

    # Add scrollbar for the treeview
    scrollbar = ttk.Scrollbar(dup_frame, orient="vertical", command=dup_tree.yview)
    scrollbar.grid(row=1, column=3, sticky='ns')
    dup_tree.configure(yscrollcommand=scrollbar.set)

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
    
    select_all_button = ttk.Button(btn_frame, text="Select All", 
                                  command=lambda: select_all_files(dup_tree))
    select_all_button.pack(side='left', padx=5)

    # Bind Ctrl+A for select all
    dup_tree.bind('<Control-a>', lambda e: select_all_files(dup_tree))

def select_all_files(tree):
    """Select all files in the tree view."""
    tree.selection_set(tree.get_children())
    for parent in tree.get_children():
        for child in tree.get_children(parent):
            tree.selection_add(child)

def scan_temp_files(temp_size_label, scan_button):
    scan_button.config(state='disabled')
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp') if os.name == 'nt' else '/tmp')
    total_size = 0
    if os.path.exists(temp_dir):
        for root, _, files in os.walk(temp_dir):
            for file in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                except PermissionError:
                    messagebox.showwarning("Permission Denied", 
                        f"Cannot access some temporary files.\nSkipping inaccessible files.")
                except Exception as e:
                    messagebox.showwarning("Error", 
                        f"Error accessing files: {str(e)}\nSkipping problematic files.")
    temp_size_label.config(text=f"Size: {total_size / (1024*1024):.2f} MB")
    scan_button.config(state='normal')

def delete_temp_files(temp_size_label, delete_button):
    delete_button.config(state='disabled')
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp') if os.name == 'nt' else '/tmp')
    skipped_files = []
    
    if os.path.exists(temp_dir):
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    send2trash.send2trash(file_path)
                except PermissionError:
                    skipped_files.append(file_path)
                except Exception as e:
                    messagebox.showwarning("Error", 
                        f"Failed to delete {file_path}: {str(e)}")
    
    if skipped_files:
        messagebox.showwarning("Permission Denied",
            "The following files could not be deleted due to insufficient permissions:\n" +
            "\n".join(skipped_files[:5]) +
            ("\n..." if len(skipped_files) > 5 else ""))
    
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
    inaccessible_files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                file_hash = calculate_file_hash(file_path)
                if file_hash:  # Only add if hash calculation succeeded
                    all_files.append((file_path, file_size, file_hash))
            except PermissionError:
                inaccessible_files.append(file_path)
            except Exception as e:
                messagebox.showwarning("Error", 
                    f"Error processing {file_path}: {str(e)}")

    # Group by hash
    hash_groups = defaultdict(list)
    for file_path, size, file_hash in all_files:
        hash_groups[file_hash].append((file_path, size))

    # Display duplicates
    for file_hash, files in hash_groups.items():
        if len(files) > 1:
            parent = dup_tree.insert('', 'end', text=f"Hash: {file_hash[:8]}...", 
                                   values=('', file_hash, ''))
            for file_path, size in files:
                dup_tree.insert(parent, 'end', text=file_path, 
                              values=(f"{size / (1024*1024):.2f}", file_hash, 'Accessible'))

    if inaccessible_files:
        parent = dup_tree.insert('', 'end', text="Inaccessible Files", 
                               values=('', '', 'Permission Denied'))
        for file_path in inaccessible_files:
            dup_tree.insert(parent, 'end', text=file_path, 
                          values=('N/A', 'N/A', 'Permission Denied'))

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

    parent = dup_tree.insert('', 'end', text=f"Files named: {filename}", 
                           values=('', '', ''))
    for path in same_name_files:
        try:
            size = os.path.getsize(path)
            file_hash = calculate_file_hash(path)
            status = 'Accessible' if file_hash else 'Permission Denied'
            dup_tree.insert(parent, 'end', text=path, 
                          values=(f"{size / (1024*1024):.2f}", 
                                 file_hash if file_hash else 'N/A',
                                 status))
        except PermissionError:
            dup_tree.insert(parent, 'end', text=path, 
                          values=('N/A', 'N/A', 'Permission Denied'))
        except Exception as e:
            dup_tree.insert(parent, 'end', text=path, 
                          values=('N/A', 'N/A', f'Error: {str(e)}'))

def delete_selected_files(dup_tree):
    selected = dup_tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select files to delete")
        return

    # Check for permission denied files
    permission_denied = []
    for item in selected:
        status = dup_tree.item(item, 'values')[2]
        if status == 'Permission Denied':
            permission_denied.append(dup_tree.item(item, 'text'))
    
    if permission_denied:
        messagebox.showwarning("Permission Denied",
            "The following files cannot be deleted due to insufficient permissions:\n" +
            "\n".join(permission_denied))
        return

    if messagebox.askyesno("Confirm", "Delete selected files? This action cannot be undone."):
        for item in selected:
            file_path = dup_tree.item(item, 'text')
            if os.path.exists(file_path):
                try:
                    # Normalize the path to handle special characters
                    normalized_path = os.path.normpath(file_path)
                    send2trash.send2trash(normalized_path)
                    dup_tree.delete(item)
                except PermissionError:
                    messagebox.showerror("Permission Denied", 
                        f"Cannot delete {file_path}\nPlease check file permissions.")
                except Exception as e:
                    messagebox.showerror("Error", 
                        f"Failed to delete {file_path}: {str(e)}")