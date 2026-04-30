import tkinter as tk
from game import Game

# ── Piece mapping ──────────────────────────────────────────────────────────────
# Makruk pieces mapped to Unicode chess symbols
# White (upper): K=King, M=Queen(Met), R=Rook, B=Bishop(Khon), N=Knight, P=Pawn
# Black (lower): same letters lowercase

PIECE_UNICODE = {
    'K': '♔', 'M': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'm': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
}

# ── Colors ─────────────────────────────────────────────────────────────────────
LIGHT_SQ     = '#F0D9B5'
DARK_SQ      = '#B58863'
SELECTED_COL = '#F6F669'   # yellow highlight for selected square
MOVE_DOT_COL = '#3D3D3D'   # dot for valid moves on empty squares
CAPTURE_COL  = '#E74C3C'   # red tint for capturable squares
LAST_MOVE_COL= '#CDD16E'   # subtle green for last-move squares
CHECK_COL    = '#FF6B6B'   # red for king-in-check square

BOARD_BORDER = '#5C3D1E'
COORD_FG     = '#8B5E3C'

SQUARE_SIZE  = 80
BOARD_OFFSET = 30          # space for rank/file labels
CANVAS_SIZE  = SQUARE_SIZE * 8 + BOARD_OFFSET * 2

# ── App ────────────────────────────────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Makruk — Thai Chess')
        self.root.resizable(False, False)
        self.root.configure(bg='#2C1810')

        self.game = Game()
        self.valid_moves = []
        self.last_move   = None   # (start, end)

        # ── Canvas ──
        self.canvas = tk.Canvas(
            root,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg='#2C1810',
            highlightthickness=0,
        )
        self.canvas.pack(padx=20, pady=20)
        self.canvas.bind('<Button-1>', self.on_click)

        # ── Status bar ──
        self.status_var = tk.StringVar(value="White's turn")
        status = tk.Label(
            root,
            textvariable=self.status_var,
            font=('Georgia', 14),
            bg='#2C1810',
            fg='#F0D9B5',
            pady=6,
        )
        status.pack()

        self.draw_board()

    # ── Drawing ────────────────────────────────────────────────────────────────
    def sq_to_xy(self, r, c):
        """Top-left pixel of square (r, c)."""
        x = BOARD_OFFSET + c * SQUARE_SIZE
        y = BOARD_OFFSET + r * SQUARE_SIZE
        return x, y

    def find_king_pos(self, is_white):
        target = 'K' if is_white else 'k'
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] == target:
                    return (r, c)
        return None

    def draw_board(self):
        self.canvas.delete('all')

        in_check     = self.game.is_in_check(self.game.turn == 0)
        king_pos     = self.find_king_pos(self.game.turn == 0) if in_check else None
        selected     = self.game.selected
        valid_set    = set(self.valid_moves)

        # ── Border ──
        bx = BOARD_OFFSET - 3
        by = BOARD_OFFSET - 3
        bw = SQUARE_SIZE * 8 + 6
        self.canvas.create_rectangle(bx, by, bx + bw, by + bw,
                                     fill=BOARD_BORDER, outline='')

        # ── Squares ──
        for r in range(8):
            for c in range(8):
                x, y = self.sq_to_xy(r, c)
                base_color = LIGHT_SQ if (r + c) % 2 == 0 else DARK_SQ

                # Layer highlights
                if selected and (r, c) == selected:
                    color = SELECTED_COL
                elif self.last_move and (r, c) in self.last_move:
                    color = LAST_MOVE_COL
                elif king_pos and (r, c) == king_pos:
                    color = CHECK_COL
                else:
                    color = base_color

                self.canvas.create_rectangle(
                    x, y, x + SQUARE_SIZE, y + SQUARE_SIZE,
                    fill=color, outline='',
                )

                # ── Valid move indicators ──
                if (r, c) in valid_set:
                    piece = self.game.board[r][c]
                    if piece == '.':
                        # Dot in center of empty square
                        cx = x + SQUARE_SIZE // 2
                        cy = y + SQUARE_SIZE // 2
                        r2 = SQUARE_SIZE * 0.15
                        self.canvas.create_oval(
                            cx - r2, cy - r2, cx + r2, cy + r2,
                            fill=MOVE_DOT_COL, outline='', stipple='gray50',
                        )
                    else:
                        # Capture ring
                        pad = 4
                        self.canvas.create_rectangle(
                            x + pad, y + pad,
                            x + SQUARE_SIZE - pad, y + SQUARE_SIZE - pad,
                            fill='', outline=CAPTURE_COL, width=3,
                        )

                # ── Piece ──
                piece = self.game.board[r][c]
                if piece != '.':
                    symbol   = PIECE_UNICODE.get(piece, piece)
                    is_white_piece = piece.isupper()
                    fg       = '#FFFFFF' if is_white_piece else '#1A1A1A'
                    shadow   = '#1A1A1A' if is_white_piece else '#888888'

                    cx = x + SQUARE_SIZE // 2
                    cy = y + SQUARE_SIZE // 2 + 2   # slight vertical nudge

                    # Shadow for legibility
                    self.canvas.create_text(
                        cx + 1, cy + 1,
                        text=symbol,
                        font=('Segoe UI Symbol', 38),
                        fill=shadow,
                        anchor='center',
                    )
                    self.canvas.create_text(
                        cx, cy,
                        text=symbol,
                        font=('Segoe UI Symbol', 38),
                        fill=fg,
                        anchor='center',
                    )

        # ── Coordinates ──
        files = 'abcdefgh'
        for i in range(8):
            # File labels (bottom)
            fx = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2
            fy = BOARD_OFFSET + 8 * SQUARE_SIZE + 12
            self.canvas.create_text(fx, fy, text=files[i],
                                    font=('Georgia', 11), fill=COORD_FG)
            # Rank labels (left)  — rank 8 at top
            rx = BOARD_OFFSET - 14
            ry = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_text(rx, ry, text=str(8 - i),
                                    font=('Georgia', 11), fill=COORD_FG)

    # ── Input ──────────────────────────────────────────────────────────────────
    def on_click(self, event):
        c = (event.x - BOARD_OFFSET) // SQUARE_SIZE
        r = (event.y - BOARD_OFFSET) // SQUARE_SIZE

        if not (0 <= r < 8 and 0 <= c < 8):
            return

        prev_selected = self.game.selected

        # If we're about to make a move, record it for last-move highlight
        if prev_selected and (r, c) in self.valid_moves:
            self.last_move = (prev_selected, (r, c))

        self.game.handle_click(r, c)

        # Update valid moves for newly selected piece
        if self.game.selected:
            sr, sc = self.game.selected
            self.valid_moves = self.game.get_valid_moves(sr, sc)
        else:
            self.valid_moves = []

        self.update_status()
        self.draw_board()

    def update_status(self):
        turn_name = 'White' if self.game.turn == 0 else 'Black'
        is_white  = self.game.turn == 0

        if self.game.is_in_check(is_white):
            self.status_var.set(f'⚠  {turn_name} is in CHECK!')
        else:
            self.status_var.set(f"{turn_name}'s turn")


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()