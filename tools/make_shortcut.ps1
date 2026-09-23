# デスクトップに「Resolve自動配置」のショートカット（アイコン付き）を作る
# ショートカット作成.bat から呼ばれる
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$runBat = Join-Path $repo "run.bat"
$icon = Join-Path $repo "assets\app.ico"
$app = Join-Path $repo "app.py"

if (-not (Test-Path $runBat)) {
    Write-Host "[エラー] run.bat がありません。先に setup.ps1 を実行してください。" -ForegroundColor Red
    exit 1
}
# run.bat の中身は  @"C:\AutoDavinch\venv\Scripts\python.exe" %*
$m = [regex]::Match((Get-Content $runBat -Raw), '"([^"]*python\.exe)"')
if (-not $m.Success) {
    Write-Host "[エラー] run.bat から python.exe の場所を読み取れません。" -ForegroundColor Red
    exit 1
}
$python = $m.Groups[1].Value
$pythonw = $python -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path $pythonw)) {
    Write-Host "[エラー] $pythonw がありません。" -ForegroundColor Red
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath("Desktop")
foreach ($dir in @($desktop, $repo)) {
    $lnk = Join-Path $dir "Resolve自動配置.lnk"
    $s = $shell.CreateShortcut($lnk)
    $s.TargetPath = $pythonw          # pythonw.exe なので黒い画面が出ない
    $s.Arguments = "`"$app`""
    $s.WorkingDirectory = $repo
    $s.IconLocation = "$icon,0"
    $s.Description = "Resolve 自動配置アプリ"
    $s.Save()
    Write-Host "作成しました: $lnk"
}
Write-Host ""
Write-Host "デスクトップの「Resolve自動配置」をダブルクリックするとアプリが開きます。" -ForegroundColor Green
Write-Host "タスクバーに置きたいときは、ショートカットを右クリック →「タスクバーにピン留めする」。"
