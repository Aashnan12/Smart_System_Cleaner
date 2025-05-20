import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading
from collections import defaultdict
import mimetypes

def get_file_category(file_path):
    """Determine the category of a file based on its extension and location."""
    try:
        # System directories
        system_dirs = {'/System', '/Windows', '/Program Files', '/Program Files (x86)', '/bin', '/sbin', '/usr'}
        for sys_dir in system_dirs:
            if file_path.startswith(sys_dir):
                return 'System'

        # Get the mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('image/'):
                return 'Images'
            elif mime_type.startswith('video/'):
                return 'Videos'
            elif mime_type.startswith('audio/'):
                return 'Audio'
            elif mime_type.startswith('text/'):
                return 'Documents'
            elif mime_type.startswith('application/'):
                if any(ext in file_path.lower() for ext in ['.exe', '.msi', '.app']):
                    return 'Applications'
                return 'Documents'
        
        # Check specific extensions
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return 'Images'
        elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return 'Videos'
        elif ext in ['.mp3', '.wav', '.flac', '.m4a']:
            return 'Audio'
        elif ext in ['.doc', '.docx', '.pdf', '.txt', '.xlsx']:
            return 'Documents'
        elif ext in ['.exe', '.msi', '.app', '.dmg']:
            return 'Applications'
        
        return 'Other'
    except:
        return 'Other'

def setup_storage_tab(frame):
    details_frame = ttk.LabelFrame(frame, text="Storage Details", padding=10)
    details_frame.pack(fill='x', padx=10, pady=10)

    total_label = ttk.Label(details_frame, text="Total: ")
    total_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
    used_label = ttk.Label(details_frame, text="Used: ")
    used_label.grid(row=1, column=0, padx=5, pady=2, sticky='w')
    free_label = ttk.Label(details_frame, text="Free: ")
    free_label.grid(row=2, column=0, padx=5, pady=2, sticky='w')

    # Progress bar for scan progress
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(details_frame, variable=progress_var, maximum=100)
    progress.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
    progress_label = ttk.Label(details_frame, text="")
    progress_label.grid(row=4, column=0, columnspan=2, padx=5, pady=2)

    # Category frame with Treeview
    category_frame = ttk.LabelFrame(frame, text="Usage by Category", padding=10)
    category_frame.pack(fill='x', padx=10, pady=10)
    
    # Add scrollbar to Treeview
    tree_frame = ttk.Frame(category_frame)
    tree_frame.pack(fill='both', expand=True)
    
    category_tree = ttk.Treeview(tree_frame, columns=('Size', 'Percentage'), show='headings', height=8)
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=category_tree.yview)
    category_tree.configure(yscrollcommand=scrollbar.set)
    
    category_tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    category_tree.heading('Size', text='Size (GB)')
    category_tree.heading('Percentage', text='Percentage')
    category_tree.column('Size', width=100)
    category_tree.column('Percentage', width=100)

    # Create figure for pie chart
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), gridspec_kw={'height_ratios': [1, 1]})
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

    def scan_directory(path, categories, total_files, progress_var, progress_label):
        try:
            for root, _, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            size = os.path.getsize(file_path)
                            category = get_file_category(file_path)
                            categories[category] += size
                            total_files[0] += 1
                            if total_files[0] % 100 == 0:  # Update progress every 100 files
                                progress_var.set((total_files[0] % 1000) / 10)
                                progress_label.config(text=f"Scanned {total_files[0]} files...")
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass

    def update_storage_info():
        drive = 'C:\\' if os.name == 'nt' else '/'
        try:
            disk = psutil.disk_usage(drive)
            total = disk.total / (1024**3)
            used = disk.used / (1024**3)
            free = disk.free / (1024**3)
            total_label.config(text=f"Total: {total:.2f} GB")
            used_label.config(text=f"Used: {used:.2f} GB")
            free_label.config(text=f"Free: {free:.2f} GB")

            # Clear previous data
            for item in category_tree.get_children():
                category_tree.delete(item)

            # Initialize categories
            categories = defaultdict(int)
            total_files = [0]  # Using list to allow modification in nested function

            # Start scanning in a separate thread
            def scan_thread():
                scan_directory(drive, categories, total_files, progress_var, progress_label)
                
                # Update UI with results
                frame.after(0, lambda: update_ui(categories, used))

            threading.Thread(target=scan_thread, daemon=True).start()

            # Update storage overview chart
            ax1.clear()
            ax1.pie([used, free], labels=['Used', 'Free'], autopct='%1.1f%%', 
                   colors=['#FF6B6B', '#4ECDC4'])
            ax1.set_title("Storage Overview")

        except Exception as e:
            total_label.config(text=f"Error: {str(e)}")

    def update_ui(categories, total_used):
        # Calculate percentages and sort by size
        total_size = sum(categories.values())
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

        # Update treeview
        for category, size in sorted_categories:
            size_gb = size / (1024**3)
            percentage = (size / total_size) * 100 if total_size > 0 else 0
            category_tree.insert('', 'end', values=(
                f"{size_gb:.2f}",
                f"{percentage:.1f}%"
            ), text=category)

        # Update category chart
        ax2.clear()
        categories_to_plot = sorted_categories[:6]  # Show top 6 categories
        sizes = [size / (1024**3) for _, size in categories_to_plot]
        labels = [cat for cat, _ in categories_to_plot]
        
        ax2.bar(labels, sizes, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5'])
        ax2.set_title("Storage Usage by Category")
        ax2.set_ylabel("Size (GB)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        canvas.draw()

        # Reset progress
        progress_var.set(0)
        progress_label.config(text="Scan complete!")

    # Initial update
    update_storage_info()

    # Schedule periodic updates
    frame.after(300000, update_storage_info)  # Update every 5 minutes