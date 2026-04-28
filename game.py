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
    
    def get_king_moves(self, r, c):
        moves = []
        piece = self.board[r][c]

        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]

                # empty OR enemy piece
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))

        return moves


    # def get_valid_moves(self, r, c):
    #     piece = self.board[r][c]

    #     if piece == '.':
    #         return []

    #     if piece.lower() == 'p':
    #         return self.get_pawn_moves(r, c)
    #     elif piece.lower() == 'r':
    #         return self.get_rook_moves(r, c)
    #     elif piece.lower() == 'n':
    #         return self.get_knight_moves(r, c)
    #     elif piece.lower() == 'b':
    #         return self.get_bishop_moves(r, c)
    #     elif piece.lower() == 'm':
    #         return self.get_met_moves(r, c)
    #     elif piece.lower() == 'k':
    #         return self.get_king_moves(r, c)
    #     return []

    # -------------------- game logic --------------------
    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end

        piece = self.board[sr][sc]

        # move piece
        self.board[er][ec] = piece
        self.board[sr][sc] = '.'

        # 🔥 Pawn promotion
        if piece == 'P' and er == 2:
            self.board[er][ec] = 'M'
        elif piece == 'p' and er == 5:
            self.board[er][ec] = 'm'



# # -------------------- check system --------------------

    def find_king(self, is_white):
        target = 'K' if is_white else 'k'

        for i in range(8):
            for j in range(8):
                if self.board[i][j] == target:
                    return (i, j)

        return None

    def is_square_attacked(self, r, c, by_white):
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]

                if piece == '.':
                    continue

                # enemy pieces only
                if by_white and piece.isupper():
                    moves = self.get_raw_moves(i, j)
                    if (r, c) in moves:
                        return True

                if not by_white and piece.islower():
                    moves = self.get_raw_moves(i, j)
                    if (r, c) in moves:
                        return True

        return False

    def get_raw_moves(self, r, c):
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

    def is_in_check(self, is_white):
        king_pos = self.find_king(is_white)

        if king_pos is None:
            return False

        r, c = king_pos

        return self.is_square_attacked(r, c, not is_white)

    def try_move(self, start, end):
        sr, sc = start
        er, ec = end

        piece = self.board[sr][sc]
        captured = self.board[er][ec]

        # make move
        self.board[er][ec] = piece
        self.board[sr][sc] = '.'

        # check condition
        is_white = piece.isupper()
        in_check = self.is_in_check(is_white)

        # undo move
        self.board[sr][sc] = piece
        self.board[er][ec] = captured

        return not in_check

    def get_valid_moves(self, r, c):
        moves = self.get_raw_moves(r, c)

        valid = []
        for move in moves:
            if self.try_move((r, c), move):
                valid.append(move)

        return valid

    def handle_click(self, r, c):
        if self.is_in_check(self.turn == 0):
            print("CHECK!")
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