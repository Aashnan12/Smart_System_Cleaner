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
    """Determine the category of a file based on its extension."""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        # Quick extension mapping for common file types
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            return 'Images'
        elif ext in {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}:
            return 'Videos'
        elif ext in {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}:
            return 'Audio'
        elif ext in {'.doc', '.docx', '.pdf', '.txt', '.xlsx', '.csv'}:
            return 'Documents'
        elif ext in {'.exe', '.msi', '.app', '.dmg', '.deb', '.rpm'}:
            return 'Applications'
        elif ext in {'.dll', '.sys', '.driver'}:
            return 'System'
        
        return 'Other'
    except:
        return 'Other'

def setup_storage_tab(frame):
    details_frame = ttk.LabelFrame(frame, text="Storage Details", padding=10)
    details_frame.pack(fill='x', padx=10, pady=10)

    # Status label for scanning
    status_label = ttk.Label(details_frame, text="")
    status_label.pack(fill='x', padx=5, pady=2)

    # Category frame with Treeview
    category_frame = ttk.LabelFrame(frame, text="Usage by Category", padding=10)
    category_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
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

    # Create figure for category chart
    fig, ax = plt.subplots(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

    def scan_directory(path, categories, status_label):
        try:
            for root, _, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            size = os.path.getsize(file_path)
                            category = get_file_category(file_path)
                            categories[category] += size
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass

    def update_storage_info():
        drive = 'C:\\' if os.name == 'nt' else '/'
        status_label.config(text="Scanning storage...")

        # Clear previous data
        for item in category_tree.get_children():
            category_tree.delete(item)

        # Initialize categories
        categories = defaultdict(int)

        # Start scanning in a separate thread
        def scan_thread():
            scan_directory(drive, categories, status_label)
            frame.after(0, lambda: update_ui(categories))

        threading.Thread(target=scan_thread, daemon=True).start()

    def update_ui(categories):
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
        ax.clear()
        categories_to_plot = sorted_categories[:6]  # Show top 6 categories
        sizes = [size / (1024**3) for _, size in categories_to_plot]
        labels = [cat for cat, _ in categories_to_plot]
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5']
        ax.bar(labels, sizes, color=colors)
        ax.set_title("Storage Usage by Category")
        ax.set_ylabel("Size (GB)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        canvas.draw()

        status_label.config(text="Scan complete!")

    # Initial update
    update_storage_info()

    # Schedule periodic updates
    frame.after(300000, update_storage_info)  # Update every 5 minutes