"""Resolve自動配置ツール。

使い方（Resolve を起動し、プロジェクトを開いた状態で）:
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方"
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方" --check-only   # フェーズ1のチェックだけ
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方" --no-resolve   # plan.json まで作り、Resolve には置かない
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方" --from-plan    # 前回の output/plan.json を使って Resolve に置くだけ
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方" --fake-align   # Whisper を使わず文字数で時間を割り振る（配置のテスト用）
    run.bat autoedit.py "D:\\動画\\動画_AI副業の始め方" --launch-resolve --project 自動編集
        # Resolve が起動していなければ起動し、プロジェクト「自動編集」を開いて（なければ作って）置く

結果は output/report.md・output/plan.json に出力する。
"""
import argparse
import json
import os
import sys
import time
import traceback

from core.checks import check_project
from core.config import ConfigError, load_config
from core.report import write_report


def print_messages(check):
    for w in check.warnings:
        print(f"[警告] {w}")
    for e in check.errors:
        print(f"[エラー] {e}")


def append_report(folder, lines):
    path = os.path.join(folder, "output", "report.md")
    with open(path, "a", encoding="utf-8") as fp:
        fp.write("\n" + "\n".join(lines) + "\n")


def check_only(folder):
    """フェーズ1だけ。終了コードを返す"""
    check = check_project(folder)
    report_path = write_report(check) if os.path.isdir(folder) else None
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


def build(folder, config, fake_align=False):
    """フェーズ1〜3。成功すれば plan を、失敗すれば None を返す"""
    # フェーズ1：台本解析・素材照合・エラーチェック
    check = check_project(folder)
    if check.errors:
        check_only(folder)
        return None
    print(f"チェックOK: {len(check.scenes)} シーン / {len(check.entries)} セクション")

    # フェーズ2：強制アライメントと plan.json
    from core.align import build_text, load_model, proportional_timings, run_alignment, save_words, section_timings
    from core.ffmpeg import FFmpegError, probe_duration
    from core.fit import apply_fit
    from core.plan import build_plan, report_rows, write_plan

    try:
        duration = probe_duration(check.audio)
    except FFmpegError as e:
        check.errors.append(f"ナレーション音声を読めません: {e}")
        write_report(check)
        print_messages(check)
        return None
    print(f"ナレーション: {os.path.basename(check.audio)}（{duration:.1f}秒）")
    bgm_duration = None
    if check.bgm:
        try:
            bgm_duration = probe_duration(check.bgm)
        except FFmpegError as e:
            check.errors.append(f"BGM を読めません: {e}")
            write_report(check)
            print_messages(check)
            return None
        print(f"BGM: {os.path.basename(check.bgm)}（{bgm_duration:.1f}秒）")

    sections = [e.section for e in check.entries]
    started = time.time()
    ratio = None
    try:
        if fake_align:
            print("[警告] --fake-align：Whisper を使わず、原稿の文字数で時間を割り振ります（配置のテスト用）")
            timings = proportional_timings(sections, duration)
        else:
            model = load_model(config["whisper_model"])
            print("強制アライメント中...")
            words = run_alignment(model, check.audio, build_text(sections))
            save_words(words, check.folder)
            timings, ratio = section_timings(sections, words)
    except Exception as e:  # モデル読み込み・アライメントの失敗はまとめてレポートに残す
        check.errors.append(f"強制アライメントに失敗しました: {e}")
        write_report(check)
        print_messages(check)
        return None
    print(f"アライメント完了（{time.time() - started:.0f}秒）")

    plan, plan_errors, plan_warnings = build_plan(check, timings, duration, config, ratio, fake=fake_align,
                                                   bgm_duration=bgm_duration)
    check.errors.extend(plan_errors)
    check.warnings.extend(plan_warnings)

    # フェーズ3：尺調整（動画が足りない分は最終フレームの静止画で埋める）
    if not plan_errors:
        fit_errors, fit_warnings = apply_fit(plan)
        check.errors.extend(fit_errors)
        check.warnings.extend(fit_warnings)

    plan_path = write_plan(plan, check.folder)
    report_path = write_report(check, report_rows(plan))

    print_messages(check)
    print(f"配置表: {plan_path}")
    print(f"レポート: {report_path}")
    if check.errors:
        print(f"\nエラーが {len(check.errors)} 件あります。report.md を確認してください。")
        return None

    fps = plan["fps"]
    print()
    for s in plan["sections"]:
        freeze = f"（うち静止 {s['freeze_frames'] / fps:.2f}秒）" if s["freeze_frames"] else ""
        print(f"  {s['label']:<7} {s['start_frame'] / fps:7.2f}秒〜  {s['duration_frames'] / fps:6.2f}秒  {s['media']['name']}{freeze}")
    return plan


def load_plan(folder):
    path = os.path.join(folder, "output", "plan.json")
    if not os.path.isfile(path):
        print(f"[エラー] {path} がありません。先に --from-plan なしで実行してください。")
        return None
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def place_in_resolve(plan, folder, launch=False, project=None):
    """フェーズ4：Resolve への配置。終了コードを返す

    launch: Resolve が起動していなければ起動する
    project: このプロジェクトを開いて（なければ作って）置く。None なら今開いているプロジェクト
    """
    from core.resolve_place import PlaceError, place
    from resolve_connect import ResolveConnectionError, ensure_resolve, open_project

    print("\nResolve に配置中...")
    try:
        resolve, _ = ensure_resolve(launch=launch)
        open_project(resolve, project)
        name, warnings = place(resolve, plan)
    except (ResolveConnectionError, PlaceError) as e:
        print(f"[エラー] Resolve への配置に失敗しました: {e}")
        append_report(folder, ["## Resolve への配置", "", f"- 失敗: {e}"])
        return 1
    except Exception as e:  # API の想定外の動きは原因調査のため詳細を出す
        traceback.print_exc()
        print(f"[エラー] Resolve への配置中に想定外のエラーが起きました: {e}")
        append_report(folder, ["## Resolve への配置", "", f"- 失敗（想定外のエラー）: {e}"])
        return 1

    for w in warnings:
        print(f"[警告] {w}")
    append_report(folder, ["## Resolve への配置", "", f"- タイムライン: {name}"] + [f"- 警告: {w}" for w in warnings])
    print(f"\nResolve にタイムライン「{name}」を作成しました。内容を確認してください。")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="台本と素材から Resolve のタイムラインを自動生成する")
    parser.add_argument("folder", help="動画フォルダ（script.md・audio・media があるフォルダ）")
    parser.add_argument("--fake-align", action="store_true",
                        help="Whisper を使わず、原稿の文字数で時間を割り振る（配置のテスト用。本番には使わない）")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-only", action="store_true", help="台本と素材のチェックだけ行う（音声処理なし）")
    mode.add_argument("--no-resolve", action="store_true", help="plan.json まで作り、Resolve には置かない")
    mode.add_argument("--from-plan", action="store_true", help="前回の output/plan.json を使って Resolve に置くだけ")
    parser.add_argument("--launch-resolve", action="store_true", help="Resolve が起動していなければ起動する")
    parser.add_argument("--project", help="Resolve のこのプロジェクトに置く（なければ作る）。省略時は今開いているプロジェクト")
    args = parser.parse_args(argv)

    if args.check_only:
        return check_only(args.folder)
    if args.from_plan:
        plan = load_plan(args.folder)
        return 1 if plan is None else place_in_resolve(plan, args.folder, args.launch_resolve, args.project)

    try:
        config = load_config()
    except ConfigError as e:
        print(f"[エラー] {e}")
        return 1

    plan = build(args.folder, config, fake_align=args.fake_align)
    if plan is None:
        return 1
    if args.no_resolve:
        print("\n（--no-resolve のため Resolve には配置していません）")
        return 0
    return place_in_resolve(plan, args.folder, args.launch_resolve, args.project)


if __name__ == "__main__":
    sys.exit(main())
