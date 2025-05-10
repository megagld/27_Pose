import tkinter as tk


def set_mousewheel(widget, command):
    """Activate / deactivate mousewheel scrolling when 
    cursor is over / not over the widget respectively."""
    widget.bind("<Enter>", lambda _: widget.bind_all('<MouseWheel>', command))
    widget.bind("<Leave>", lambda _: widget.unbind_all('<MouseWheel>'))


root = tk.Tk()
root.geometry('300x300')

l0 = tk.Label(root, text='Hover and scroll on the labels.')
l0.pack(padx=10, pady=10)

l1 = tk.Label(root, text='0', bg='pink', width=10, height=5)
l1.pack(pady=10)
set_mousewheel(l1, lambda e: l1.config(text=e.delta))

l2 = tk.Label(root, text='0', bg='cyan', width=10, height=5)
l2.pack(pady=10)
set_mousewheel(l2, lambda e: l2.config(text=e.delta))

root.mainloop()