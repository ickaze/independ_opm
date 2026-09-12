# Independent OPM 0.10b

YM2151のレジスタ入力からステレオ音声を生成する、独自実装のC++17音源コアです。
**発音する機能エミュレータです。実チップとのビット一致・サイクル一致は未達成です。**

## 0.10bの変更

0.9を起点に、ユーザー提供のX68Sound src020615原版からLFOを再作成しました。詳細・参照範囲・ライセンス判断は [再作成報告](REBUILD_0.10b.md) を参照してください。

F0h〜FFhは16内部サンプルごとに倍の位相加算、18h書込みは同値でも時間カウンタを再始動します。矩形AMの最大値256を扱うため、inspect_lfoのphase/amはuint16_tになりました。17bit LFSRは指定された暫定モデルを維持します。

原版との256周波数×3波形の比較と既存3テスト群が通過。全体のCC0化はしていません。LICENSE.txtとTHIRD_PARTY_NOTICES.txtを参照してください。

## 0.9の変更

04〜07の実機録音を追加解析し、測定出力モードをALG7へ拡張しました。M1/M2/C1/C2の全出力とch7境界を反映しています。APIは `set_measured_output_timing(true)`。旧API名は互換用に残り、同じALG5/ALG7モードを有効にします。CLIの `--gmc-opt04-4mhz` も両ALGに適用されます。ALG0〜4/6は未検証のため既存出力を維持します。

[追加解析報告](measurements-4mhz-04-07/REPORT.md) に音程・ペア・負荷試験の結果と限界を記載しました。

## 0.8の変更

4MHz録音から確認したALG5のキャリア別・チャンネル別出力タイミングを、任意で有効にできる本体APIとCLIモードへ実装しました。ch7の境界も反映しています。

```bat
bin\opm_render.exe hardware-tests\traces\01SOLO.trace model.wav 21 4000000 96000 0.7 --gmc-opt04-4mhz
```

測定表、適用範囲、前回測定音色の訂正は [解析報告](measurements-4mhz/REPORT.md) を参照してください。既定の出力は変更しません。測定モードのAPIは `set_measured_alg5_timing(true)`、共通取り込み遅延はCLI側で処理します。GCCで既存3テスト群および全8ALG×8chの新モード検証を通過。Windows/MSVCでは未検証です。

## Windows 11 / Visual Studio 2022

「x64 Native Tools Command Prompt for VS 2022」でこのフォルダを開き、実行します。

```bat
build_windows.bat
```

bin/opm_render.exe と bin/opm_tests.exe を生成し、テスト後に demo.wav を生成します。
Windows用実行ファイルは同梱していません。bin/内の拡張子なしファイルはLinux用です。
C++によるデスクトップ開発ワークロードが必要です。

CMakeでもビルドできます。

```bat
cmake -S . -B build -A x64
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
build\Release\opm_render.exe --demo demo.wav
```

## WAV生成

```bat
bin\opm_render.exe --demo demo.wav
bin\opm_render.exe examples\a440.trace a440.wav 2 3579545 48000 1
```

引数は「入力または--demo」「出力WAV」「秒数」「チップクロックHz」「出力Hz」「ゲイン」です。
最後の4つの既定値は6秒、3579545Hz、48000Hz、1です。
44100〜192000Hz等の出力に対応します（許容範囲8000〜192000Hz）。
出力は16bitステレオPCM WAV。クリップ数を終了時に表示します。
ゲインはチップの実アナログ出力電圧とは対応しません。

trace形式は examples/a440.trace を参照してください。
絶対マスタークロック、レジスタ番号、書込値の3列です。
数値は10進、または0xを付けた16進。先頭0の数値はC++の変換規則により8進です。
同時刻の書込は記載順に処理します。時刻が逆行する入力はエラーです。
CLIは最大600秒、時刻は32bitまで。実行中に指定範囲以降のイベントがある場合はエラーです。
trace入力はBUSY待ちを省いた直接レジスタAPIを使います。
MDX/PDX/VGMのファイル読込は今回のツールにはありません。

## 組み込み

include/ym2151.hpp、src/ym2151.cpp、src/envelope_times.hpp の3ファイルで利用できます。
音源コアはC++標準ライブラリのみを使用します。

```cpp
#include "ym2151.hpp"
using namespace independent_opm;
Ym2151 chip(3579545);
chip.write_register(0x20, 0xc7);
chip.write_register(0x28, 0x4a);
chip.write_register(0x40, 1);
chip.write_register(0x80, 0xdf);
chip.write_register(8, 8);
chip.advance(64);
Stereo sample = chip.last_sample();
```

advance()はマスタークロックを進め、64クロックごとに音声を生成します。
全サンプルが必要な場合はadvance(clocks, callback, context)を使います。
callback内で同じchipを変更・再帰呼出ししないでください。
バスとして接続する場合はwrite_address()/write_data()/status()/irq()を使用します。
write_data()はBUSY中にfalseを返し、書込みを適用しません。
write_register()は統合用の直接APIであり、BUSY拒否を省略します。

Resamplerを使用すると、33タップの窓付きsincでホストのサンプルレートへ変換できます。
src/main.cppに、イベント時刻を維持した使用例があります。
フィルタ遅延はネイティブ16サンプルです。
保存・復元は同一実行ファイル内でオブジェクトをコピーします。
ホスト出力まで再現する場合はResamplerと時刻余りも一緒にコピーしてください。
ディスク保存用のバイナリ形式は未定義です。

## 実装範囲

- 8チャンネル、32オペレータ、8アルゴリズム、フィードバック
- KC/KF、MUL、DT1/DT2、TL、KS、AR/D1R/D2R/D1L/RR
- LFO 4波形、PMD/AMDの独立保持、PMS/AMS、LFOリセット
- チャンネル8のC2ノイズ、タイマA/B、IRQ、BUSY、CT1/CT2
- CSMの簡易キーオンパルス
- ステレオPCM、ホスト側リサンプラ、trace→WAV、内蔵デモ

## 精度上の制限

Yamahaの公開マニュアルの仕様をもとに実装しています。
波形はstd::sin、位相は32bit。実チップの波形ROM・対数演算・切捨て・内部パイプラインは再現していません。
アタックは公開時間表の各RATEの値を使用し、高速ディケイも表の値を使用します。低速ディケイとアタックの曲線形状は近似で、内部ステップ列とは一致しません。
DT1はマニュアルの丸められた周波数差から単位値を推定。DT2も公開されたセント値を使用しています。
通常FM変調の倍率、無効KCの扱い、ノイズの分周・多項式、ランダムLFO、CSMパルス幅は暫定モデルです。
バス書込は即時適用であり、実チップの内部書込遅延やスロット順は未再現です。
CSMでのTLラッチなど詳細動作、未公開TEST機能、YM3012シリアル形式・DAC・アナログ回路は未再現です。
浮動小数点のため、異なるコンパイラやCPUでのビット一致は保証しません。

**高精度版としての完成ではなく、動作する独自コアの初版です。**
他のエミュレータとの比較は行っていません。実機データによる検証も未実施です。

## 検証

Linux/GCCでコンパイルし tests/test_core.cpp を実行済み。
440Hzは出力波形のゼロ交差でも確認。左右分離、減衰終了、タイマ期限、BUSY期限、
状態コピー、クロック刻み変更の一致、全アルゴリズムの有限出力、リサンプラのDCゲインを検査しています。
8アルゴリズムを順に使う6秒/48kHzのdemo.wavを同梱。クリッピングは0サンプルです。
Windows/MSVCのビルド・実行、実機との音色一致、GUI操作は未検証です。

## 参照元

- Yamaha YM2151 (OPM) Application Manual（Yamaha原著スキャン）
  https://github.com/electrified/rc2014-ym2151/blob/main/docs/LSI-_______%20Yamaha%20YM2151%20(OPM)%20Application%20Manual.pdf
  印刷ページ5〜21、特に図2.2〜2.16。リポジトリのエミュレータやプレーヤーのコードは参照していません。

## 0.7：出力サンプル対応の校正機能

チャンネル別・出力OP別に、左右それぞれ現サンプル/前サンプルを選択する
set_output_sample_delays(channel,left_mask,right_mask)を実装。
マスクのbit0/1/2/3はレジスタ順M1/M2/C1/C2です。全アルゴリズムの出力キャリアに適用します。
既定は両マスク0で従来の出力。どのOPが実機でずれるかは未確定なので自動では有効化しません。
これは時分割演算のサンプル境界を検証するための出力モデルです。
32スロットの演算順・各2クロックの内部回路・パイプライン全体を復元したものではありません。
FM接続、エンベロープ、レジスタ書込の内部タイミングは従来の近似を維持します。
OP履歴と設定はオブジェクトコピーに含まれ、resetで設定も履歴も初期化します。
設定切替のフェードはありません。発音前に設定してください。

CLIの最後にプロファイルファイルを指定可能。1行は「ch 左前サンプルmask 右前サンプルmask」。
chは0〜7、maskは0〜15。ch昇順で記述。#以降はコメント。
例としてch0のALG5で左右の一部成分の時刻を変える比較設定：

```
0 0x0e 0x02
```

これはLのM2/C1/C2を前サンプルに、RのM2のみ前サンプルにします。
実機の確定プリセットではありません。DAC等の全体遅延はこの設定に含めません。

実機確認用MDXと区間表はhardware-tests/を参照してください。

0.7検証：GCCでcore、precision、output_timingの3テストが通過。
追加テストは全8アルゴリズム×8チャンネル、前サンプル出力、チャンネル独立性、
部分左右差、状態コピー、刻み幅、reset、範囲外入力を検査しました。
