import tkinter as tk
from tkinter import ttk
from cleanup import setup_cleanup_tab
from storage import setup_storage_tab
from memory import setup_memory_tab
from deep_clean import setup_deep_clean_tab

def create_ui(root):
    root.title("Smart System Cleaner")
    root.geometry("1000x700")
    root.configure(bg="#F2F2F7")  # Light macOS-like background

    # Custom style for Apple-like UI
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TNotebook', background="#F2F2F7", borderwidth=0)
    style.configure('TNotebook.Tab', background="#E0E0E0", padding=[20, 10], font=('Helvetica', 12))
    style.map('TNotebook.Tab', background=[('selected', '#F2F2F7')])
    style.configure('TFrame', background="#F2F2F7")
    style.configure('TLabel', background="#F2F2F7", font=('Helvetica', 12))
    style.configure('TButton', background="#E0E0E0", font=('Helvetica', 12), relief='flat')
    style.map('TButton', background=[('active', '#D0D0D0')])

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=20, pady=20)

    # Tabs
    cleanup_frame = ttk.Frame(notebook)
    notebook.add(cleanup_frame, text='Cleanup')
    setup_cleanup_tab(cleanup_frame)

    storage_frame = ttk.Frame(notebook)
    notebook.add(storage_frame, text='Storage')
    setup_storage_tab(storage_frame)

    memory_frame = ttk.Frame(notebook)
    notebook.add(memory_frame, text='Memory')
    setup_memory_tab(memory_frame)

    deep_clean_frame = ttk.Frame(notebook)
    notebook.add(deep_clean_frame, text='Deep Clean')
    setup_deep_clean_tab(deep_clean_frame)

    # Subtle shadow effect
    shadow = tk.Frame(root, bg="#D0D0D0", height=2)
    shadow.place(relx=0, rely=0.08, relwidth=1)