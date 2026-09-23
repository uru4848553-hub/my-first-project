"""Resolve自動配置ツール。

使い方:
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方"

現在はフェーズ1（台本解析・素材照合・エラーチェック）まで。結果は output/report.md に出力する。
"""
import argparse
import os
import sys

from core.checks import check_project
from core.report import write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="台本と素材から Resolve のタイムラインを自動生成する")
    parser.add_argument("folder", help="動画フォルダ（script.md・audio・media があるフォルダ）")
    args = parser.parse_args(argv)

    check = check_project(args.folder)
    report_path = write_report(check) if os.path.isdir(args.folder) else None

    for w in check.warnings:
        print(f"[警告] {w}")
    for e in check.errors:
        print(f"[エラー] {e}")
    if report_path:
        print(f"レポート: {report_path}")

    if check.errors:
        print(f"\nエラーが {len(check.errors)} 件あります。修正してから再実行してください。")
        return 1

    print(f"\nチェックOK: {len(check.scenes)} シーン / {len(check.entries)} セクション")
    for e in check.entries:
        print(f"  {e.section.label:<7} {e.media.name}")
    print("\n（フェーズ2以降のアライメント・Resolve への配置は未実装です）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
