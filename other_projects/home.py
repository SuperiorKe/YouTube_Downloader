from tkinter import *
from tkinter import ttk

#creeate root window
root = Tk(screenName="Budget")

#title osf the window
root.title("Home")

# set min and max width and height
root.geometry("720x480")
root.minsize(720, 480)
root.maxsize(1800, 720)

frame = ttk.Frame(root, padding=10)
frame.grid()


welcome = ttk.Label(frame, text="Home", background="grey")
welcome.grid(column=2, row=1)

name = ttk.Label(frame, text="Kenn Waweru")
name.grid(column=1, row=2)

qr = ttk.Label(frame, text="#")
qr.grid(column=4, row=2)

balance = ttk.Label(frame, text="Balance")
balance.grid(column=2, row=4)

amt = ttk.Label(frame, text="$ 7,723.85")
amt.grid(column=2, row=5)

credit_card = ttk.Label(frame, text="Primary Card")
credit_card.grid(column=1, row=6)

credit_card_amt = ttk.Label(frame, text="$ 7,723.85")
credit_card_amt.grid(column=4, row=6)

credit_income = ttk.Label(frame, text="$ +723.85")
credit_income.grid(column=1, row=7)

debit_card = ttk.Label(frame, text="Primary Debit Card")
debit_card.grid(column=1, row=8)

debit_card_amt = ttk.Label(frame, text="$ 7,723.85")
debit_card_amt.grid(column=4, row=8)

debit_income = ttk.Label(frame, text="$ +1,923.85")
debit_income.grid(column=1, row=9)

transactions = ttk.Label(frame, text="Transactions")
transactions.grid(column=1, row=10)

alx_logo = ttk.Label(frame, text="&")
alx_logo.grid(column=1, row=11)

alx = ttk.Label(frame, text="ALX")
alx.grid(column=2, row=11)

alx_amount = ttk.Label(frame, text="$ +5")
alx_amount.grid(column=3, row=11)

warriors_logo = ttk.Label(frame, text="*")
warriors_logo.grid(column=1, row=12)

warriors = ttk.Label(frame, text="Warriors")
warriors.grid(column=2, row=12)

warriors_amt = ttk.Label(frame, text="$  40")
warriors_amt.grid(column=3, row=12)

dashboard = ttk.Label(frame, text="#")
dashboard.grid(column=1, row=13)

budget = ttk.Label(frame, text="$")
budget.grid(column=2, row=13)

profile = ttk.Label(frame, text="@")
profile.grid(column=3, row=13)

analytics = ttk.Label(frame, text="%")
analytics.grid(column=4, row=13)



root.mainloop()