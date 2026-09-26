YM2151 LFO evidence / 日本語・English
Open output/lfo-evidence-ja.html or output/lfo-evidence-en.html offline.
HTMLをブラウザで開いてください。全41録音の図は折り畳み欄にあります。

Rebuild HTML from included plot values: python build.py
Dependencies: Python 3, numpy. No network required.
Re-extract audio figures: put original files in input/, then python extract.py; python detail.py; python build.py
Audio extraction also requires scipy, ffmpeg and ffprobe. Original recordings are not bundled.
Core source/evidence snapshot: core/independent-opm/
Earlier frequency coverage and measurement evidence: previous/
Source ZIP identity and source hashes: provenance.json
Each data/*.flac.json or *.wav.json records original audio SHA-256, duration and plot values.
The new illustrative plots do not replace the archived formal statistics.
新しい説明図は保存済みの正式な検証集計を置き換えません。
For PM, the prediction uses a calibrated empirical pitch table, not the current core pitch converter.
PM予測線は実測較正表を使います。現行コアの音程精度の証明ではありません。
