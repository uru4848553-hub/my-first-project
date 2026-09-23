"""Resolve自動配置ツール。

使い方:
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方"
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方" --check-only   # フェーズ1のチェックだけ

現在はフェーズ2（強制アライメントと output/plan.json の生成）まで。結果は output/report.md にも出力する。
"""
import argparse
import os
import sys
import time

from core.checks import check_project
from core.config import ConfigError, load_config
from core.report import write_report


def print_messages(check):
    for w in check.warnings:
        print(f"[警告] {w}")
    for e in check.errors:
        print(f"[エラー] {e}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="台本と素材から Resolve のタイムラインを自動生成する")
    parser.add_argument("folder", help="動画フォルダ（script.md・audio・media があるフォルダ）")
    parser.add_argument("--check-only", action="store_true", help="台本と素材のチェックだけ行う（音声処理なし）")
    args = parser.parse_args(argv)

    try:
        config = load_config()
    except ConfigError as e:
        print(f"[エラー] {e}")
        return 1

    # フェーズ1：台本解析・素材照合・エラーチェック
    check = check_project(args.folder)
    if check.errors or args.check_only:
        report_path = write_report(check) if os.path.isdir(args.folder) else None
        print_messages(check)
        if report_path:
            print(f"レポート: {report_path}")
        if check.errors:
            print(f"\nエラーが {len(check.errors)} 件あります。修正してから再実行してください。")
            return 1
        print(f"\nチェックOK: {len(check.scenes)} シーン / {len(check.entries)} セクション")
        for e in check.entries:
            print(f"  {e.section.label:<7} {e.media.name}")
        return 0

    print(f"チェックOK: {len(check.scenes)} シーン / {len(check.entries)} セクション")

    # フェーズ2：強制アライメントと plan.json
    from core.align import build_text, load_model, run_alignment, save_words, section_timings
    from core.ffmpeg import FFmpegError, probe_duration
    from core.plan import build_plan, report_rows, write_plan

    try:
        duration = probe_duration(check.audio)
    except FFmpegError as e:
        check.errors.append(f"ナレーション音声を読めません: {e}")
        write_report(check)
        print_messages(check)
        return 1
    print(f"ナレーション: {os.path.basename(check.audio)}（{duration:.1f}秒）")

    sections = [e.section for e in check.entries]
    started = time.time()
    try:
        model = load_model(config["whisper_model"])
        print("強制アライメント中...")
        words = run_alignment(model, check.audio, build_text(sections))
        save_words(words, check.folder)
        timings, ratio = section_timings(sections, words)
    except Exception as e:  # モデル読み込み・アライメントの失敗はまとめてレポートに残す
        check.errors.append(f"強制アライメントに失敗しました: {e}")
        write_report(check)
        print_messages(check)
        return 1
    print(f"アライメント完了（{time.time() - started:.0f}秒）")

    plan, plan_errors, plan_warnings = build_plan(check, timings, duration, config, ratio)
    check.errors.extend(plan_errors)
    check.warnings.extend(plan_warnings)
    plan_path = write_plan(plan, check.folder)
    report_path = write_report(check, report_rows(plan))

    print_messages(check)
    print(f"配置表: {plan_path}")
    print(f"レポート: {report_path}")
    if check.errors:
        print(f"\nエラーが {len(check.errors)} 件あります。report.md を確認してください。")
        return 1

    fps = plan["fps"]
    print()
    for s in plan["sections"]:
        print(f"  {s['label']:<7} {s['start_frame'] / fps:7.2f}秒〜  {s['duration_frames'] / fps:6.2f}秒  {s['media']['name']}")
    print("\n（フェーズ3以降の尺調整・Resolve への配置は未実装です）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
