import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading

category_cache = {}

def setup_storage_tab(frame):
    details_frame = ttk.LabelFrame(frame, text="Storage Details", padding=10)
    details_frame.pack(fill='x', padx=10, pady=10)

    total_label = ttk.Label(details_frame, text="Total: ")
    total_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
    used_label = ttk.Label(details_frame, text="Used: ")
    used_label.grid(row=1, column=0, padx=5, pady=2, sticky='w')
    free_label = ttk.Label(details_frame, text="Free: ")
    free_label.grid(row=2, column=0, padx=5, pady=2, sticky='w')

    category_frame = ttk.LabelFrame(frame, text="Usage by Category", padding=10)
    category_frame.pack(fill='x', padx=10, pady=10)
    category_tree = ttk.Treeview(category_frame, columns=('Size',), show='headings', height=5)
    category_tree.pack(fill='x')
    category_tree.heading('Size', text='Size (GB)')
    category_tree.column('Size', width=100)

    fig, ax = plt.subplots(figsize=(6, 4))
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

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

            if not category_cache:
                threading.Thread(target=scan_categories, args=(category_tree, ax, canvas)).start()
            else:
                update_category_ui(category_tree, ax, canvas)
        except Exception as e:
            total_label.config(text=f"Error: {str(e)}")
        frame.after(5000, update_storage_info)

    def scan_categories(category_tree, ax, canvas):
        global category_cache
        categories = {'System': 0, 'Users': 0, 'Apps': 0, 'Other': 0}
        base_dirs = {
            'System': ['/System', '/Windows'],
            'Users': ['/Users', 'C:\\Users'],
            'Apps': ['/Applications', 'C:\\Program Files']
        }
        for cat, dirs in base_dirs.items():
            for d in dirs:
                if os.path.exists(d):
                    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(d) for f in fs if os.path.exists(os.path.join(r, f))) / (1024**3)
                    categories[cat] += size
        categories['Other'] = used - sum(categories.values())
        category_cache = categories
        update_category_ui(category_tree, ax, canvas)

    def update_category_ui(category_tree, ax, canvas):
        for item in category_tree.get_children():
            category_tree.delete(item)
        for cat, size in category_cache.items():
            if size > 0:
                category_tree.insert('', 'end', text=cat, values=(f"{size:.2f}",))
        ax.clear()
        ax.bar(category_cache.keys(), [max(0, s) for s in category_cache.values()], color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax.set_title("Storage Usage by Category")
        ax.set_ylabel("Size (GB)")
        canvas.draw()

    update_storage_info()