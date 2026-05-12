"""
merge_datasets.py — รวม dataset.pt จากหลายเครื่องเป็นไฟล์เดียว
================================================================
วิธีใช้:
    python merge_datasets.py pc1.pt pc2.pt pc3.pt --out merged.pt
    python merge_datasets.py data/*.pt --out merged.pt
"""

import argparse
import os
import sys
import zipfile
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("[warn] torch ไม่พบ — จะบันทึกเป็น .npz แทน")


def load_pt(path):
    """โหลด .pt หรือ .npz → (X np.array, y np.array)"""
    if path.endswith('.npz'):
        data = np.load(path)
        return data['X'], data['y']

    if HAS_TORCH:
        data = torch.load(path, map_location='cpu', weights_only=False)
        return data['X'].numpy(), data['y'].numpy()

    # อ่านแบบ manual ผ่าน zipfile (ไม่ต้องมี torch)
    with zipfile.ZipFile(path) as z:
        raw0 = z.read('dataset/data/0')
        raw1 = z.read('dataset/data/1')
    X_flat = np.frombuffer(raw0, dtype='<f4').copy()
    y_flat  = np.frombuffer(raw1, dtype='<f4').copy()
    N = len(y_flat)
    X = X_flat.reshape(N, 12, 8, 8)
    return X, y_flat


def summarize(name, X, y):
    N      = len(y)
    n_pos  = (y >  0.5).sum()
    n_neg  = (y < -0.5).sum()
    n_zero = N - n_pos - n_neg
    print(f"  {name}")
    print(f"    positions : {N:>8,}")
    print(f"    White (+1): {n_pos:>8,}  ({n_pos/N*100:.1f}%)")
    print(f"    Draw  ( 0): {n_zero:>8,}  ({n_zero/N*100:.1f}%)")
    print(f"    Black (-1): {n_neg:>8,}  ({n_neg/N*100:.1f}%)")


def save(X, y, path):
    if HAS_TORCH:
        torch.save({
            'X': torch.from_numpy(X),
            'y': torch.from_numpy(y),
            'shape': X.shape,
            'description': 'Makruk merged dataset. X=(N,12,8,8) y=(N,) outcome {-1,0,1}',
        }, path)
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"  บันทึก → {path}  ({size_mb:.1f} MB)")
    else:
        npz = path.replace('.pt', '.npz')
        np.savez_compressed(npz, X=X, y=y)
        size_mb = os.path.getsize(npz) / 1024 / 1024
        print(f"  บันทึก → {npz}  ({size_mb:.1f} MB)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='+', help='ไฟล์ .pt ที่จะรวม')
    parser.add_argument('--out',      default='merged.pt', help='output file')
    parser.add_argument('--shuffle',  action='store_true', help='สุ่มลำดับหลังรวม (แนะนำ)')
    parser.add_argument('--no-dedup', action='store_true', help='ไม่ตัด duplicate positions')
    args = parser.parse_args()

    # ── โหลดทุกไฟล์ ──
    all_X, all_y = [], []
    print("=== โหลดไฟล์ ===")
    for path in args.inputs:
        if not os.path.exists(path):
            print(f"  [skip] ไม่พบไฟล์: {path}")
            continue
        X, y = load_pt(path)
        summarize(os.path.basename(path), X, y)
        all_X.append(X)
        all_y.append(y)

    if not all_X:
        print("ไม่มีไฟล์ที่โหลดได้เลย")
        sys.exit(1)

    # ── รวม ──
    X_merged = np.concatenate(all_X, axis=0)
    y_merged = np.concatenate(all_y, axis=0)
    print(f"\n  รวมแล้ว: {len(y_merged):,} positions")

    # ── ตัด duplicate (optional) ──
    if not args.no_dedup:
        # hash แต่ละ position เป็น bytes แล้วหา unique
        flat   = X_merged.reshape(len(X_merged), -1)
        hashes = [row.tobytes() for row in flat]
        seen   = set()
        keep   = []
        for i, h in enumerate(hashes):
            if h not in seen:
                seen.add(h)
                keep.append(i)
        before = len(y_merged)
        X_merged = X_merged[keep]
        y_merged = y_merged[keep]
        removed  = before - len(y_merged)
        print(f"  ตัด duplicate: {removed:,} positions → เหลือ {len(y_merged):,}")

    # ── shuffle ──
    if args.shuffle:
        idx = np.random.permutation(len(y_merged))
        X_merged = X_merged[idx]
        y_merged = y_merged[idx]
        print(f"  shuffle เรียบร้อย")

    # ── สรุปรวม ──
    print(f"\n=== สรุป merged dataset ===")
    summarize(args.out, X_merged, y_merged)

    # ── บันทึก ──
    print(f"\n=== บันทึก ===")
    save(X_merged.astype(np.float32), y_merged.astype(np.float32), args.out)
    print("เสร็จ ✅")