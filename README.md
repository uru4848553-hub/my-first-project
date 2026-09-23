# Resolve自動配置ツール

使い方は [取扱説明書.md](取扱説明書.md)、仕様は [CLAUDE.md](CLAUDE.md) を参照。フェーズ0〜5（環境構築から Resolve への配置、通し実行）まで実装済み。

## 保存先 `G:\@Auto_Davinch-Cloude` に取り込む

PowerShell で:

```powershell
cd "G:\@Auto_Davinch-Cloude"
git init
git remote add origin https://github.com/uru4848553-hub/my-first-project.git
git fetch origin claude/claude-md-phase-0-qxn5wu
git checkout -f -B main FETCH_HEAD
```

（`-f` は、既に置いてある CLAUDE.md をリポジトリ版で上書きするため。内容は同じ）

## フェーズ0の手順

### 1. Resolve 側の設定
DaVinci Resolve Studio → 環境設定 → システム → 一般 → 「外部スクリプトに使用」を **ローカル** にして Resolve を再起動。

### 2. 環境構築
Python 3.13 64bit が未インストールなら先に入れる（`winget install Python.Python.3.13`）。
Resolve 21 の fusionscript は Python 3.13 向けで、3.11 では読み込めない。
ffmpeg が未インストールなら `winget install Gyan.FFmpeg`。

```powershell
cd "G:\@Auto_Davinch-Cloude"
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

これで次が行われる:
- 仮想環境（Python 3.13）を `C:\AutoDavinch\venv` に作成し、それを呼び出す `run.bat` を生成
  （G: が NTFS でないため仮想環境は C: に置く。場所は `-VenvPath` で変更可）
- CUDA 版 PyTorch と stable-ts のインストール
- ユーザー環境変数 `RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB` / `PYTHONPATH` の設定
- `tools\check_env.py` による確認

PyTorch は既定で CUDA 12.6 版（GTX 10xx〜RTX 40xx 対応）。RTX 50xx の場合は `.\setup.ps1 -CudaIndex cu128` で再実行。

### 3. Whisper large-v3 の読み込み確認（初回は約3GBダウンロード）
```powershell
.\run.bat tools\check_env.py --load-model
```

### 4. Resolve 接続テスト
Resolve を起動してプロジェクトを開いた状態で:
```powershell
.\run.bat tools\resolve_test.py
```
成功するとプロジェクト名などが表示される:
```
[OK] 接続成功: DaVinci Resolve Studio 21.0.3...
     プロジェクト名   : ○○○
```

## フェーズ1：台本解析・素材照合・エラーチェック

```powershell
.\run.bat autoedit.py "D:\動画\動画_AI副業の始め方"
```

- `script.md` / `media/` / `audio/` を読み、台本のセクション（S01, S03[a] …）と素材を対応付ける
- エラー・警告と対応表を `output\report.md` に出力する。エラーがあれば終了コード 1
- `--check-only` を付けるとここで終わる（音声処理なし）

サンプル（中身が空のダミーファイル）で試す:
```powershell
.\run.bat autoedit.py samples\動画_サンプル
```

単体テスト（Resolve・音声処理なしで動く）:
```powershell
.\run.bat -m unittest discover -s tests -t . -v
```

## フェーズ2：強制アライメントと plan.json

`--check-only` を付けずに実行すると、フェーズ1のチェックに続けて:

1. ffprobe でナレーションの長さを取得
2. stable-ts（Whisper large-v3）で台本全文を音声に強制アライメント
3. 各セクションの開始時刻＝そのセクション最初の単語の開始時刻（最初のセクションは0秒）を求め、30fps のフレームに丸める（終了フレーム＝次の開始フレーム、最後は音声の終端）
4. `output\plan.json`（配置表）と `output\report.md`（開始時刻・尺入り）を出力。単語ごとの結果は `output\alignment.json`

警告：尺が1秒未満のセクション、単語の平均確率が `low_confidence`（config.json、既定 0.5）未満のセクション、台本とアライメント結果の文字の一致度が 90% 未満。
エラー：開始時刻の逆転、尺0フレーム、開始時刻が音声の長さを超える（plan.json の `errors` に入り、フェーズ4では使わない）。

## フェーズ3：尺調整

フェーズ2に続けて自動で行う（アライメントでエラーがあれば行わない）。plan.json の各セクションに、タイムラインへ置くクリップの列 `clips` を付ける。

- 静止画：セクション尺そのまま（`image`）
- 動画がセクションより長い：素材の先頭から使い、セクション尺で切る（`video`、`source_out_sec` まで使う）
- 動画がセクションより短い：動画の直後に最終フレームの静止画を置いて埋める（`freeze`）。静止画は ffmpeg で `media\_freeze\<動画名>_last_<内容のハッシュ>.png` に書き出す（毎回書き出し、内容が変われば別名になる）
- 静止フレームで埋めた尺が2秒以上なら警告

各クリップは `record_frame`（タイムライン上の開始フレーム）と `frames`（長さ）を持ち、隙間も重なりもなく並ぶ。

静止画（素材の画像・最終フレームの PNG）は、その画像が必要な尺だけ続く動画（H.264、30fps）に変換してから置く（Resolve は静止画の長さの指定を無視して5秒で置くため）。素材の画像は `media\_stills\`、最終フレームは `media\_freeze\` に作り、同じ画像・同じ長さなら使い回す。元の画像は clip の `image`、置く動画は `path`。

## フェーズ4：Resolve への配置

Resolve を起動してプロジェクトを開いた状態で、オプションなしで実行すると、フェーズ3に続けて Resolve に配置する。

- メディアプールにフォルダ名のビンを作り（あれば使い回す）、素材・静止画・ナレーションを取り込む（取り込み済みのファイルは使い回す）
- 新しいタイムライン `{フォルダ名}_{YYYYMMDD_HHMM}`（同名があれば `_2` …）を作り、1080×1920・30fps・解像度違いの扱い（fit→scaleToFit／fill→scaleToCrop）を設定
  - タイムライン単位で30fpsにできず、プロジェクトにほかのタイムラインがなければ、プロジェクトのフレームレートを30にして作り直す。ほかのタイムラインがあればエラーで止まる（既存のタイムラインは変えない）
- V1 に clips どおり配置（動画は映像だけ）、A1 にナレーションを0フレームから、シーン先頭にマーカー
- 置いたクリップの位置・長さを読み戻して plan と照合し、違えばエラーで止まる

オプション:
- `--no-resolve`：plan.json まで作り、Resolve には置かない
- `--from-plan`：前回の `output\plan.json` を使って Resolve に置くだけ（Whisper をやり直さない）
- `--fake-align`：Whisper を使わず、原稿の文字数で時間を割り振る（配置のテスト用。本番には使わない）

録音なしで配置を試す:
```powershell
.\run.bat tools\make_sample.py
.\run.bat autoedit.py samples\動画_生成テスト --fake-align
```
