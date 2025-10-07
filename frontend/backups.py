
from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\MISI\PycharmProjects\Ensha\frontend\build\assets\frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


window = Tk()

window.geometry("1200x700")
window.configure(bg = "#FFFFFF")


canvas = Canvas(
    window,
    bg = "#FFFFFF",
    height = 700,
    width = 1200,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    602.0,
    350.0,
    image=image_image_1
)

canvas.create_text(
    297.0,
    90.0,
    anchor="nw",
    text="Backup Selection",
    fill="#38363B",
    font=("Inter Medium", 28 * -1)
)

canvas.create_text(
    294.0,
    125.4041748046875,
    anchor="nw",
    text="Choose files and folders to backup",
    fill="#736F7C",
    font=("Inter", 16 * -1)
)

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    956.0,
    419.0,
    image=image_image_2
)

canvas.create_text(
    1071.0,
    548.0,
    anchor="nw",
    text="SIZETEXT",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    1071.0,
    567.0,
    anchor="nw",
    text="ETATEXT",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    782.0,
    545.0,
    anchor="nw",
    text="Size estimation:",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    782.0,
    567.0,
    anchor="nw",
    text="Time estimation:",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    780.0,
    189.0,
    anchor="nw",
    text="Selected Items",
    fill="#000000",
    font=("Inter", 16 * -1)
)

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_1 clicked"),
    relief="flat"
)
button_1.place(
    x=294.0,
    y=181.69586181640625,
    width=199.43333435058594,
    height=98.9124984741211
)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_2 clicked"),
    relief="flat"
)
button_2.place(
    x=522.3834228515625,
    y=181.69586181640625,
    width=199.43333435058594,
    height=98.9124984741211
)

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_3 clicked"),
    relief="flat"
)
button_3.place(
    x=294.0,
    y=307.1458435058594,
    width=199.43333435058594,
    height=98.9124984741211
)

button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
button_4 = Button(
    image=button_image_4,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_4 clicked"),
    relief="flat"
)
button_4.place(
    x=522.3834228515625,
    y=307.1458435058594,
    width=199.43333435058594,
    height=98.9124984741211
)

button_image_5 = PhotoImage(
    file=relative_to_assets("button_5.png"))
button_5 = Button(
    image=button_image_5,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_5 clicked"),
    relief="flat"
)
button_5.place(
    x=294.0,
    y=432.5958251953125,
    width=199.43333435058594,
    height=98.9124984741211
)

canvas.create_rectangle(
    779.0,
    224.0,
    1134.0,
    531.0,
    fill="#EDECFD",
    outline="")

button_image_6 = PhotoImage(
    file=relative_to_assets("button_6.png"))
button_6 = Button(
    image=button_image_6,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_6 clicked"),
    relief="flat"
)
button_6.place(
    x=779.0,
    y=602.0,
    width=186.56666564941406,
    height=36.99166488647461
)

button_image_7 = PhotoImage(
    file=relative_to_assets("button_7.png"))
button_7 = Button(
    image=button_image_7,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_7 clicked"),
    relief="flat"
)
button_7.place(
    x=990.0,
    y=602.0,
    width=144.0,
    height=38.0
)

#SIDEBAR
image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    120.0,
    360.0,
    image=image_image_3
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    720.0,
    20.0,
    image=image_image_4
)

button_image_8 = PhotoImage(
    file=relative_to_assets("button_8.png"))
button_8 = Button(
    image=button_image_8,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("audits")],
    relief="flat"
)
button_8.place(
    x=17.0,
    y=356.0,
    width=215.0,
    height=44.0
)

button_image_9 = PhotoImage(
    file=relative_to_assets("button_9.png"))
button_9 = Button(
    image=button_image_9,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("recovers")],
    relief="flat"
)
button_9.place(
    x=17.0,
    y=302.0,
    width=215.0,
    height=44.0
)

button_image_10 = PhotoImage(
    file=relative_to_assets("button_10.png"))
button_10 = Button(
    image=button_image_10,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_10 clicked"),
    relief="flat"
)
button_10.place(
    x=17.0,
    y=246.0,
    width=215.0,
    height=44.0
)

button_image_11 = PhotoImage(
    file=relative_to_assets("button_11.png"))
button_11 = Button(
    image=button_image_11,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("explorers")],
    relief="flat"
)
button_11.place(
    x=16.8876953125,
    y=189.7833251953125,
    width=215.0,
    height=44.0
)

button_image_12 = PhotoImage(
    file=relative_to_assets("button_12.png"))
button_12 = Button(
    image=button_image_12,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("dashboards")],
    relief="flat"
)
button_12.place(
    x=18.0,
    y=136.0,
    width=215.0,
    height=44.0
)

image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    120.0,
    660.0,
    image=image_image_5
)

#LOGO
image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    120.0,
    50.0,
    image=image_image_6
)

canvas.create_text(
    173.0,
    636.0,
    anchor="nw",
    text="USERTEXT",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    173.0,
    664.0,
    anchor="nw",
    text="TIMETEXT",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    17.0,
    664.0,
    anchor="nw",
    text="Last login:",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    17.0,
    636.0,
    anchor="nw",
    text="Login as:",
    fill="#000000",
    font=("Inter", 12 * -1)
)

button_image_13 = PhotoImage(
    file=relative_to_assets("button_13.png"))
button_13 = Button(
    image=button_image_13,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_13 clicked"),
    relief="flat"
)
button_13.place(
    x=997.0,
    y=16.0,
    width=28.0,
    height=28.0
)

button_image_14 = PhotoImage(
    file=relative_to_assets("button_14.png"))
button_14 = Button(
    image=button_image_14,
    bg = "#FFFFFF", borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("logins")],
    relief="flat"
)
button_14.place(
    x=1047.0,
    y=12.0,
    width=123.0,
    height=36.7216796875
)

canvas.create_text(
    81.220703125,
    57.9000244140625,
    anchor="nw",
    text="2025",
    fill="#777779",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    80.41650390625,
    32.1666259765625,
    anchor="nw",
    text="EnshaVault",
    fill="#000000",
    font=("Inter", 18 * -1)
)

image_image_7 = PhotoImage(
    file=relative_to_assets("image_7.png"))
image_7 = canvas.create_image(
    47.0,
    50.0,
    image=image_image_7
)
window.resizable(False, False)
window.mainloop()
