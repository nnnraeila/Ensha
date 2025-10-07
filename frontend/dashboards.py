from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\MISI\PycharmProjects\Ensha\frontend\build\assets\frame3")


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
    600.0,
    350.0,
    image=image_image_1
)

canvas.create_rectangle(
    490.0,
    154.0,
    672.6436767578125,
    256.9885025024414,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    490.0,
    154.0,
    672.6436767578125,
    265.8390808105469,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    687.9541015625,
    154.0,
    870.5977783203125,
    265.8390808105469,
    fill="#FFFFFF",
    outline="")

canvas.create_text(
    502.87353515625,
    164.459716796875,
    anchor="nw",
    text="Total Backed Up",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_rectangle(
    293.0,
    154.0,
    476.0,
    266.0,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    898.0,
    147.0,
    1185.0,
    672.0,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    914.0,
    202.0,
    1170.0,
    651.0,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    294.0,
    290.0,
    871.0,
    672.0,
    fill="#FFFFFF",
    outline="")

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    922.700927734375,
    174.310302734375,
    image=image_image_2
)

image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    653.758544921875,
    168.9234619140625,
    image=image_image_3
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    851.386962890625,
    168.58251953125,
    image=image_image_4
)

image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    449.341064453125,
    169.6820068359375,
    image=image_image_5
)

canvas.create_rectangle(
    306.0,
    342.0,
    853.0,
    651.0,
    fill="#FFFFFF",
    outline="")

canvas.create_text(
    306.0,
    164.0,
    anchor="nw",
    text="Storage ",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    704.8505859375,
    162.0458984375,
    anchor="nw",
    text="Last Backed Up",
    fill="#000000",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    942.2529296875,
    163.896484375,
    anchor="nw",
    text="Alerts",
    fill="#000000",
    font=("Inter", 16 * -1)
)

canvas.create_text(
    313.0,
    305.0,
    anchor="nw",
    text="Recent Backup",
    fill="#000000",
    font=("Inter", 15 * -1)
)

canvas.create_text(
    313.0,
    236.0,
    anchor="nw",
    text="%GB",
    fill="#64636A",
    font=("Inter", 12 * -1)
)

canvas.create_text(
    610.0,
    217.0,
    anchor="nw",
    text="files",
    fill="#64636A",
    font=("Inter", 19 * -1)
)

canvas.create_text(
    293.6552734375,
    86.0,
    anchor="nw",
    text="Dashboard",
    fill="#38363B",
    font=("Inter Medium", 28 * -1)
)

canvas.create_text(
    511.0,
    193.0,
    anchor="nw",
    text="%NO",
    fill="#000000",
    font=("NunitoSans ExtraBold", 36 * -1)
)

canvas.create_text(
    704.8505859375,
    195.839111328125,
    anchor="nw",
    text="%DATE",
    fill="#000000",
    font=("NunitoSans ExtraBold", 32 * -1)
)

canvas.create_text(
    310.0,
    193.0,
    anchor="nw",
    text="%ST",
    fill="#000000",
    font=("NunitoSans ExtraBold", 36 * -1)
)

canvas.create_text(
    294.0,
    121.0,
    anchor="nw",
    text="Welcome, USERTEXT.",
    fill="#736F7C",
    font=("Inter", 16 * -1)
)

image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    120.0,
    360.0,
    image=image_image_6
)

image_image_7 = PhotoImage(
    file=relative_to_assets("image_7.png"))
image_7 = canvas.create_image(
    720.0,
    20.0,
    image=image_image_7
)

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    bg = "#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("audits")],
    relief="flat"
)
button_1.place(
    x=17.0,
    y=356.0,
    width=215.0,
    height=44.0
)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    bg = "#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("recovers")],
    relief="flat"
)
button_2.place(
    x=17.0,
    y=302.0,
    width=215.0,
    height=44.0
)

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    bg="#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("backups")],
    relief="flat"
)
button_3.place(
    x=17.0,
    y=246.0,
    width=215.0,
    height=44.0
)

button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
button_4 = Button(
    image=button_image_4,
    bg = "#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("explorers")],
    relief="flat"
)
button_4.place(
    x=16.8876953125,
    y=189.7833251953125,
    width=215.0,
    height=44.0
)

button_image_5 = PhotoImage(
    file=relative_to_assets("button_5.png"))
button_5 = Button(
    image=button_image_5,
    bg = "#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_5 clicked"),
    relief="flat"
)
button_5.place(
    x=18.0,
    y=136.0,
    width=215.0,
    height=44.0
)

image_image_8 = PhotoImage(
    file=relative_to_assets("image_8.png"))
image_8 = canvas.create_image(
    120.0,
    660.0,
    image=image_image_8
)

#LOGO
image_image_9 = PhotoImage(
    file=relative_to_assets("image_9.png"))
image_9 = canvas.create_image(
    120.0,
    50.0,
    image=image_image_9
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

button_image_6 = PhotoImage(
    file=relative_to_assets("button_6.png"))
button_6 = Button(
    image=button_image_6,
    bg = "#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_6 clicked"),
    relief="flat"
)
button_6.place(
    x=997.0,
    y=16.0,
    width=28.0,
    height=28.0
)

button_image_7 = PhotoImage(
    file=relative_to_assets("button_7.png"))
button_7 = Button(
    image=button_image_7,
    bg = "#FFFFFF",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: [window.destroy(), __import__("logins")],
    relief="flat"
)
button_7.place(
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

image_image_10 = PhotoImage(
    file=relative_to_assets("image_10.png"))
image_10 = canvas.create_image(
    47.0,
    50.0,
    image=image_image_10
)
window.resizable(False, False)
window.mainloop()
