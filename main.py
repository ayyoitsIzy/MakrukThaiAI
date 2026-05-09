import tkinter as tk
from tkinter import messagebox
from game import Game

# ── Piece mapping ──────────────────────────────────────────────────────────────
PIECE_UNICODE = {
    'K': '♔', 'M': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'm': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
}

# ── Colors ─────────────────────────────────────────────────────────────────────
LIGHT_SQ     = '#F0D9B5'
DARK_SQ      = '#B58863'
SELECTED_COL = '#F6F669'
MOVE_DOT_COL = '#3D3D3D'
CAPTURE_COL  = '#E74C3C'
LAST_MOVE_COL= '#CDD16E'
CHECK_COL    = '#FF6B6B'

BOARD_BORDER = '#5C3D1E'
COORD_FG     = '#8B5E3C'

SQUARE_SIZE  = 80
BOARD_OFFSET = 30
CANVAS_SIZE  = SQUARE_SIZE * 8 + BOARD_OFFSET * 2

AI_DELAY_MS  = 600   # หน่วง ms ระหว่างการเดินของ AI ใน AI vs AI

# ── Modes ──────────────────────────────────────────────────────────────────────
MODE_HVA = 'human_vs_ai'
MODE_AVA = 'ai_vs_ai'
MODE_HVH = 'human_vs_human'

# ── App ────────────────────────────────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Makruk — Thai Chess')
        self.root.resizable(False, False)
        self.root.configure(bg='#2C1810')

        self.mode        = MODE_HVA
        self.game        = Game()
        self.valid_moves = []
        self.last_move   = None
        self._ai_job     = None       # after() job id สำหรับ AI vs AI

        self._build_ui()
        self.draw_board()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Mode selector ──
        mode_frame = tk.Frame(self.root, bg='#2C1810')
        mode_frame.pack(pady=(16, 0))

        tk.Label(
            mode_frame, text='โหมด:', font=('Georgia', 12),
            bg='#2C1810', fg='#F0D9B5',
        ).pack(side='left', padx=(0, 8))

        self.mode_var = tk.StringVar(value=MODE_HVA)
        modes = [
            ('👤 vs 🤖  Human vs AI',    MODE_HVA),
            ('🤖 vs 🤖  AI vs AI',        MODE_AVA),
            ('👤 vs 👤  Human vs Human',  MODE_HVH),
        ]
        for label, val in modes:
            tk.Radiobutton(
                mode_frame, text=label, variable=self.mode_var, value=val,
                font=('Georgia', 11), bg='#2C1810', fg='#F0D9B5',
                selectcolor='#5C3D1E', activebackground='#2C1810',
                activeforeground='#F0D9B5',
                command=self._on_mode_change,
            ).pack(side='left', padx=6)

        # ── Canvas ──
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg='#2C1810', highlightthickness=0,
        )
        self.canvas.pack(padx=20, pady=12)
        self.canvas.bind('<Button-1>', self.on_click)

        # ── Status bar ──
        self.status_var = tk.StringVar(value="White's turn")
        tk.Label(
            self.root, textvariable=self.status_var,
            font=('Georgia', 14), bg='#2C1810', fg='#F0D9B5', pady=6,
        ).pack()

        # ── Restart button ──
        tk.Button(
            self.root, text='🔄  เริ่มเกมใหม่',
            font=('Georgia', 12), bg='#5C3D1E', fg='#F0D9B5',
            activebackground='#7A5230', activeforeground='#FFFFFF',
            relief='flat', padx=16, pady=6, cursor='hand2',
            command=self.restart_game,
        ).pack(pady=(0, 16))

    def _on_mode_change(self):
        self.mode = self.mode_var.get()
        self.restart_game()

    # ── Drawing ────────────────────────────────────────────────────────────────
    def sq_to_xy(self, r, c):
        return BOARD_OFFSET + c * SQUARE_SIZE, BOARD_OFFSET + r * SQUARE_SIZE

    def find_king_pos(self, is_white):
        target = 'K' if is_white else 'k'
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] == target:
                    return (r, c)
        return None

    def draw_board(self):
        self.canvas.delete('all')
        self.root.update_idletasks()
        self.canvas.update()

        in_check  = self.game.is_in_check(self.game.turn == 0)
        king_pos  = self.find_king_pos(self.game.turn == 0) if in_check else None
        selected  = self.game.selected
        valid_set = set(self.valid_moves)

        bx = BOARD_OFFSET - 3
        bw = SQUARE_SIZE * 8 + 6
        self.canvas.create_rectangle(bx, bx, bx + bw, bx + bw,
                                     fill=BOARD_BORDER, outline='')

        for r in range(8):
            for c in range(8):
                x, y = self.sq_to_xy(r, c)
                base  = LIGHT_SQ if (r + c) % 2 == 0 else DARK_SQ

                if selected and (r, c) == selected:
                    color = SELECTED_COL
                elif self.last_move and (r, c) in self.last_move:
                    color = LAST_MOVE_COL
                elif king_pos and (r, c) == king_pos:
                    color = CHECK_COL
                else:
                    color = base

                self.canvas.create_rectangle(
                    x, y, x + SQUARE_SIZE, y + SQUARE_SIZE,
                    fill=color, outline='')

                if (r, c) in valid_set:
                    piece = self.game.board[r][c]
                    if piece == '.':
                        cx = x + SQUARE_SIZE // 2
                        cy = y + SQUARE_SIZE // 2
                        r2 = SQUARE_SIZE * 0.15
                        self.canvas.create_oval(
                            cx-r2, cy-r2, cx+r2, cy+r2,
                            fill=MOVE_DOT_COL, outline='', stipple='gray50')
                    else:
                        pad = 4
                        self.canvas.create_rectangle(
                            x+pad, y+pad, x+SQUARE_SIZE-pad, y+SQUARE_SIZE-pad,
                            fill='', outline=CAPTURE_COL, width=3)

                piece = self.game.board[r][c]
                if piece != '.':
                    sym    = PIECE_UNICODE.get(piece, piece)
                    white  = piece.isupper()
                    fg     = '#FFFFFF' if white else '#1A1A1A'
                    shadow = '#1A1A1A' if white else '#888888'
                    cx = x + SQUARE_SIZE // 2
                    cy = y + SQUARE_SIZE // 2 + 2
                    self.canvas.create_text(cx+1, cy+1, text=sym,
                                            font=('Segoe UI Symbol', 34),
                                            fill=shadow, anchor='center')
                    self.canvas.create_text(cx, cy, text=sym,
                                            font=('Segoe UI Symbol', 34),
                                            fill=fg, anchor='center')

        files = 'abcdefgh'
        for i in range(8):
            fx = BOARD_OFFSET + i * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_text(fx, BOARD_OFFSET + 8*SQUARE_SIZE + 12,
                                    text=files[i], font=('Georgia', 11), fill=COORD_FG)
            self.canvas.create_text(BOARD_OFFSET - 14,
                                    BOARD_OFFSET + i*SQUARE_SIZE + SQUARE_SIZE//2,
                                    text=str(8-i), font=('Georgia', 11), fill=COORD_FG)

    # ── AI scheduling ──────────────────────────────────────────────────────────
    def _is_ai_turn(self):
        if self.mode == MODE_AVA:
            return True
        if self.mode == MODE_HVA:
            return self.game.turn == 1   # Black เป็น AI
        return False

    def _schedule_ai(self):
        if self._ai_job:
            self.root.after_cancel(self._ai_job)
        self._ai_job = self.root.after(AI_DELAY_MS, self._do_ai_move)

    def _do_ai_move(self):
        self._ai_job = None
        if self.game.game_over:
            return

        ai_move = self.game.get_best_move(4)
        if not ai_move:
            return

        start, end = ai_move
        self.last_move = (start, end)
        self.game.move_piece(start, end)
        self.game.turn = 1 - self.game.turn
        self.game._record_position()   # บันทึก position จริง (ไม่ใช่ simulate)

        status = self.game.get_game_status()
        if status:
            self.game.game_over = True

        self.update_status()
        self.draw_board()

        if status:
            self.root.after(100, lambda: self.show_game_over(status))
            return

        # AI vs AI — นัดรอบถัดไป
        if self.mode == MODE_AVA and not self.game.game_over:
            self._schedule_ai()

    # ── Input ──────────────────────────────────────────────────────────────────
    def on_click(self, event):
        if self.game.game_over or self._is_ai_turn():
            return

        c = (event.x - BOARD_OFFSET) // SQUARE_SIZE
        r = (event.y - BOARD_OFFSET) // SQUARE_SIZE
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        prev_selected = self.game.selected
        if prev_selected and (r, c) in self.valid_moves:
            self.last_move = (prev_selected, (r, c))

        moved = self._human_click(r, c)

        if self.game.selected:
            sr, sc = self.game.selected
            self.valid_moves = self.game.get_valid_moves(sr, sc)
        else:
            self.valid_moves = []

        self.update_status()
        self.draw_board()

        if moved:
            status = self.game.get_game_status()
            if status:
                self.game.game_over = True
                self.root.after(100, lambda: self.show_game_over(status))
                return
            if self._is_ai_turn():
                self._schedule_ai()

    def _human_click(self, r, c):
        """จัดการคลิกของผู้เล่น คืน True ถ้ามีการเดินจริง"""
        piece = self.game.board[r][c]

        if self.game.selected is None:
            if piece != '.' and self.game.check_turn(piece):
                self.game.selected = (r, c)
            return False

        sr, sc = self.game.selected
        if (r, c) == (sr, sc):
            self.game.selected = None
            return False
        if piece != '.' and self.game.check_turn(piece):
            self.game.selected = (r, c)
            return False

        valid_moves = self.game.get_valid_moves(sr, sc)
        if (r, c) in valid_moves:
            self.game.move_piece((sr, sc), (r, c))
            self.game.turn = 1 - self.game.turn
            self.game._record_position()   # บันทึก position จริง
            self.game.selected = None
            return True

        self.game.selected = None
        return False

    # ── Game over ──────────────────────────────────────────────────────────────
    def show_game_over(self, status):
        if self._ai_job:
            self.root.after_cancel(self._ai_job)
            self._ai_job = None

        turn_name = 'White' if self.game.turn == 0 else 'Black'
        if status == 'checkmate':
            winner  = 'Black' if self.game.turn == 0 else 'White'
            title   = '♚  Checkmate!'
            message = f'{turn_name} ถูกรุกจนแพ้\n\n🏆  {winner} ชนะ!'
        elif status == 'stalemate':
            title   = '🤝  หมากอับ (Stalemate)!'
            message = f'{turn_name} ไม่มีตาเดิน แต่ไม่ถูกรุก\n\nเกมเสมอ!'
        elif status == 'threefold':
            title   = '🔁  รุกล้อ / เดินล้อ!'
            message = 'ตำแหน่งหมากซ้ำเดิมครบ 3 ครั้ง\n\nเกมเสมอ!'
        else:  # bare_king
            title   = '👑  ขุนคู่ขุน!'
            message = 'ทั้งสองฝ่ายเหลือเพียงขุน\nไม่สามารถรุกจนได้\n\nเกมเสมอ!'

        answer = messagebox.askquestion(title, message + '\n\nต้องการเริ่มเกมใหม่ไหม?',
                                        icon='info')
        if answer == 'yes':
            self.restart_game()

    def restart_game(self):
        if self._ai_job:
            self.root.after_cancel(self._ai_job)
            self._ai_job = None

        self.mode        = self.mode_var.get()
        self.game        = Game()
        self.valid_moves = []
        self.last_move   = None
        self.status_var.set("White's turn")
        self.draw_board()

        if self._is_ai_turn():
            self._schedule_ai()

    def update_status(self):
        if self.game.game_over:
            return
        turn_name = 'White' if self.game.turn == 0 else 'Black'
        is_white  = self.game.turn == 0
        mode_label = {
            MODE_HVA: '🤖 AI'     if self.game.turn == 1 else '👤 Human',
            MODE_AVA: '🤖 AI',
            MODE_HVH: '👤 Human',
        }.get(self.mode, '')

        if self.game.is_in_check(is_white):
            self.status_var.set(f'⚠  {turn_name} is in CHECK!  [{mode_label}]')
        else:
            self.status_var.set(f"{turn_name}'s turn  [{mode_label}]")


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()