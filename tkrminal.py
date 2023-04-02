import tkinter as tk
from tkinter import ttk


def run_in_terminal(cmd, *, title="Terminal"):
    root = tk.Tk()
    root.title(title)
    ttk.Button(root, text="Hello world").grid()
    root.mainloop()
