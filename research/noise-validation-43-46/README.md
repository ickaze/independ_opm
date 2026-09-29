# YM2151 ノイズ検証 43～46 / Noise validation

analysis/NOISE_VALIDATION.html を開いてください。全1624測定区間を確認済み。
46の再録音を採用しました。元録音は同梱せず、recordings.jsonのSHA-256で特定します。
MDXは stimulus/mdx にあります。短縮曲名を維持しています。
independent-opm 0.11bの本体側でノイズ倍率を0.25に修正。この検証用ZIPには本体ソースを含みません。
高TL末端量子化・変化するEG/AM・サブサンプル切替タイミングは未確定です。

All scheduled measurement windows are present. The replacement 46 capture is used.
The matching independent-opm source release scales noise by 0.25. This evidence ZIP does not include the emulator core.

## 再現 / Reproduction
Python 3, NumPy, Matplotlib and FFmpeg are required.
Place original recordings in ./upload/ as 43NOISE.flac, 44NROUTE.flac, 45NMOD.flac, 46NSTATE.flac.
For 46 use the replacement identified by SHA-256 in analysis/recordings.json.
Run from the archive root:

    python analysis/decode_recordings.py
    python analysis/analyze.py
    python analysis/report.py
    python stimulus/verify.py
    python stimulus/verify_routes.py

Regenerate MDX if needed:

    python stimulus/generate_noise.py
    python stimulus/generate_routes.py

Fixed offsets are approximate, not sample-exact synchronization. Measurements use the central 60% of scheduled windows.
Test log is from direct GCC builds, not Windows or CTest.
Copyright (C) 2026 by I.C.KaZe
Code license: 0BSD (LICENSE.txt).
