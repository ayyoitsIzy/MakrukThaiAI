import random

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
        self.selected  = None
        self.turn      = 0
        self.game_over = False

        # --- Transposition Table ---
        self.tt = {}
        self.zobrist = {}
        pieces = 'pnbrmkPNBRMK'
        for p in pieces:
            for r in range(8):
                for c in range(8):
                    self.zobrist[(p, r, c)] = random.getrandbits(64)
        self.zobrist_turn = random.getrandbits(64)
        self.hash = self._compute_hash()

        # --- Killer Moves ---
        self.killers = [[None, None] for _ in range(20)]

        # --- รุกล้อ / เดินล้อ: นับจำนวนครั้งที่ position ซ้ำ ---
        # ใช้ Zobrist hash เป็น key  (hash รวม turn อยู่แล้ว)
        self.position_history = {self.hash: 1}

    # -------------------- Zobrist --------------------
    def _compute_hash(self):
        h = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p != '.':
                    h ^= self.zobrist[(p, r, c)]
        if self.turn == 0:
            h ^= self.zobrist_turn
        return h

    def _update_hash(self, piece, r, c, captured, er, ec, promoted_to):
        h = self.hash
        h ^= self.zobrist[(piece, r, c)]
        if captured != '.':
            h ^= self.zobrist[(captured, er, ec)]
        p_placed = promoted_to if promoted_to else piece
        h ^= self.zobrist[(p_placed, er, ec)]
        h ^= self.zobrist_turn
        return h

    # -------------------- Piece-Square Tables --------------------
    PAWN_TABLE = [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [ 5, 10, 10,-20,-20, 10, 10,  5],
        [ 5, -5,-10,  0,  0,-10, -5,  5],
        [ 0,  0,  0, 20, 20,  0,  0,  0],
        [ 5,  5, 10, 25, 25, 10,  5,  5],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [ 0,  0,  0,  0,  0,  0,  0,  0],
    ]
    KNIGHT_TABLE = [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ]
    BISHOP_TABLE = [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ]
    ROOK_TABLE = [
        [ 0,  0,  0,  5,  5,  0,  0,  0],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [ 5, 10, 10, 10, 10, 10, 10,  5],
        [ 0,  0,  0,  0,  0,  0,  0,  0],
    ]
    MET_TABLE = [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ]
    KING_TABLE = [
        [ 20, 30, 10,  0,  0, 10, 30, 20],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
    ]
    PIECE_VALUES = {
        'p': 100, 'n': 320, 'b': 330,
        'r': 500, 'm': 400, 'k': 20000
    }

    # -------------------- helpers --------------------
    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def check_turn(self, piece):
        if piece.isupper() and self.turn == 0: return True
        if piece.islower() and self.turn == 1: return True
        return False

    def get_piece_table(self, piece_lower):
        return {
            'p': self.PAWN_TABLE, 'n': self.KNIGHT_TABLE,
            'b': self.BISHOP_TABLE, 'r': self.ROOK_TABLE,
            'm': self.MET_TABLE,   'k': self.KING_TABLE,
        }.get(piece_lower)

    # -------------------- move generators --------------------
    def get_pawn_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        direction = -1 if piece.isupper() else 1
        if self.is_in_bounds(r+direction, c) and self.board[r+direction][c] == '.':
            moves.append((r+direction, c))
        for dc in [-1, 1]:
            nr, nc = r+direction, c+dc
            if self.is_in_bounds(nr, nc):
                t = self.board[nr][nc]
                if t != '.' and t.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    def get_rook_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            while self.is_in_bounds(nr, nc):
                t = self.board[nr][nc]
                if t == '.':
                    moves.append((nr, nc))
                else:
                    if t.isupper() != piece.isupper():
                        moves.append((nr, nc))
                    break
                nr += dr; nc += dc
        return moves

    def get_knight_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r+dr, c+dc
            if self.is_in_bounds(nr, nc):
                t = self.board[nr][nc]
                if t == '.' or t.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    def get_met_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if self.is_in_bounds(nr, nc):
                t = self.board[nr][nc]
                if t == '.' or t.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    def get_bishop_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if self.is_in_bounds(nr, nc):
                t = self.board[nr][nc]
                if t == '.' or t.isupper() != piece.isupper():
                    moves.append((nr, nc))
        direction = -1 if piece.isupper() else 1
        nr, nc = r+direction, c
        if self.is_in_bounds(nr, nc):
            t = self.board[nr][nc]
            if t == '.' or t.isupper() != piece.isupper():
                moves.append((nr, nc))
        return moves

    def get_king_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr, nc = r+dr, c+dc
            if self.is_in_bounds(nr, nc):
                t = self.board[nr][nc]
                if t == '.' or t.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    # -------------------- move execution --------------------
    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end
        piece    = self.board[sr][sc]
        captured = self.board[er][ec]

        self.board[er][ec] = piece
        self.board[sr][sc] = '.'

        promoted_to = None
        if piece == 'P' and er == 2:
            self.board[er][ec] = 'M'; promoted_to = 'M'
        elif piece == 'p' and er == 5:
            self.board[er][ec] = 'm'; promoted_to = 'm'

        self.hash = self._update_hash(piece, sr, sc, captured, er, ec, promoted_to)
        return captured

    def _record_position(self):
        """บันทึก position จริงลง history (เรียกหลังเดินจริงเท่านั้น ไม่เรียกใน minimax)"""
        self.position_history[self.hash] = self.position_history.get(self.hash, 0) + 1

    # -------------------- check system --------------------
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
                if piece == '.': continue
                if by_white and piece.isupper():
                    if (r, c) in self.get_raw_moves(i, j): return True
                if not by_white and piece.islower():
                    if (r, c) in self.get_raw_moves(i, j): return True
        return False

    def get_raw_moves(self, r, c):
        piece = self.board[r][c]
        if piece == '.': return []
        p = piece.lower()
        if p == 'p': return self.get_pawn_moves(r, c)
        if p == 'r': return self.get_rook_moves(r, c)
        if p == 'n': return self.get_knight_moves(r, c)
        if p == 'b': return self.get_bishop_moves(r, c)
        if p == 'm': return self.get_met_moves(r, c)
        if p == 'k': return self.get_king_moves(r, c)
        return []

    def is_in_check(self, is_white):
        king_pos = self.find_king(is_white)
        if king_pos is None: return False
        return self.is_square_attacked(king_pos[0], king_pos[1], not is_white)

    def try_move(self, start, end):
        sr, sc = start
        er, ec = end
        piece    = self.board[sr][sc]
        captured = self.board[er][ec]
        saved    = self.hash

        self.board[er][ec] = piece
        self.board[sr][sc] = '.'
        if piece == 'P' and er == 2: self.board[er][ec] = 'M'
        elif piece == 'p' and er == 5: self.board[er][ec] = 'm'

        in_check = self.is_in_check(piece.isupper())

        self.board[sr][sc] = piece
        self.board[er][ec] = captured
        self.hash = saved
        return not in_check

    def get_valid_moves(self, r, c):
        return [m for m in self.get_raw_moves(r, c) if self.try_move((r, c), m)]

    # ══════════════════════════════════════════════════════════════
    #  Game Status — ตามกฎหมากรุกไทยที่ถูกต้อง
    # ══════════════════════════════════════════════════════════════

    def _count_pieces(self):
        """นับหมากทุกตัวบนกระดาน คืน dict {piece_lower: count} แยกฝ่าย"""
        white = {}; black = {}
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p == '.': continue
                d = white if p.isupper() else black
                key = p.lower()
                d[key] = d.get(key, 0) + 1
        return white, black

    def is_bare_king_draw(self):
        """
        เสมอทันทีเมื่อทั้งสองฝ่ายเหลือเพียงขุน 1 ตัว
        (ขุนคู่ขุน ไม่สามารถรุกจนได้)
        """
        white, black = self._count_pieces()
        w_only_king = list(white.keys()) == ['k'] and white['k'] == 1
        b_only_king = list(black.keys()) == ['k'] and black['k'] == 1
        return w_only_king and b_only_king

    def has_any_legal_move(self, is_white):
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p == '.': continue
                if is_white and p.isupper() and self.get_valid_moves(r, c):
                    return True
                if not is_white and p.islower() and self.get_valid_moves(r, c):
                    return True
        return False

    def get_game_status(self):
        """
        ตรวจสถานะเกมตามกฎหมากรุกไทย:

          'bare_king'   — ขุนคู่ขุน → เสมอทันที
          'threefold'   — รุกล้อ/เดินล้อ ซ้ำตำแหน่งเดิมครบ 3 ครั้ง → เสมอ
          'stalemate'   — หมากอับ (ไม่ถูกรุก แต่เดินไม่ได้) → เสมอ
          'checkmate'   — ถูกรุกและเดินไม่พ้น → แพ้
          None          — เกมยังดำเนินต่อ
        """
        # 1. ขุนคู่ขุน → เสมอทันที
        if self.is_bare_king_draw():
            return 'bare_king'

        # 2. รุกล้อ — position ซ้ำครบ 3 ครั้ง → เสมอ
        if self.position_history.get(self.hash, 0) >= 3:
            return 'threefold'

        is_white = (self.turn == 0)

        # 3. ตรวจว่ามีการเดินถูกกฎหมายไหม
        if not self.has_any_legal_move(is_white):
            if self.is_in_check(is_white):
                return 'checkmate'
            else:
                return 'stalemate'

        return None

    # -------------------- handle_click --------------------
    def handle_click(self, r, c):
        if self.game_over:
            return None

        piece = self.board[r][c]
        if self.selected is None:
            if piece != '.' and self.check_turn(piece):
                self.selected = (r, c)
            return None

        sr, sc = self.selected
        if (r, c) == (sr, sc):
            self.selected = None; return None
        if piece != '.' and self.check_turn(piece):
            self.selected = (r, c); return None

        valid_moves = self.get_valid_moves(sr, sc)
        if (r, c) in valid_moves:
            self.move_piece(self.selected, (r, c))
            self.turn = 1 - self.turn
            self._record_position()
            self.selected = None

            status = self.get_game_status()
            if status:
                self.game_over = True
                return status

            # AI เดิน
            ai_move = self.get_best_move(4)
            if ai_move:
                self.move_piece(ai_move[0], ai_move[1])
                self.turn = 1 - self.turn
                self._record_position()
                status = self.get_game_status()
                if status:
                    self.game_over = True
                    return status
        else:
            print("illegal move")

        self.selected = None
        return None

    # -------------------- Evaluation --------------------
    def evaluate_board(self):
        score = 0
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece == '.': continue
                p     = piece.lower()
                base  = self.PIECE_VALUES.get(p, 0)
                table = self.get_piece_table(p)
                if piece.isupper():
                    score += base + (table[7-i][j] if table else 0)
                else:
                    score -= base + (table[i][j] if table else 0)
        return score

    def get_all_moves(self, is_white):
        moves = []
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece == '.': continue
                if is_white and piece.isupper():
                    for m in self.get_valid_moves(i, j):
                        moves.append(((i, j), m))
                elif not is_white and piece.islower():
                    for m in self.get_valid_moves(i, j):
                        moves.append(((i, j), m))
        return moves

    # -------------------- Move Ordering --------------------
    def score_move(self, start, end, depth):
        sr, sc = start; er, ec = end
        piece  = self.board[sr][sc]
        target = self.board[er][ec]
        score  = 0
        if target != '.':
            score += 10000 + self.PIECE_VALUES.get(target.lower(), 0) \
                           - self.PIECE_VALUES.get(piece.lower(), 0) // 10
        elif self.killers[depth][0] == (start, end): score += 9000
        elif self.killers[depth][1] == (start, end): score += 8000
        return score

    def order_moves(self, moves, depth):
        return sorted(moves, key=lambda m: self.score_move(m[0], m[1], depth), reverse=True)

    # -------------------- Minimax --------------------
    def minimax(self, depth, alpha, beta, is_maximizing):
        tt_key = self.hash
        if tt_key in self.tt:
            td, tf, tv = self.tt[tt_key]
            if td >= depth:
                if tf == 'exact': return tv
                if tf == 'lower' and tv >= beta:  return tv
                if tf == 'upper' and tv <= alpha: return tv

        if depth == 0:
            return self.evaluate_board()

        moves = self.get_all_moves(is_maximizing)
        if not moves:
            if self.is_in_check(is_maximizing):
                return -99999 if is_maximizing else 99999
            return 0

        moves = self.order_moves(moves, depth)
        orig_alpha = alpha

        if is_maximizing:
            best = -float('inf')
            for start, end in moves:
                cap   = self.board[end[0]][end[1]]
                piece = self.board[start[0]][start[1]]
                saved = self.hash
                self.move_piece(start, end)
                val = self.minimax(depth-1, alpha, beta, False)
                self.board[start[0]][start[1]] = piece
                self.board[end[0]][end[1]]     = cap
                self.hash = saved
                if val > best: best = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    if cap == '.' and depth < len(self.killers):
                        self.killers[depth][1] = self.killers[depth][0]
                        self.killers[depth][0] = (start, end)
                    break
            flag = 'exact' if best > orig_alpha and best < beta else \
                   'lower' if best >= beta else 'upper'
            self.tt[tt_key] = (depth, flag, best)
            return best
        else:
            best = float('inf')
            for start, end in moves:
                cap   = self.board[end[0]][end[1]]
                piece = self.board[start[0]][start[1]]
                saved = self.hash
                self.move_piece(start, end)
                val = self.minimax(depth-1, alpha, beta, True)
                self.board[start[0]][start[1]] = piece
                self.board[end[0]][end[1]]     = cap
                self.hash = saved
                if val < best: best = val
                beta = min(beta, val)
                if beta <= alpha:
                    if cap == '.' and depth < len(self.killers):
                        self.killers[depth][1] = self.killers[depth][0]
                        self.killers[depth][0] = (start, end)
                    break
            flag = 'exact' if best < beta and best > alpha else \
                   'lower' if best >= beta else 'upper'
            self.tt[tt_key] = (depth, flag, best)
            return best

    def _count_total_pieces(self):
        """นับจำนวนหมากทั้งหมดบนกระดาน (ไม่รวมช่องว่าง)"""
        return sum(1 for r in self.board for c in r if c != '.')

    def _get_temperature(self):
        """
        คำนวณ temperature ตามช่วงเกม
        - Opening  (หมาก >= 28) : temperature สูง → เดินหลากหลาย
        - Midgame  (หมาก 16-27) : temperature กลาง
        - Endgame  (หมาก < 16)  : temperature ต่ำ → เล่นดีที่สุด
        """
        pieces = self._count_total_pieces()
        if pieces >= 28:
            return 1.4   # opening: หลากหลายมาก
        elif pieces >= 16:
            return 0.7   # midgame: ปานกลาง
        else:
            return 0.15  # endgame: ใกล้ deterministic

    def _sample_move(self, moves_scores, temperature, is_white):
        """
        Temperature sampling: softmax บน scores แล้วสุ่ม
        temperature → 0   : เลือก best move เสมอ (deterministic)
        temperature = 1.0 : สุ่มตามสัดส่วน score
        temperature > 1.0 : สุ่มมากขึ้น (flatten distribution)
        """
        import math

        if not moves_scores:
            return None

        # ถ้า temperature ต่ำมาก ๆ ให้ greedy เลย
        if temperature < 0.05:
            if is_white:
                return max(moves_scores, key=lambda x: x[2])[:2]
            else:
                return min(moves_scores, key=lambda x: x[2])[:2]

        # flip score สำหรับ Black ให้สูง = ดี เหมือนกัน
        scores = [v if is_white else -v for _, _, v in moves_scores]

        # Softmax with temperature — ลบ max ก่อนเพื่อ numerical stability
        max_s = max(scores)
        exp_s = [math.exp((s - max_s) / temperature) for s in scores]
        total = sum(exp_s)
        probs = [e / total for e in exp_s]

        idx = random.choices(range(len(moves_scores)), weights=probs, k=1)[0]
        return moves_scores[idx][0], moves_scores[idx][1]

    def get_best_move(self, depth, temperature=None):
        """
        หา move ที่ดีที่สุดด้วย minimax + alpha-beta
        แล้วเลือกด้วย temperature sampling เพื่อเพิ่ม variance

        temperature=None  → คำนวณอัตโนมัติตามช่วงเกม
        temperature=0.0   → deterministic (เหมือนเดิม)
        temperature=1.5   → สุ่มมาก (เหมาะ opening)
        """
        self.killers  = [[None, None] for _ in range(20)]
        is_white      = (self.turn == 0)
        moves_scores  = []

        # คำนวณ temperature อัตโนมัติถ้าไม่ได้ระบุ
        if temperature is None:
            temperature = self._get_temperature()

        all_moves = self.order_moves(self.get_all_moves(is_white), depth)

        for start, end in all_moves:
            cap   = self.board[end[0]][end[1]]
            piece = self.board[start[0]][start[1]]
            saved = self.hash
            self.move_piece(start, end)
            val = self.minimax(depth - 1, -float('inf'), float('inf'), not is_white)
            self.board[start[0]][start[1]] = piece
            self.board[end[0]][end[1]]     = cap
            self.hash = saved
            moves_scores.append((start, end, val))

        if not moves_scores:
            return None

        return self._sample_move(moves_scores, temperature, is_white)