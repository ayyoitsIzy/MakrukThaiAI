import tkinter as tk
from game import Game

game = Game()
buttons = []

def on_click(r, c):
    game.handle_click(r, c)
    update_board()

def update_board():
    for i in range(8):
        for j in range(8):
            buttons[i][j]['text'] = game.board[i][j]

root = tk.Tk()
root.title("Thai Chess (Makruk)")

for i in range(8):
    row = []
    for j in range(8):
        btn = tk.Button(
            root,
            text=game.board[i][j],
            width=4,
            height=2,
            command=lambda r=i, c=j: on_click(r, c)
        )
        btn.grid(row=i, column=j)
        row.append(btn)
    buttons.append(row)

root.mainloop()