from tkinter import *
from tkinter import ttk

root = Tk(screenName="Budget")

#title osf the window
root.title("Budget")

# set min and max width and height
root.geometry("720x480")
root.minsize(720, 480)
root.maxsize(1800, 720)

frame = ttk.Frame(root, padding=10)
frame.grid()

welcome = ttk.Label(frame, text="Budget", background="grey")
welcome.grid(column=2, row=1)

balance = ttk.Label(frame, text="$  Balance")
balance.grid(column=1, row=2)

income = ttk.Label(frame, text="$  Income")
income.grid(column=2, row=2)

expences = ttk.Label(frame, text="&  Expences")
expences.grid(column=3, row=2)

withdrawals = ttk.Label(frame, text="%  Witdrawals")
withdrawals.grid(column=4, row=2)

amount = ttk.Label(frame, text='Amount')
amount.grid(column=1, row=3)

amount_entry = ttk.Entry(frame )
amount_entry.grid(column=1, row=4)

category = ttk.Label(frame, text='Category')
category.grid(column=1, row=5)

category_entry = ttk.Entry(frame )
category_entry.grid(column=1, row=6)

notes = ttk.Label(frame, text='Notes (Optional)')
notes.grid(column=1, row=7)

notes_entry = ttk.Entry(frame )
notes_entry.grid(column=1, row=8)

types = ttk.Label(frame, text='Transaction_type')
types.grid(column=3, row=3)

types_entry = ttk.Entry(frame )
types_entry.grid(column=3, row=4)

root.mainloop()