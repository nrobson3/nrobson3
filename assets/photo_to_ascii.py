"""Turns a portrait photo into the character art used on sheet 2.

    python photo_to_ascii.py path/to/photo.png      ->  portrait.txt

Only the characters are kept in the repo, not the photo. The person is cut out
with OpenCV GrabCut, seeded with a head-and-shoulders layout for a centred
square headshot; local contrast is evened out (CLAHE) and sharpened so hair,
glasses and the jaw keep their edges, then darkness maps to character density.
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAMP = " .'`,:;!|ijlk%*mHM@"     # light -> dark
COLS = 64
ASPECT = 0.48                    # rows per column for a square region (char width / line height)
SHARP = 1.2


def segment(img):
    h, w = img.shape[:2]
    s = w / 422.0                                  # seeds were laid out on a 422 px square
    yy, xx = np.mgrid[:h, :w] / s
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    head = ((xx - 200) / 118.0) ** 2 + ((yy - 175) / 150.0) ** 2 < 1
    shoulders = (xx > 85) & (xx < 335) & (yy > 290)
    mask[head | shoulders] = cv2.GC_PR_FGD
    core = ((xx - 200) / 62.0) ** 2 + ((yy - 185) / 95.0) ** 2 < 1
    mask[core | ((xx > 150) & (xx < 260) & (yy > 320))] = cv2.GC_FGD
    outside = ((xx - 211) ** 2 + (yy - 211) ** 2) > 207 ** 2
    mask[outside | ((xx < 72) & (yy < 300)) | ((xx > 338) & (yy < 280))] = cv2.GC_BGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:                                      # keep the person, drop stray islands
        fg = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return fg & (((xx - 211) ** 2 + (yy - 211) ** 2) < 195 ** 2).astype(np.uint8)


def to_ascii(img, fg):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(6, 6)).apply(gray).astype(np.float32) / 255.0
    eq = np.clip(eq + SHARP * (eq - cv2.GaussianBlur(eq, (0, 0), 3.0)), 0, 1)
    rows = int(round(COLS * ASPECT))
    small = cv2.resize(eq, (COLS, rows), interpolation=cv2.INTER_AREA)
    msk = cv2.resize(fg.astype(np.float32), (COLS, rows), interpolation=cv2.INTER_AREA)
    dark = np.clip((1.0 - small - 0.12) / 0.8, 0, 1) ** 0.9
    lines = []
    for r in range(rows):
        lines.append(''.join(' ' if msk[r, c] < 0.5 else RAMP[min(len(RAMP) - 1, int(dark[r, c] * len(RAMP)))]
                             for c in range(COLS)).rstrip())
    return '\n'.join(lines).strip('\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('usage: python photo_to_ascii.py photo.png')
    img = cv2.imread(sys.argv[1], cv2.IMREAD_COLOR)
    art = to_ascii(img, segment(img))
    with open(os.path.join(HERE, 'portrait.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(art + '\n')
    print(art)
