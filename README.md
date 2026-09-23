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
Python 3.11 64bit が未インストールなら先に入れる（`winget install Python.Python.3.11`）。
ffmpeg が未インストールなら `winget install Gyan.FFmpeg`。

```powershell
cd "G:\@Auto_Davinch-Cloude"
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

これで次が行われる:
- `.venv`（Python 3.11 の仮想環境）作成
- CUDA 版 PyTorch と stable-ts のインストール
- ユーザー環境変数 `RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB` / `PYTHONPATH` の設定
- `tools\check_env.py` による確認

PyTorch が CUDA を認識しない（古いNVIDIAドライバ）場合は `.\setup.ps1 -CudaIndex cu126` で再実行。

### 3. Whisper large-v3 の読み込み確認（初回は約3GBダウンロード）
```powershell
.venv\Scripts\python tools\check_env.py --load-model
```

### 4. Resolve 接続テスト
Resolve を起動してプロジェクトを開いた状態で:
```powershell
.venv\Scripts\python tools\resolve_test.py
```
成功するとプロジェクト名などが表示される:
```
[OK] 接続成功: DaVinci Resolve Studio 21.0.3...
     プロジェクト名   : ○○○
```
