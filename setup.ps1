# フェーズ0：環境構築スクリプト（Windows PowerShell）
# 使い方（このフォルダで）:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# オプション:
#   -CudaIndex cu128   PyTorch の CUDA 版を変える（既定 cu126。GTX 10xx〜RTX 40xx は cu126、RTX 50xx は cu128）
#   -VenvPath <パス>   仮想環境の作成先（既定 C:\AutoDavinch\venv）
#   -SkipEnvVars       Resolve 用の環境変数を設定しない
#
# 仮想環境は NTFS のドライブに置く。FAT32/exFAT などのドライブに置くと
# PyTorch のインストールが "No space left on device" で失敗する。

param(
    [string]$CudaIndex = "cu126",
    [string]$VenvPath = "C:\AutoDavinch\venv",
    [switch]$SkipEnvVars
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# 1. Python 3.11
Step "Python 3.11 の確認"
try {
    $pyver = & py -3.11 -c "import sys,struct;print(sys.version.split()[0], struct.calcsize('P')*8)"
} catch {
    $pyver = $null
}
if (-not $pyver) {
    Write-Host "Python 3.11 が見つかりません。次のどちらかでインストールしてから再実行してください:" -ForegroundColor Red
    Write-Host "  winget install Python.Python.3.11"
    Write-Host "  または https://www.python.org/downloads/ から 3.11 系の Windows installer (64-bit)"
    exit 1
}
Write-Host "Python $pyver"
if ($pyver -notmatch " 64$") {
    Write-Host "64bit 版の Python 3.11 が必要です。" -ForegroundColor Red
    exit 1
}

# 2. 仮想環境
Step "仮想環境の作成 ($VenvPath)"
$py = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $py)) {
    & py -3.11 -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { Write-Host "仮想環境の作成に失敗しました。" -ForegroundColor Red; exit 1 }
}
& $py -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Write-Host "pip の更新に失敗しました。" -ForegroundColor Red; exit 1 }

# このフォルダから仮想環境の Python を呼ぶための run.bat
Set-Content -Path (Join-Path $PSScriptRoot "run.bat") -Encoding Oem -Value "@`"$py`" %*"

# 3. CUDA 版 PyTorch → stable-ts
Step "CUDA 版 PyTorch ($CudaIndex) のインストール"
# 別の CUDA 版が入っていると pip は「インストール済み」とみなすので、先に削除する
$current = & $py -c "import importlib.util as u, importlib.metadata as m; print(m.version('torch') if u.find_spec('torch') else '')"
if ($current -and ($current -notlike "*+$CudaIndex")) {
    Write-Host "torch $current を削除して $CudaIndex 版に入れ替えます"
    & $py -m pip uninstall -y torch torchaudio
}
& $py -m pip install torch torchaudio --index-url "https://download.pytorch.org/whl/$CudaIndex"
if ($LASTEXITCODE -ne 0) { Write-Host "PyTorch のインストールに失敗しました。" -ForegroundColor Red; exit 1 }

Step "stable-ts のインストール"
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "stable-ts のインストールに失敗しました。" -ForegroundColor Red; exit 1 }

# 4. ffmpeg
Step "ffmpeg の確認"
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "ffmpeg: $((Get-Command ffmpeg).Source)"
} else {
    Write-Host "ffmpeg が見つかりません。次でインストールし、PowerShell を開き直してください:" -ForegroundColor Yellow
    Write-Host "  winget install Gyan.FFmpeg"
}

# 5. Resolve 用環境変数（ユーザー環境変数に設定）
if (-not $SkipEnvVars) {
    Step "Resolve 用環境変数の設定"
    $api = "$env:PROGRAMDATA\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
    $lib = "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
    $modules = "$api\Modules\"

    if (-not (Test-Path $lib)) { Write-Host "注意: $lib が見つかりません（Resolve のインストール先を確認）" -ForegroundColor Yellow }
    if (-not (Test-Path $modules)) { Write-Host "注意: $modules が見つかりません" -ForegroundColor Yellow }

    [Environment]::SetEnvironmentVariable("RESOLVE_SCRIPT_API", $api, "User")
    [Environment]::SetEnvironmentVariable("RESOLVE_SCRIPT_LIB", $lib, "User")

    $pp = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
    $entries = @()
    if ($pp) { $entries = $pp -split ";" | Where-Object { $_ } }
    if ($entries -notcontains $modules) {
        $entries += $modules
        [Environment]::SetEnvironmentVariable("PYTHONPATH", ($entries -join ";"), "User")
    }

    # このセッションにも反映
    $env:RESOLVE_SCRIPT_API = $api
    $env:RESOLVE_SCRIPT_LIB = $lib
    $env:PYTHONPATH = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")

    Write-Host "RESOLVE_SCRIPT_API = $api"
    Write-Host "RESOLVE_SCRIPT_LIB = $lib"
    Write-Host "PYTHONPATH         = $env:PYTHONPATH"
}

# 6. チェック
Step "環境チェック"
& $py tools\check_env.py

Write-Host "`n次に Resolve を起動してプロジェクトを開き、接続テストを実行してください:" -ForegroundColor Green
Write-Host "  .\run.bat tools\resolve_test.py"
