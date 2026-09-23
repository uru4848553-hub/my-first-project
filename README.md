# Resolve自動配置ツール

仕様は [CLAUDE.md](CLAUDE.md) を参照。現在は **フェーズ0（環境構築と Resolve 接続テスト）** まで。

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
- アライメントと Resolve への配置はまだ行わない（フェーズ2以降）

サンプル（中身が空のダミーファイル）で試す:
```powershell
.\run.bat autoedit.py samples\動画_サンプル
```

単体テスト（Resolve・音声処理なしで動く）:
```powershell
.\run.bat -m unittest discover -s tests -t . -v
```
