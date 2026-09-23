"""フェーズ0：環境チェック（Python / ffmpeg / CUDA版PyTorch / stable-ts）。

使い方:
    run.bat tools\\check_env.py              # 基本チェック
    run.bat tools\\check_env.py --load-model # Whisper モデルを実際にGPUに読み込む（初回は約3GBダウンロード）
"""
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

results = []


def report(ok, name, detail):
    results.append(ok)
    print(f"[{'OK' if ok else 'NG'}] {name}: {detail}")


def check_python():
    ver = sys.version.split()[0]
    bits = struct.calcsize("P") * 8
    ok = sys.version_info[:2] == (3, 13) and bits == 64
    report(ok, "Python", f"{ver} {bits}bit ({sys.executable})" + ("" if ok else " → 3.13 64bit が必要です（Resolve 21 の要件）"))


def check_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        if not path:
            report(False, tool, "見つかりません（PATH を確認してください）")
            continue
        out = subprocess.run([path, "-version"], capture_output=True, text=True).stdout
        report(True, tool, out.splitlines()[0] if out else path)


def check_torch():
    try:
        import torch
    except ImportError:
        report(False, "PyTorch", "インストールされていません")
        return False
    if not torch.cuda.is_available():
        report(False, "PyTorch CUDA", f"torch {torch.__version__} だが CUDA が使えません（CPU版が入っている可能性）")
        return False

    name = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    arch = f"sm_{major}{minor}"
    if arch not in torch.cuda.get_arch_list():
        report(False, "PyTorch CUDA",
               f"torch {torch.__version__} は {name}（{arch}）に対応していません → setup.ps1 を -CudaIndex cu126 で再実行")
        return False

    # 認識だけでなく、実際に GPU で計算できるか確認する
    try:
        x = torch.ones(256, 256, device="cuda")
        (x @ x).sum().item()
    except Exception as e:
        report(False, "PyTorch CUDA", f"{name} で計算できません: {e}")
        return False
    report(True, "PyTorch CUDA", f"torch {torch.__version__} / CUDA {torch.version.cuda} / {name}（{arch}）で計算OK")
    return True


def check_stable_ts():
    try:
        import stable_whisper
    except ImportError as e:
        report(False, "stable-ts", f"読み込めません: {e}")
        return False
    report(True, "stable-ts", getattr(stable_whisper, "__version__", "読み込みOK"))
    return True


def check_pillow():
    try:
        import PIL
    except ImportError:
        report(False, "Pillow（テロップ用）", "入っていません。  .\\run.bat -m pip install pillow  を実行してください")
        return False
    report(True, "Pillow（テロップ用）", PIL.__version__)
    return True


def check_model(model_name):
    import stable_whisper
    print(f"     Whisper {model_name} を読み込み中（初回はダウンロードに時間がかかります）...")
    try:
        stable_whisper.load_model(model_name, device="cuda")
    except Exception as e:
        report(False, "Whisper モデル", f"{model_name} の読み込みに失敗: {e}")
        return
    report(True, "Whisper モデル", f"{model_name} を GPU に読み込めました")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--load-model", action="store_true", help="Whisper モデルを実際に読み込んで確認する")
    args = parser.parse_args()

    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    check_python()
    check_ffmpeg()
    torch_ok = check_torch()
    stable_ok = check_stable_ts()
    check_pillow()
    if args.load_model and torch_ok and stable_ok:
        check_model(config["whisper_model"])

    print()
    if all(results):
        print("すべてのチェックに合格しました。")
        return 0
    print("NG の項目があります。README.md の手順を確認してください。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
