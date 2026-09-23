"""DaVinci Resolve Scripting API への接続。

環境変数 RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB が未設定でも、
Windows の標準インストール先を使って接続を試みる。
"""
import os
import sys

DEFAULT_SCRIPT_API = os.path.join(
    os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
    "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting",
)
DEFAULT_SCRIPT_LIB = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"


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
            "Python が 3.11 64bit か確認してください。"
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
