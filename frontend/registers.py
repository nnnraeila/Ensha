from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\MISI\PycharmProjects\Ensha\frontend\build\assets\frame1")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


window = Tk()

window.geometry("800x480")
window.configure(bg = "#FFFFFF")

canvas = Canvas(window, bg = "#FFFFFF", height = 480, width = 800, bd = 0, highlightthickness = 0, relief = "ridge")

canvas.place(x = 0, y = 0)
image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(400.0, 240.0, image=image_image_1)

canvas.create_text(131.2, 58,  anchor="nw",  text="SIGN UP",  fill="#474D59",  font=("NunitoSans ExtraBold", 25))

image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(90.2, 78, image=image_image_2)

canvas.create_text( 63.2, 133, anchor="nw", text="Username", fill="#474D59", font=("NunitoSans Regular", 12))
canvas.create_text(63.2, 208, anchor="nw", text="Password", fill="#474D59", font=("Nunito Regular", 12))
canvas.create_text( 63.2, 285, anchor="nw", text="Phone number", fill="#474D59", font=("Nunito Regular", 12))

entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image( 200.4, 171, image=entry_image_1)
entry_1 = Entry( bd=0, bg="#FFFFFF", highlightthickness=0, font = ("Nunito Regular", 11))
entry_1.place( x=75.2, y=154.4, width=250.4, height=33)

entry_image_2 = PhotoImage( file=relative_to_assets("entry_2.png"))
entry_bg_2 = canvas.create_image( 200.4, 247, image=entry_image_2)
entry_2 = Entry( bd=0, bg="#FFFFFF", fg="#000716", highlightthickness=0, font=("Nunito Regular", 11))
entry_2.place( x=75.2, y=229.6, width=250.4, height=34)

entry_image_3 = PhotoImage(file=relative_to_assets("entry_3.png"))
entry_bg_3 = canvas.create_image(200.4, 323, image=entry_image_3)
entry_3 = Entry( bd=0, bg="#FFFFFF", fg="#000716", highlightthickness=0, font = ("Nunito Regular", 11))
entry_3.place( x=75.2, y=306.4, width=250.4, height=34)

#login
button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
button_1 = Button( image=button_image_1, bg="#FFFFFF", borderwidth=0, highlightthickness=0,command=lambda: [window.destroy(), __import__("logins")], relief="flat")
button_1.place(x=213.2, y=370, width=130.4, height=33)

button_image_2 = PhotoImage( file=relative_to_assets("button_2.png"))
button_2 = Button( image=button_image_2, bg="#FFFFFF", borderwidth=0, highlightthickness=0, command=lambda: print("button_2 clicked"),relief="flat")
button_2.place( x=57.0, y=370.0, width=134.0, height=33.0)

window.resizable(False, False)
window.mainloop()
