"""Procedural fixtures, explicitly not satellite benchmark imagery."""
import cv2
import numpy as np

CASES = {"mixed": "Structural edits + shadow", "shift": "Registration false alarm", "light": "Illumination false alarm", "unchanged": "Unchanged scene"}


def scene(seed=18, size=640):
    rng = np.random.default_rng(seed)
    a = np.empty((size, size, 3), np.uint8)
    noise = rng.normal(0, 6, (size, size, 1))
    a[:] = np.clip(np.array([74, 95, 73]) + noise, 0, 255)
    for pos in [170, 390]:
        cv2.rectangle(a, (pos, 0), (pos + 30, size - 1), (70, 77, 81), -1)
        cv2.rectangle(a, (0, pos), (size - 1, pos + 30), (70, 77, 81), -1)
        for n in range(0, size, 32):
            cv2.line(a, (pos + 15, n), (pos + 15, n + 12), (181, 177, 147), 1)
            cv2.line(a, (n, pos + 15), (n + 12, pos + 15), (181, 177, 147), 1)
    for y in [40, 105, 240, 310, 465, 540]:
        for x in [35, 105, 240, 310, 465, 540]:
            roof = tuple(int(v) for v in rng.integers(145, 190, 3))
            cv2.rectangle(a, (x + 7, y + 8), (x + 58, y + 43), (36, 47, 41), -1)
            cv2.rectangle(a, (x, y), (x + 51, y + 35), roof, -1)
            cv2.rectangle(a, (x + 3, y + 3), (x + 48, y + 32), tuple(max(0, v - 18) for v in roof), 1)
            cv2.line(a, (x + 25, y), (x + 25, y + 35), (208, 202, 184), 1)
    for _ in range(180):
        x, y = rng.integers(0, size, 2)
        if (x % 220 < 160) and (y % 220 < 160):
            cv2.circle(a, (int(x), int(y)), int(rng.integers(3, 8)), (46, 76, 52), -1)
    return a


def pair(case="mixed", seed=18):
    a = scene(seed)
    b = a.copy()
    truth = np.zeros(a.shape[:2], np.uint8)
    if case == "mixed":
        b[238:278, 238:295] = (80, 100, 76)
        truth[238:278, 238:295] = 255
        cv2.rectangle(b, (455, 300), (510, 345), (183, 174, 143), -1)
        cv2.line(b, (482, 300), (482, 345), (217, 211, 181), 2)
        truth[300:346, 455:511] = 255
        b[450:585, 20:155] = (b[450:585, 20:155].astype(float) * .64).astype(np.uint8)
    elif case == "shift":
        b = cv2.warpAffine(a, np.float32([[1, 0, 5], [0, 1, -4]]), (640, 640), borderMode=cv2.BORDER_REFLECT)
    elif case == "light":
        b = np.clip(a.astype(float) * .72 + 12, 0, 255).astype(np.uint8)
    elif case != "unchanged":
        raise ValueError("Unknown demo scenario")
    return a, b, truth
