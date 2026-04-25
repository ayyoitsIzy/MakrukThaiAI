import tkinter as tk

class Game:
    def __init__(self):
        self.board = [
            ['r','n','b','m','k','b','n','r'],
            ['.','.','.','.','.','.','.','.'],
            ['p','p','p','p','p','p','p','p'],
            ['.','.','.','.','.','.','.','.'],
            ['.','.','.','.','.','.','.','.'],
            ['P','P','P','P','P','P','P','P'],
            ['.','.','.','.','.','.','.','.'],
            ['R','N','B','K','M','B','N','R']
        ]

        self.selected = None
        self.turn = 0  # 0 = white, 1 = black

    # -------------------- helpers --------------------
    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def check_turn(self, piece):
        if piece.isupper() and self.turn == 0:
            return True
        if piece.islower() and self.turn == 1:
            return True
        return False

    # -------------------- moves --------------------
    def get_pawn_moves(self, r, c):
        moves = []
        piece = self.board[r][c]

        direction = -1 if piece.isupper() else 1

        if self.is_in_bounds(r + direction, c) and self.board[r + direction][c] == '.':
            moves.append((r + direction, c))

        for dc in [-1, 1]:
            nr, nc = r + direction, c + dc
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target != '.' and target.isupper() != piece.isupper():
                    moves.append((nr, nc))

        return moves

    def get_rook_moves(self, r, c):
        moves = []
        piece = self.board[r][c]

        directions = [(-1,0),(1,0),(0,-1),(0,1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            while self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]

                if target == '.':
                    moves.append((nr, nc))
                else:
                    if target.isupper() != piece.isupper():
                        moves.append((nr, nc))
                    break

                nr += dr
                nc += dc

        return moves
    
    def get_knight_moves(self, r, c):
        moves = []
        piece = self.board[r][c]

        directions = [
            (-2,-1), (-2,1),
            (-1,-2), (-1,2),
            (1,-2), (1,2),
            (2,-1), (2,1)
        ]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))

        return moves
    
    def get_met_moves(self, r, c):
        moves = []
        piece = self.board[r][c]

        # Diagonal 1 step
        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))

        return moves
    
    def get_bishop_moves(self, r, c):
        moves = []
        piece = self.board[r][c]

        directions = [(-1,-1), (-1,1), (1,-1), (1,1)]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))
       

        # Forward 1 step
        direction = -1 if piece.isupper() else 1
        nr, nc = r + direction, c

        if self.is_in_bounds(nr, nc):
            target = self.board[nr][nc]
            if target == '.' or target.isupper() != piece.isupper():
                moves.append((nr, nc))

        return moves
    


    def get_valid_moves(self, r, c):
        piece = self.board[r][c]

        if piece == '.':
            return []

        if piece.lower() == 'p':
            return self.get_pawn_moves(r, c)
        elif piece.lower() == 'r':
            return self.get_rook_moves(r, c)
        elif piece.lower() == 'n':
            return self.get_knight_moves(r, c)
        elif piece.lower() == 'b':
            return self.get_bishop_moves(r, c)
        elif piece.lower() == 'm':
            return self.get_met_moves(r, c)
        elif piece.lower() == 'k':
            return self.get_king_moves(r, c)
        return []

    # -------------------- game logic --------------------
    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end

        self.board[er][ec] = self.board[sr][sc]
        self.board[sr][sc] = '.'

    def handle_click(self, r, c):
        if self.selected is None:
            if self.board[r][c] != '.' and self.check_turn(self.board[r][c]):
                self.selected = (r, c)
        else:
            sr, sc = self.selected
            valid_moves = self.get_valid_moves(sr, sc)

            if (r, c) in valid_moves:
                self.move_piece(self.selected, (r, c))
                self.turn = 1 - self.turn
            else:
                print("illegal move")

            self.selected = None


# # -------------------- UI --------------------

# game = Game()
# buttons = []

# def on_click(r, c):
#     game.handle_click(r, c)
#     update_board()

# def update_board():
#     for i in range(8):
#         for j in range(8):
#             buttons[i][j]['text'] = game.board[i][j]

# root = tk.Tk()

# for i in range(8):
#     row = []
#     for j in range(8):
#         btn = tk.Button(root, text=game.board[i][j],
#                         width=4, height=2,
#                         command=lambda r=i, c=j: on_click(r, c))
#         btn.grid(row=i, column=j)
#         row.append(btn)
#     buttons.append(row)

# root.mainloop()