from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\MISI\PycharmProjects\Ensha\frontend\build\assets\frame2")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


window = Tk()

window.geometry("800x480")
window.configure(bg = "#FFFFFF")

canvas = Canvas(window, bg = "#FFFFFF", height = 480, width = 800, bd = 0, highlightthickness = 0, relief = "ridge")

canvas.place(x = 0, y = 0)
image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(400.0, 240.0, image=image_image_1)

canvas.create_text( 131.2, 85, anchor="nw", text="LOGIN", fill="#474D59", font=("NunitoSans ExtraBold", 26))

image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(90.2, 105, image=image_image_2)

canvas.create_text( 63.2, 174, anchor="nw", text="Username", fill="#474D59", font=("NunitoSans Regular", 12))

canvas.create_text( 63.2, 243, anchor="nw", text="Password", fill="#474D59", font=("Nunito Regular", 12))

entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(200.4, 213, image=entry_image_1)
entry_1 = Entry(bd=0, bg="#FFFFFF", fg="#000716", highlightthickness=0, font=("Nunito Regular", 11))
entry_1.place(x=75.2, y=196.0, width=250.4, height=33.0)

entry_image_2 = PhotoImage( file=relative_to_assets("entry_2.png"))
entry_bg_2 = canvas.create_image(200.4, 283, image=entry_image_2)
entry_2 = Entry( bd=0, bg="#FFFFFF", fg="#000716", highlightthickness=0, font=("Nunito Regular", 11))
entry_2.place( x=75.2, y=265.6, width=250.4, height=34)

#REGISTER
button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
button_1 = Button( image=button_image_1, bg="#FFFFFF", borderwidth=0, highlightthickness=0, command=lambda: [window.destroy(), __import__("registers")], relief="flat")
button_1.place(x=147.2, y=376.8, width=134.4, height=15.2)

button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
button_2 = Button(image=button_image_2, borderwidth=0, highlightthickness=0, command=lambda: [window.destroy(), __import__("dashboards")], relief="flat")
button_2.place(x=57.6, y=331.2, width=285.6, height=33.6)

window.resizable(False, False)
window.mainloop()
