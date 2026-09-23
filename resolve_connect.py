"""DaVinci Resolve Scripting API への接続。

環境変数 RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB が未設定でも、
Windows の標準インストール先を使って接続を試みる。
"""
import os
import subprocess
import sys
import time

DEFAULT_SCRIPT_API = os.path.join(
    os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
    "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting",
)
DEFAULT_SCRIPT_LIB = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
RESOLVE_EXE = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
# Resolve を起動したばかりのときに開いている、名前のないプロジェクト
UNTITLED_PROJECTS = {"Untitled Project", "名称未設定プロジェクト"}


class ResolveConnectionError(RuntimeError):
    pass


def _prepare_environment():
    api = os.environ.get("RESOLVE_SCRIPT_API") or DEFAULT_SCRIPT_API
    lib = os.environ.get("RESOLVE_SCRIPT_LIB") or DEFAULT_SCRIPT_LIB
    # DaVinciResolveScript.py は RESOLVE_SCRIPT_LIB を参照して fusionscript を読み込む
    os.environ["RESOLVE_SCRIPT_API"] = api
    os.environ["RESOLVE_SCRIPT_LIB"] = lib

    modules = os.path.join(api, "Modules")
    if modules not in sys.path:
        sys.path.append(modules)
    return api, lib, modules


def get_resolve(log=lambda msg: None):
    """起動中の Resolve オブジェクトを返す。失敗時は原因付きで ResolveConnectionError。

    log: 進行状況を受け取る関数（接続途中で止まった箇所を特定するため）
    """
    api, lib, modules = _prepare_environment()
    log(f"RESOLVE_SCRIPT_LIB = {lib}")
    log(f"Modules            = {modules}")

    if not os.path.isfile(lib):
        raise ResolveConnectionError(
            f"fusionscript.dll が見つかりません: {lib}\n"
            "Resolve のインストール先が違う場合は RESOLVE_SCRIPT_LIB を設定してください。"
        )
    if not os.path.isfile(os.path.join(modules, "DaVinciResolveScript.py")):
        raise ResolveConnectionError(
            f"DaVinciResolveScript.py が見つかりません: {modules}\n"
            "RESOLVE_SCRIPT_API の設定を確認してください。"
        )

    log("DaVinciResolveScript を読み込み中...")
    try:
        import DaVinciResolveScript as dvr_script
    except ImportError as e:
        raise ResolveConnectionError(
            f"DaVinciResolveScript を読み込めません: {e}\n"
            "Python が 3.13 64bit か確認してください（Resolve 21 は 3.11 では動きません）。"
        ) from e

    log("Resolve に接続中...")
    resolve = dvr_script.scriptapp("Resolve")
    if resolve is None:
        raise ResolveConnectionError(
            "Resolve に接続できません。次を確認してください:\n"
            "  1. DaVinci Resolve Studio が起動している\n"
            "  2. 環境設定 → システム → 一般 → 「外部スクリプトに使用」が「ローカル」\n"
            "  3. 設定変更後に Resolve を再起動した"
        )
    return resolve


def ensure_resolve(launch=True, timeout=240, log=print):
    """Resolve に接続する。起動していなければ起動して、つながるまで待つ。

    戻り値: (resolve, 今回起動したか)
    """
    try:
        return get_resolve(), False
    except ResolveConnectionError:
        exe = os.environ.get("RESOLVE_EXE") or RESOLVE_EXE
        if not launch or not os.path.isfile(exe):
            raise

    log("DaVinci Resolve を起動しています（1〜2分かかることがあります）...")
    subprocess.Popen([exe], close_fds=True)
    import DaVinciResolveScript as dvr_script   # get_resolve で読み込み済み
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(5)
        resolve = dvr_script.scriptapp("Resolve")
        if resolve is not None and resolve.GetProjectManager() is not None:
            log("DaVinci Resolve に接続しました")
            return resolve, True
    raise ResolveConnectionError(
        f"DaVinci Resolve を起動しましたが、{timeout}秒待っても接続できません。\n"
        "環境設定 → システム → 一般 →「外部スクリプトに使用」が「ローカル」か確認してください。"
    )


def open_project(resolve, name, log=print):
    """プロジェクト name を開く（なければ作る）。name が空なら、今開いているプロジェクトをそのまま使う。"""
    pm = resolve.GetProjectManager()
    current = pm.GetCurrentProject()
    if not name:
        if current is None:
            raise ResolveConnectionError("Resolve でプロジェクトが開かれていません")
        return current
    if current is not None and current.GetName() == name:
        return current
    if current is not None and current.GetName() not in UNTITLED_PROJECTS:
        pm.SaveProject()
    project = pm.LoadProject(name)
    if project is None:
        log(f"Resolve にプロジェクト「{name}」を作成します")
        project = pm.CreateProject(name)
    else:
        log(f"Resolve のプロジェクト「{name}」を開きました")
    if project is None:
        raise ResolveConnectionError(f"Resolve のプロジェクト「{name}」を開けません（作成もできません）")
    return project
