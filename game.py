import random
import hashlib

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
        self.turn = 0

        # --- Transposition Table ---
        self.tt = {}          # hash -> (depth, flag, value)
        # Zobrist keys: random 64-bit int for each (piece, square)
        self.zobrist = {}
        pieces = 'pnbrmkPNBRMK'
        for p in pieces:
            for r in range(8):
                for c in range(8):
                    self.zobrist[(p, r, c)] = random.getrandbits(64)
        self.zobrist_turn = random.getrandbits(64)
        self.hash = self._compute_hash()

        # --- Killer Moves (for move ordering) ---
        self.killers = [[None, None] for _ in range(20)]  # depth -> [move1, move2]

    # -------------------- Zobrist Hashing --------------------
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
        h ^= self.zobrist[(piece, r, c)]           # remove from src
        if captured != '.':
            h ^= self.zobrist[(captured, er, ec)]  # remove captured
        p_placed = promoted_to if promoted_to else piece
        h ^= self.zobrist[(p_placed, er, ec)]      # place at dst
        h ^= self.zobrist_turn                     # flip turn
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
            'm': self.MET_TABLE, 'k': self.KING_TABLE,
        }.get(piece_lower)

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
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            while self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.':
                    moves.append((nr, nc))
                else:
                    if target.isupper() != piece.isupper():
                        moves.append((nr, nc))
                    break
                nr += dr; nc += dc
        return moves

    def get_knight_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r + dr, c + dc
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    def get_met_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r + dr, c + dc
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    def get_bishop_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r + dr, c + dc
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))
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
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr, nc = r + dr, c + dc
            if self.is_in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or target.isupper() != piece.isupper():
                    moves.append((nr, nc))
        return moves

    # -------------------- game logic --------------------
    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end
        piece = self.board[sr][sc]
        captured = self.board[er][ec]

        self.board[er][ec] = piece
        self.board[sr][sc] = '.'

        promoted_to = None
        if piece == 'P' and er == 2:
            self.board[er][ec] = 'M'; promoted_to = 'M'
        elif piece == 'p' and er == 5:
            self.board[er][ec] = 'm'; promoted_to = 'm'

        # Update hash incrementally (fast!)
        self.hash = self._update_hash(piece, sr, sc, captured, er, ec, promoted_to)
        return piece

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
        r, c = king_pos
        return self.is_square_attacked(r, c, not is_white)

    def try_move(self, start, end):
        sr, sc = start
        er, ec = end
        piece = self.board[sr][sc]
        captured = self.board[er][ec]
        saved_hash = self.hash

        self.board[er][ec] = piece
        self.board[sr][sc] = '.'
        if piece == 'P' and er == 2: self.board[er][ec] = 'M'
        elif piece == 'p' and er == 5: self.board[er][ec] = 'm'

        is_white = piece.isupper()
        in_check = self.is_in_check(is_white)

        self.board[sr][sc] = piece
        self.board[er][ec] = captured
        self.hash = saved_hash
        return not in_check

    def get_valid_moves(self, r, c):
        return [m for m in self.get_raw_moves(r, c) if self.try_move((r, c), m)]

    def handle_click(self, r, c):
        piece = self.board[r][c]
        if self.selected is None:
            if piece != '.' and self.check_turn(piece):
                self.selected = (r, c)
            return

        sr, sc = self.selected
        if (r, c) == self.selected:
            self.selected = None; return
        if piece != '.' and self.check_turn(piece):
            self.selected = (r, c); return

        valid_moves = self.get_valid_moves(sr, sc)
        if (r, c) in valid_moves:
            self.move_piece(self.selected, (r, c))
            self.turn = 1 - self.turn
            self.selected = None

            ai_move = self.get_best_move(4)
            if ai_move:
                start, end = ai_move
                self.move_piece(start, end)
                self.turn = 1 - self.turn
        else:
            print("illegal move")
        self.selected = None

    # -------------------- Evaluation --------------------
    def evaluate_board(self):
        score = 0
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece == '.': continue
                p = piece.lower()
                base_value = self.PIECE_VALUES.get(p, 0)
                table = self.get_piece_table(p)
                if piece.isupper():
                    score += base_value + (table[7-i][j] if table else 0)
                else:
                    score -= base_value + (table[i][j] if table else 0)
        return score

    def get_all_moves(self, is_white):
        moves = []
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece == '.': continue
                if is_white and piece.isupper():
                    for move in self.get_valid_moves(i, j):
                        moves.append(((i, j), move))
                elif not is_white and piece.islower():
                    for move in self.get_valid_moves(i, j):
                        moves.append(((i, j), move))
        return moves

    # -------------------- Move Ordering --------------------
    def score_move(self, start, end, depth):
        """Score a move for ordering (higher = search first)."""
        sr, sc = start
        er, ec = end
        piece = self.board[sr][sc]
        target = self.board[er][ec]
        score = 0

        # 1. MVV-LVA: captures sorted by (victim value - attacker value)
        if target != '.':
            victim_val = self.PIECE_VALUES.get(target.lower(), 0)
            attacker_val = self.PIECE_VALUES.get(piece.lower(), 0)
            score += 10000 + victim_val - attacker_val // 10

        # 2. Killer moves (quiet moves that caused beta cutoff before)
        elif self.killers[depth][0] == (start, end):
            score += 9000
        elif self.killers[depth][1] == (start, end):
            score += 8000

        return score

    def order_moves(self, moves, depth):
        return sorted(moves, key=lambda m: self.score_move(m[0], m[1], depth), reverse=True)

    # -------------------- Minimax + Alpha-Beta + TT --------------------
    def minimax(self, depth, alpha, beta, is_maximizing):
        # --- Transposition Table lookup ---
        tt_key = self.hash
        if tt_key in self.tt:
            tt_depth, tt_flag, tt_value = self.tt[tt_key]
            if tt_depth >= depth:
                if tt_flag == 'exact':
                    return tt_value
                elif tt_flag == 'lower' and tt_value >= beta:
                    return tt_value
                elif tt_flag == 'upper' and tt_value <= alpha:
                    return tt_value

        if depth == 0:
            return self.evaluate_board()

        moves = self.get_all_moves(is_maximizing)
        if not moves:
            if self.is_in_check(is_maximizing):
                return -99999 if is_maximizing else 99999
            return 0

        # Order moves before searching
        moves = self.order_moves(moves, depth)

        original_alpha = alpha

        if is_maximizing:
            max_eval = -float('inf')
            best_move = None
            for start, end in moves:
                captured = self.board[end[0]][end[1]]
                piece = self.board[start[0]][start[1]]
                saved_hash = self.hash

                self.move_piece(start, end)
                eval_score = self.minimax(depth - 1, alpha, beta, False)

                self.board[start[0]][start[1]] = piece
                self.board[end[0]][end[1]] = captured
                self.hash = saved_hash

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (start, end)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    # Store killer move
                    if captured == '.' and depth < len(self.killers):
                        self.killers[depth][1] = self.killers[depth][0]
                        self.killers[depth][0] = (start, end)
                    break

            # Store in TT
            flag = 'exact' if max_eval > original_alpha and max_eval < beta else \
                   'lower' if max_eval >= beta else 'upper'
            self.tt[tt_key] = (depth, flag, max_eval)
            return max_eval

        else:
            min_eval = float('inf')
            for start, end in moves:
                captured = self.board[end[0]][end[1]]
                piece = self.board[start[0]][start[1]]
                saved_hash = self.hash

                self.move_piece(start, end)
                eval_score = self.minimax(depth - 1, alpha, beta, True)

                self.board[start[0]][start[1]] = piece
                self.board[end[0]][end[1]] = captured
                self.hash = saved_hash

                if eval_score < min_eval:
                    min_eval = eval_score
                beta = min(beta, eval_score)
                if beta <= alpha:
                    if captured == '.' and depth < len(self.killers):
                        self.killers[depth][1] = self.killers[depth][0]
                        self.killers[depth][0] = (start, end)
                    break

            flag = 'exact' if min_eval < beta and min_eval > alpha else \
                   'lower' if min_eval >= beta else 'upper'
            self.tt[tt_key] = (depth, flag, min_eval)
            return min_eval

    def get_best_move(self, depth):
        # Clear killers at start of new search
        self.killers = [[None, None] for _ in range(20)]

        is_white = (self.turn == 0)
        best_move = None

        if is_white:
            best_value = -float('inf')
            for start, end in self.order_moves(self.get_all_moves(True), depth):
                captured = self.board[end[0]][end[1]]
                piece = self.board[start[0]][start[1]]
                saved_hash = self.hash

                self.move_piece(start, end)
                value = self.minimax(depth - 1, -float('inf'), float('inf'), False)
                self.board[start[0]][start[1]] = piece
                self.board[end[0]][end[1]] = captured
                self.hash = saved_hash

                if value > best_value:
                    best_value = value; best_move = (start, end)
        else:
            best_value = float('inf')
            for start, end in self.order_moves(self.get_all_moves(False), depth):
                captured = self.board[end[0]][end[1]]
                piece = self.board[start[0]][start[1]]
                saved_hash = self.hash

                self.move_piece(start, end)
                value = self.minimax(depth - 1, -float('inf'), float('inf'), True)
                self.board[start[0]][start[1]] = piece
                self.board[end[0]][end[1]] = captured
                self.hash = saved_hash

                if value < best_value:
                    best_value = value; best_move = (start, end)

        return best_move