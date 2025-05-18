import tkinter as tk
from tkinter import ttk, messagebox
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

    def move_to_bin(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        metadata = self._load_metadata()
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bin_name = f"{timestamp}_{file_name}"
        bin_path = os.path.join(self.bin_dir, bin_name)

        shutil.move(file_path, bin_path)
        metadata[bin_name] = {
            'original_path': file_path,
            'deleted_date': datetime.now().isoformat(),
            'size': os.path.getsize(bin_path)
        }
        self._save_metadata(metadata)

    def restore_file(self, bin_name):
        metadata = self._load_metadata()
        if bin_name not in metadata:
            raise ValueError(f"File not found in recycle bin: {bin_name}")

        bin_path = os.path.join(self.bin_dir, bin_name)
        original_path = metadata[bin_name]['original_path']
        original_dir = os.path.dirname(original_path)

        if not os.path.exists(original_dir):
            os.makedirs(original_dir)

        shutil.move(bin_path, original_path)
        del metadata[bin_name]
        self._save_metadata(metadata)

    def permanently_delete(self, bin_name):
        metadata = self._load_metadata()
        if bin_name not in metadata:
            raise ValueError(f"File not found in recycle bin: {bin_name}")

        bin_path = os.path.join(self.bin_dir, bin_name)
        os.remove(bin_path)
        del metadata[bin_name]
        self._save_metadata(metadata)

    def get_bin_contents(self):
        return self._load_metadata()

def setup_recycle_bin_tab(frame):
    bin_instance = RecycleBin()

    # Create Treeview
    tree = ttk.Treeview(frame, columns=('Original Path', 'Date', 'Size'), show='headings', height=15)
    tree.heading('Original Path', text='Original Path')
    tree.heading('Date', text='Deletion Date')
    tree.heading('Size', text='Size (KB)')
    tree.column('Date', width=150)
    tree.column('Size', width=100)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    # Buttons frame
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill='x', padx=10, pady=5)

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        
        contents = bin_instance.get_bin_contents()
        for bin_name, info in contents.items():
            size_kb = info['size'] / 1024
            tree.insert('', 'end', values=(
                info['original_path'],
                datetime.fromisoformat(info['deleted_date']).strftime("%Y-%m-%d %H:%M:%S"),
                f"{size_kb:.2f}"
            ), tags=(bin_name,))

    def restore_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to restore")
            return
        
        try:
            bin_name = tree.item(selection[0], 'tags')[0]
            bin_instance.restore_file(bin_name)
            messagebox.showinfo("Success", "File restored successfully")
            refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore file: {str(e)}")

    def delete_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to delete")
            return
        
        if messagebox.askyesno("Confirm", "Permanently delete selected file?"):
            try:
                bin_name = tree.item(selection[0], 'tags')[0]
                bin_instance.permanently_delete(bin_name)
                messagebox.showinfo("Success", "File deleted permanently")
                refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

    ttk.Button(btn_frame, text="Refresh", command=refresh_list).pack(side='left', padx=5)
    ttk.Button(btn_frame, text="Restore Selected", command=restore_selected).pack(side='left', padx=5)
    ttk.Button(btn_frame, text="Delete Permanently", command=delete_selected).pack(side='left', padx=5)

    refresh_list()