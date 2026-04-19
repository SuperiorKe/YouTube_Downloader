from tkinter import ttk
import customtkinter as ctk
import os

# Creeate root window
root = ctk.CTk()
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

# Title of the window
root.title("News App")

# Set min and max width and height
root.geometry("720x480")
root.minsize(720, 480)
root.maxsize(1800, 720)

# Create a frame to hold the content
content_frame = ctk.CTkFrame(root)
content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)



#create label and the entry widget for video url
Welcome_label = ctk.CTkLabel(content_frame, text="GOOD MORNING, KENN")
Head_label = ctk.CTkLabel(content_frame, text="What's on your mind")
# amount = ctk.CTkLabel(content_frame, text="AMOUNT")
# amount_entry = ctk.CTkEntry(content_frame, width=300, height=40)

listbox = ctk.CTkTextbox(content_frame)
My_notes = ctk.CTkButton(content_frame, text="My Notes")

Welcome_label.pack(pady=(10, 5))
Head_label.pack(pady=(10, 10))
My_notes.pack(pady=(10, 30))
# amount.pack(pady=(20, 10))
# amount_entry.pack(pady=(10, 20))

listbox.pack(pady=(30, 20))

table = ctk.CTkButton(content_frame, text="SAVE")
table.pack(pady=(15,15))



# Start the app
root.mainloop()