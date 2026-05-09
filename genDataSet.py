"""
Phase 1 — Self-play Dataset Generator
=======================================
ให้ minimax (game.py) เล่นกับตัวเองแล้วบันทึก dataset สำหรับ train ML

Output:
    dataset.pt   — PyTorch file มี 2 tensors:
                    X : (N, 12, 8, 8)  float32  board planes
                    y : (N,)           float32  outcome +1 / 0 / -1

Usage:
    python generate_dataset.py               # 500 เกม (ทดสอบ)
    python generate_dataset.py --games 5000  # 5000 เกม (แนะนำ)
    python generate_dataset.py --games 5000 --depth 2 --out my_data.pt
"""

import argparse
import copy
import time
import sys
import os

# ── ตรวจว่ามี torch ไหม ถ้าไม่มีก็บันทึกเป็น .npz แทน ──────────────────────
try:
    import torch
    HAS_TORCH = True
except ImportError:
    import numpy as np
    HAS_TORCH = False
    print("[warn] torch ไม่พบ — จะบันทึกเป็น dataset.npz แทน")

import numpy as np
from game import Game

# ── Piece index map ────────────────────────────────────────────────────────────
# 12 channels: White P N B R M K (0-5)  Black p n b r m k (6-11)
PIECE_IDX = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'M': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'm': 10,'k': 11,
}

MAX_MOVES_PER_GAME = 300   # ป้องกันเกมวนไม่จบ


def board_to_tensor(board):
    """แปลง board 8×8 list → numpy array (12, 8, 8) float32"""
    planes = np.zeros((12, 8, 8), dtype=np.float32)
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p != '.':
                planes[PIECE_IDX[p], r, c] = 1.0
    return planes


def play_one_game(depth=2, temperature=None):
    """
    เล่นเกมเดียวจนจบ คืน list ของ (board_tensor, turn)
    และ outcome สุดท้าย

    outcome:
        +1  White ชนะ
        -1  Black ชนะ
         0  เสมอ
    """
    game = Game()
    states = []   # list of (np.array 12×8×8, turn:int)

    for _ in range(MAX_MOVES_PER_GAME):
        # บันทึก state ก่อนเดิน
        states.append((board_to_tensor(game.board), game.turn))

        # หา move
        move = game.get_best_move(depth, temperature)
        if move is None:
            break

        # เดิน
        start, end = move
        game.move_piece(start, end)
        game.turn = 1 - game.turn
        game._record_position()

        # ตรวจสถานะ
        status = game.get_game_status()
        if status is not None:
            # แปลง status → outcome
            if status == 'checkmate':
                # ฝ่ายที่ถึงตาเดินอยู่แพ้
                outcome = -1.0 if game.turn == 0 else 1.0
            else:
                outcome = 0.0   # stalemate / threefold / bare_king
            return states, outcome

    # ถ้าครบ MAX_MOVES ยังไม่จบ → เสมอ
    return states, 0.0


def _worker(args):
    """worker สำหรับ multiprocessing"""
    depth, temperature, seed = args
    import random as _rand
    _rand.seed(seed)
    return play_one_game(depth=depth, temperature=temperature)


def generate_dataset(n_games=500, depth=2, temperature=None, verbose=True, workers=1):
    """
    สร้าง dataset จาก n_games เกม
    คืน (X, y) โดย X: (N,12,8,8), y: (N,)

    workers > 1 → ใช้ multiprocessing เพิ่มความเร็ว
    แนะนำ workers = จำนวน CPU core - 1
    """
    import multiprocessing as mp

    all_X = []
    all_y = []
    wins  = {1.0: 0, -1.0: 0, 0.0: 0}
    t0    = time.time()

    seeds    = [i + int(time.time()) for i in range(n_games)]
    job_args = [(depth, temperature, s) for s in seeds]

    def _process(game_idx, states, outcome):
        for board_tensor, turn in states:
            perspective_outcome = outcome if turn == 0 else -outcome
            all_X.append(board_tensor)
            all_y.append(perspective_outcome)
        wins[outcome] += 1
        if verbose and (game_idx + 1) % 50 == 0:
            elapsed = time.time() - t0
            speed   = (game_idx + 1) / max(elapsed, 1e-6)
            remain  = (n_games - game_idx - 1) / speed
            print(
                f"  [{game_idx+1:>5}/{n_games}]  "
                f"positions: {len(all_X):>7}  "
                f"W/D/B: {wins[1.0]}/{wins[0.0]}/{wins[-1.0]}  "
                f"speed: {speed:.1f} games/s  "
                f"ETA: {remain:.0f}s"
            )

    if workers > 1:
        with mp.Pool(processes=workers) as pool:
            for i, (states, outcome) in enumerate(
                pool.imap_unordered(_worker, job_args, chunksize=4)
            ):
                _process(i, states, outcome)
    else:
        for i, job in enumerate(job_args):
            states, outcome = _worker(job)
            _process(i, states, outcome)

    X = np.stack(all_X).astype(np.float32)
    y = np.array(all_y, dtype=np.float32)

    elapsed = time.time() - t0
    if verbose:
        print(f"\n  Done — {len(y):,} positions จาก {n_games} เกม ({elapsed:.1f}s)")
        print(f"  W/D/B: {wins[1.0]}/{wins[0.0]}/{wins[-1.0]}")
        print(f"  y distribution: min={y.min():.1f}  max={y.max():.1f}  mean={y.mean():.3f}")

    return X, y


def save_dataset(X, y, path):
    """บันทึก dataset ลงไฟล์ (.pt หรือ .npz ตามที่มี)"""
    if HAS_TORCH:
        torch.save({
            'X': torch.from_numpy(X),
            'y': torch.from_numpy(y),
            'shape': X.shape,
            'channels': 12,
            'description': 'Makruk self-play dataset. X=(N,12,8,8) y=(N,) outcome in {-1,0,1}',
        }, path)
        print(f"  บันทึก → {path}  (torch format)")
    else:
        npz_path = path.replace('.pt', '.npz')
        np.savez_compressed(npz_path, X=X, y=y)
        print(f"  บันทึก → {npz_path}  (numpy format)")


def load_dataset(path):
    """โหลด dataset กลับมา คืน (X_tensor, y_tensor)"""
    if path.endswith('.npz'):
        data = np.load(path)
        X = torch.from_numpy(data['X'])
        y = torch.from_numpy(data['y'])
    else:
        data = torch.load(path, weights_only=True)
        X = data['X']
        y = data['y']
    return X, y


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Makruk Phase 1 — Self-play dataset generator')
    parser.add_argument('--games',  type=int,   default=500,          help='จำนวนเกม (default: 500)')
    parser.add_argument('--depth',  type=int,   default=2,            help='minimax depth (default: 2)')
    parser.add_argument('--temp',   type=float, default=None,         help='temperature override (default: auto)')
    parser.add_argument('--out',     type=str,   default='dataset.pt', help='output file (default: dataset.pt)')
    parser.add_argument('--workers', type=int,   default=1,            help='parallel workers (default: 1, แนะนำ CPU-1)')
    parser.add_argument('--test',    action='store_true',              help='ทดสอบ 5 เกม แล้วออก')
    args = parser.parse_args()

    if args.test:
        print("=== ทดสอบ 5 เกม ===")
        X, y = generate_dataset(n_games=5, depth=args.depth, temperature=args.temp, verbose=True)
        print(f"X shape: {X.shape}  y shape: {y.shape}")
        print(f"X sample plane sum: {X[0].sum():.0f} (ควรประมาณ 32 ตอนเริ่มเกม)")
        print(f"y sample: {y[:10]}")
        sys.exit(0)

    print(f"=== Makruk Phase 1 — Self-play Dataset Generator ===")
    print(f"  games={args.games}  depth={args.depth}  temp={args.temp}  workers={args.workers}  out={args.out}\n")

    X, y = generate_dataset(
        n_games=args.games,
        depth=args.depth,
        temperature=args.temp,
        verbose=True,
        workers=args.workers,
    )

    save_dataset(X, y, args.out)

    # ── สรุปขนาดไฟล์ ──
    target = args.out if args.out.endswith('.pt') or not HAS_TORCH else args.out.replace('.pt', '.npz')
    if os.path.exists(target):
        size_mb = os.path.getsize(target) / 1024 / 1024
        print(f"  ขนาดไฟล์: {size_mb:.1f} MB")

    print("\nวิธีโหลดกลับ:")
    print("  from generate_dataset import load_dataset")
    print(f"  X, y = load_dataset('{args.out}')")
    print("  # X: (N, 12, 8, 8) float32 — board planes")
    print("  # y: (N,)          float32 — outcome +1/0/-1 จาก perspective ของฝ่ายที่เดิน")