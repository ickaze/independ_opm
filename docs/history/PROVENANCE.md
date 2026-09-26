# 由来と撤去記録

旧0.10bおよび先行0.11bには、ユーザー提供X68Sound src020615を参照したLFO処理がありました。今回、名称と許諾表示だけでなく対象の実装と参照比較試験を置き換えています。

- LfoClockを撤去。PeriodicModulatorで実測の反転順の進み幅を実装。
- lfo_valueを撤去。実測波形の数値規則からperiodic_valuesを実装。
- write_register/synthesizeの関連処理を新しい状態・整数深度/感度へ接続。
- tests/reference_lfo.cpp、run_reference_check.pyを撤去。原版の読込/比較は不要。
- test_precision内の参照由来LFO期待値を撤去。test_periodicを追加。
- reference_hashes.json、旧再作成報告、旧コードを含む2本のpatchを今回の配布から除外。

公開マニュアルの数値仕様に基づく他の音源処理、出力タイミング測定モデル、独自ランダムモデルは継続します。系列の17次という性質は測定結果として記録します。

research/recording-analysis.zipのファイル一覧とテキストも点検しています。配布ファイル一覧とハッシュはPACKAGE_MANIFEST.jsonを参照してください。これは過去の外部参照を隠すための履歴書き換えではありません。
