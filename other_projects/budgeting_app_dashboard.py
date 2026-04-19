from tkinter import *
from tkinter import ttk

root = Tk(screenName="Dashboard")

#title osf the window
root.title("Dashboard")

# set min and max width and height
root.geometry("720x480")
root.minsize(720, 480)
root.maxsize(1800, 720)

frame = ttk.Frame(root, padding=10, border=5, borderwidth=5)
frame.grid()

welcome = ttk.Label(frame, text="DASHBOARD", background="grey")
welcome.grid(column=2, row=0)

logo = ttk.Label(frame, text="@")
logo.grid(column=1, row=1)

amount = ttk.Label(frame, text="$ 10,000,000")
amount.grid(column=3, row=1)

amount = ttk.Label(frame, text="Send Money")
amount.grid(column=1, row=2)

amount = ttk.Label(frame, text="Pay Bill")
amount.grid(column=2, row=2)

amount = ttk.Label(frame, text="Buy Goods")
amount.grid(column=3, row=2)

searchbox = ttk.Entry(frame, text="search")
searchbox.grid(column=2, row=3)

transaction = ttk.Label(frame, text="Transaction")
transaction.grid(column=1, row=4)

purpose = ttk.Label(frame, text="Purpose")
purpose.grid(column=2, row=4)

amount = ttk.Label(frame, text="Amount")
amount.grid(column=3, row=4)

cellA = ttk.Label(frame, text="Cell A")
cellA.grid(column=1, row=5)

cellB = ttk.Label(frame, text="Cell B")
cellB.grid(column=2, row=5)

cellC = ttk.Label(frame, text="Cell C")
cellC.grid(column=3, row=5)

transport = ttk.Label(frame, text="Transport")
transport.grid(column=1, row=6)


# transport_progress = ttk.Progressbar(value=50,orient="horizontal")
# transport_progress.grid(column=2, row=6)

food = ttk.Label(frame, text="Food")
food.grid(column=1, row=7)

home = ttk.Label(frame, text="@")
home.grid(column=1, row=8)

budget = ttk.Label(frame, text="$")
budget.grid(column=2, row=8)

analytics = ttk.Label(frame, text="#")
analytics.grid(column=3, row=8)

# food_progress = ttk.Progressbar(value=50,orient="horizontal")
# food_progress.grid(column=2, row=7, pady=10)




# #create a resolutions combo box
# menu = ["Home", "Budget", "Analytics"]
# menu_var = ttk.StringVar()
# menu_box = ttk.Combobox(frame, value=menu, textvariable=menu_var)
# menu_box.grid(column=1, row=8, columnspan=3)





root.mainloop()
