import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def setup_memory_tab(frame):
    details_frame = ttk.LabelFrame(frame, text="Memory Details", padding=10)
    details_frame.pack(fill='x', padx=10, pady=10)

    total_label = ttk.Label(details_frame, text="Total: ")
    total_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
    used_label = ttk.Label(details_frame, text="Used: ")
    used_label.grid(row=1, column=0, padx=5, pady=2, sticky='w')
    free_label = ttk.Label(details_frame, text="Free: ")
    free_label.grid(row=2, column=0, padx=5, pady=2, sticky='w')
    swap_label = ttk.Label(details_frame, text="Swap Used: ")
    swap_label.grid(row=3, column=0, padx=5, pady=2, sticky='w')

    fig, ax = plt.subplots(figsize=(6, 4))
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

    process_frame = ttk.LabelFrame(frame, text="Top Memory-Consuming Processes", padding=10)
    process_frame.pack(fill='x', padx=10, pady=10)
    mem_tree = ttk.Treeview(process_frame, columns=('PID', 'Name', 'Memory'), show='headings', height=5)
    mem_tree.pack(fill='x')
    mem_tree.heading('PID', text='PID')
    mem_tree.heading('Name', text='Name')
    mem_tree.heading('Memory', text='Memory (MB)')
    mem_tree.column('PID', width=50)
    mem_tree.column('Memory', width=100)

    def update_memory_info():
        try:
            mem = psutil.virtual_memory()
            total = mem.total / (1024**3)
            used = mem.used / (1024**3)
            free = mem.free / (1024**3)
            swap = psutil.swap_memory().used / (1024**3)
            total_label.config(text=f"Total: {total:.2f} GB")
            used_label.config(text=f"Used: {used:.2f} GB")
            free_label.config(text=f"Free: {free:.2f} GB")
            swap_label.config(text=f"Swap Used: {swap:.2f} GB")

            ax.clear()
            ax.pie([used, free], labels=['Used', 'Free'], autopct='%1.1f%%', colors=['#FF6B6B', '#96CEB4'])
            ax.set_title("Memory Usage")
            canvas.draw()

            for i in mem_tree.get_children():
                mem_tree.delete(i)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    mem_info = proc.info['memory_info']
                    if mem_info:
                        mem_usage = mem_info.rss / (1024*1024)
                        processes.append((proc.info['pid'], proc.info['name'], mem_usage))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            processes.sort(key=lambda x: x[2], reverse=True)
            for proc in processes[:5]:
                mem_tree.insert('', 'end', values=(proc[0], proc[1], f"{proc[2]:.2f}"))
        except Exception as e:
            total_label.config(text=f"Error: {str(e)}")
        frame.after(5000, update_memory_info)

    update_memory_info()