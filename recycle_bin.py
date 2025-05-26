import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import json
from datetime import datetime
import threading

class RecycleBin:
    def __init__(self):
        self.bin_dir = os.path.join(os.path.expanduser('~'), '.smart_cleaner_bin')
        self.metadata_file = os.path.join(self.bin_dir, 'metadata.json')
        self._ensure_bin_exists()

    def _ensure_bin_exists(self):
        if not os.path.exists(self.bin_dir):
            os.makedirs(self.bin_dir)
        if not os.path.exists(self.metadata_file):
            self._save_metadata({})

    def _load_metadata(self):
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_metadata(self, metadata):
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)

    def move_to_bin(self, file_paths):
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        moved_files = []
        failed_files = []
        metadata = self._load_metadata()

        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    failed_files.append((file_path, "File not found"))
                    continue

                file_name = os.path.basename(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                bin_name = f"{timestamp}_{file_name}"
                bin_path = os.path.join(self.bin_dir, bin_name)

                # Store original structure for folders
                original_structure = None
                if os.path.isdir(file_path):
                    original_structure = []
                    for root, dirs, files in os.walk(file_path):
                        rel_path = os.path.relpath(root, file_path)
                        for f in files:
                            file_full_path = os.path.join(root, f)
                            rel_file_path = os.path.relpath(file_full_path, file_path)
                            original_structure.append({
                                'path': rel_file_path,
                                'size': os.path.getsize(file_full_path)
                            })

                shutil.move(file_path, bin_path)
                metadata[bin_name] = {
                    'original_path': file_path,
                    'deleted_date': datetime.now().isoformat(),
                    'size': os.path.getsize(bin_path) if os.path.isfile(bin_path) else self._get_dir_size(bin_path),
                    'is_directory': os.path.isdir(bin_path),
                    'original_structure': original_structure
                }
                moved_files.append(file_path)
            except Exception as e:
                failed_files.append((file_path, str(e)))

        self._save_metadata(metadata)
        return moved_files, failed_files

    def _get_dir_size(self, path):
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def restore_file(self, bin_name, file_path=None, custom_path=None):
        metadata = self._load_metadata()
        if bin_name not in metadata:
            raise ValueError(f"File not found in recycle bin: {bin_name}")

        bin_path = os.path.join(self.bin_dir, bin_name)
        original_path = metadata[bin_name]['original_path']

        # Handle individual file restoration from a folder
        if metadata[bin_name]['is_directory'] and file_path:
            bin_file_path = os.path.join(bin_path, file_path)
            if not os.path.exists(bin_file_path):
                raise ValueError(f"File not found in folder: {file_path}")

            restore_path = custom_path if custom_path else os.path.join(
                os.path.dirname(original_path),
                file_path
            )
            restore_dir = os.path.dirname(restore_path)

            if not os.path.exists(restore_dir):
                os.makedirs(restore_dir)

            shutil.copy2(bin_file_path, restore_path)
            os.remove(bin_file_path)

            # Update the metadata to remove the restored file
            metadata[bin_name]['original_structure'] = [
                item for item in metadata[bin_name]['original_structure']
                if item['path'] != file_path
            ]
            metadata[bin_name]['size'] = self._get_dir_size(bin_path)

            # If the folder is empty after restoration, remove it
            if not os.listdir(bin_path):
                os.rmdir(bin_path)
                del metadata[bin_name]
        else:
            # Regular file or full folder restoration
            restore_path = custom_path if custom_path else original_path
            restore_dir = os.path.dirname(restore_path)

            if not os.path.exists(restore_dir):
                os.makedirs(restore_dir)

            shutil.move(bin_path, restore_path)
            del metadata[bin_name]

        self._save_metadata(metadata)

    def permanently_delete(self, bin_names):
        if not isinstance(bin_names, list):
            bin_names = [bin_names]

        metadata = self._load_metadata()
        deleted = []
        failed = []

        for bin_name in bin_names:
            try:
                if bin_name not in metadata:
                    failed.append((bin_name, "File not found in recycle bin"))
                    continue

                bin_path = os.path.join(self.bin_dir, bin_name)
                if os.path.isdir(bin_path):
                    shutil.rmtree(bin_path)
                else:
                    os.remove(bin_path)
                del metadata[bin_name]
                deleted.append(bin_name)
            except Exception as e:
                failed.append((bin_name, str(e)))

        self._save_metadata(metadata)
        return deleted, failed

    def get_bin_contents(self):
        return self._load_metadata()

def setup_recycle_bin_tab(frame):
    bin_instance = RecycleBin()

    # Create Treeview with checkboxes
    tree = ttk.Treeview(frame, columns=('Original Path', 'Date', 'Size', 'Type'), 
                       show='tree headings', height=15)
    tree.heading('Original Path', text='Original Path')
    tree.heading('Date', text='Deletion Date')
    tree.heading('Size', text='Size')
    tree.heading('Type', text='Type')
    tree.column('Date', width=150)
    tree.column('Size', width=100)
    tree.column('Type', width=100)

    # Add scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    # Grid layout for tree and scrollbars
    tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    hsb.grid(row=1, column=0, sticky='ew')
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    # Buttons frame
    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

    def format_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        
        contents = bin_instance.get_bin_contents()
        for bin_name, info in contents.items():
            is_dir = info.get('is_directory', False)
            item_type = 'Folder' if is_dir else 'File'
            
            parent = tree.insert('', 'end', values=(
                info['original_path'],
                datetime.fromisoformat(info['deleted_date']).strftime("%Y-%m-%d %H:%M:%S"),
                format_size(info['size']),
                item_type
            ), tags=(bin_name,))

            # If it's a directory, add child items for each file
            if is_dir and info.get('original_structure'):
                for file_info in info['original_structure']:
                    tree.insert(parent, 'end', values=(
                        file_info['path'],
                        '',
                        format_size(file_info['size']),
                        'File'
                    ), tags=(f"{bin_name}:{file_info['path']}",))

    def restore_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select items to restore")
            return

        restored = []
        failed = []
        for item in selection:
            try:
                tags = tree.item(item)['tags'][0]
                if ':' in tags:  # Individual file from a folder
                    bin_name, file_path = tags.split(':', 1)
                    custom_path = None
                    if messagebox.askyesno("Restore Location", 
                                         "Would you like to choose a custom restore location?"):
                        custom_path = filedialog.asksaveasfilename(
                            title="Choose Restore Location",
                            initialfile=os.path.basename(file_path)
                        )
                    bin_instance.restore_file(bin_name, file_path, custom_path)
                else:  # Regular file or folder
                    custom_path = None
                    if messagebox.askyesno("Restore Location", 
                                         "Would you like to choose a custom restore location?"):
                        if tree.item(item)['values'][3] == 'Folder':
                            custom_path = filedialog.askdirectory(title="Choose Restore Location")
                        else:
                            custom_path = filedialog.asksaveasfilename(
                                title="Choose Restore Location",
                                initialfile=os.path.basename(tree.item(item)['values'][0])
                            )
                    bin_instance.restore_file(tags, custom_path=custom_path)
                restored.append(tree.item(item)['values'][0])
            except Exception as e:
                failed.append((tree.item(item)['values'][0], str(e)))

        if restored:
            messagebox.showinfo("Success", f"Successfully restored {len(restored)} items")
        if failed:
            messagebox.showerror("Error", "Failed to restore some items:\n" + 
                               "\n".join(f"{path}: {error}" for path, error in failed))
        refresh_list()

    def delete_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select items to delete")
            return
        
        items_to_delete = []
        for item in selection:
            tags = tree.item(item)['tags'][0]
            if ':' not in tags:  # Only allow deleting whole folders/files
                items_to_delete.append(tree.item(item)['values'][0])
        
        if not items_to_delete:
            messagebox.showwarning("Warning", "Please select entire folders or files to delete")
            return
        
        if messagebox.askyesno("Confirm Deletion", 
                              "Permanently delete the following items?\n\n" + 
                              "\n".join(items_to_delete)):
            try:
                bin_names = [tree.item(item)['tags'][0] for item in selection 
                           if ':' not in tree.item(item)['tags'][0]]
                deleted, failed = bin_instance.permanently_delete(bin_names)
                
                if deleted:
                    messagebox.showinfo("Success", f"Successfully deleted {len(deleted)} items")
                if failed:
                    messagebox.showerror("Error", "Failed to delete some items:\n" + 
                                       "\n".join(f"{name}: {error}" for name, error in failed))
                refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete items: {str(e)}")

    ttk.Button(btn_frame, text="Refresh", command=refresh_list).pack(side='left', padx=5)
    ttk.Button(btn_frame, text="Restore Selected", command=restore_selected).pack(side='left', padx=5)
    ttk.Button(btn_frame, text="Delete Permanently", command=delete_selected).pack(side='left', padx=5)

    # Initialize the view
    refresh_list()

    # Enable multiple selection
    tree.configure(selectmode='extended')

    # Bind Ctrl+A for select all
    def select_all(event):
        for item in tree.get_children():
            tree.selection_add(item)
    tree.bind('<Control-a>', select_all)