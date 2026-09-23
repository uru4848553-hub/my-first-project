"""フェーズ0：Resolve API 接続テスト。現在のプロジェクト名を表示する。

使い方（Resolve を起動してプロジェクトを開いた状態で）:
    .venv\\Scripts\\python tools\\resolve_test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resolve_connect import ResolveConnectionError, get_resolve  # noqa: E402


def main():
    if sys.version_info[:2] != (3, 11):
        print(f"[警告] Python {sys.version.split()[0]} で実行中です（推奨は 3.11）")

    try:
        resolve = get_resolve()
    except ResolveConnectionError as e:
        print(f"[NG] {e}")
        return 1

    print(f"[OK] 接続成功: {resolve.GetProductName()} {resolve.GetVersionString()}")

    project = resolve.GetProjectManager().GetCurrentProject()
    if project is None:
        print("[NG] プロジェクトが開かれていません。Resolve でプロジェクトを開いてください。")
        return 1

    print(f"     プロジェクト名   : {project.GetName()}")
    print(f"     タイムライン数   : {project.GetTimelineCount()}")
    timeline = project.GetCurrentTimeline()
    print(f"     現在のタイムライン: {timeline.GetName() if timeline else '（なし）'}")
    print(f"     フレームレート   : {project.GetSetting('timelineFrameRate')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
