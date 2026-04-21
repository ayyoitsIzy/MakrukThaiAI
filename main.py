import tkinter as tk
import game


board = game.get_board()

root = tk.Tk()

for i in range(8):
    row = []
    for j in range(8):
        btn = tk.Button(root, text=board[i][j], width=4, height=2,
                        command=lambda r=i, c=j: game.on_click(r, c))
        btn.grid(row=i, column=j)
        row.append(btn)

    
    buttons = game.get_buttons()
    buttons.append(row)

root.mainloop()