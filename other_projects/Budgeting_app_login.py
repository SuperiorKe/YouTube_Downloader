from tkinter import *
from tkinter import ttk

root = Tk(screenName="Budgeting App")

#title osf the window
root.title("LogIn")

# set min and max width and height
root.geometry("720x480")
root.minsize(720, 480)
root.maxsize(1800, 720)

frame = ttk.Frame(root, padding= 10)
frame.grid()

welcome = ttk.Label(frame, text="Welcome, KENN!")
welcome.grid(column=2, row=0)

name = ttk.Label(frame, text="Enter your email: ")
name.grid(column=1, row=1)

name_entry = ttk.Entry(frame)
name_entry.grid(column=2, row=1)

password = ttk.Label(frame, text="Enter Password: ")
password.grid(column=1, row=2)

password_entry = ttk.Entry(frame)
password_entry.grid(column=2, row=2)

login = ttk.Button(frame, text="login", command=root.destroy)
login.grid(column=2, row=4)

recovery = ttk.Label(frame, text="Forgot Password?")
recovery.grid(column=3, row=5)

signup = ttk.Label(frame, text="Don't have an account?")
signup.grid(column=2, row=6)

signup_btn = ttk.Button(frame, text="Sign Up", command=root.destroy)
signup_btn.grid(column=2, row=7)

quit = ttk.Button(frame, text="Quit", command=root.destroy)
quit.grid(column=3, row=8)

menu = ttk.Menubutton(frame)
menu.grid(column=1, row=8)



root.mainloop()













 
#creeate root window
# root = ctk.CTk()
# ctk.set_appearance_mode("system")
# ctk.set_default_color_theme("blue")

# #title osf the window
# root.title("Budgeting App")

# # set min and max width and height
# root.geometry("720x480")
# root.minsize(720, 480)
# root.maxsize(1800, 720)

# #create a frame to hold the content
# content_frame = ctk.CTkFrame(root)
# content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

# phone = ctk.CTkLabel(ctk.CTk(), text="Enter your name:")
# phone.pack()

# # ctk.Entry(ctk.CTk(), width=200).pack()


# #start the app
# root.mainloop()


