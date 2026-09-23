"""強制アライメント（stable-ts）と、単語の時刻からセクション開始時刻を求める処理。

stable-ts を呼ぶのは run_alignment だけ。単語の時刻からセクションの開始時刻を求める
section_timings は、単語の並び（word, start, probability を持つもの）さえあれば動くので
音声やモデルなしで単体テストできる。
"""
import bisect
import difflib
import json
import os
import re
from dataclasses import dataclass

_SPACE = re.compile(r"\s+")


def _norm(text):
    return _SPACE.sub("", text).lower()


def _join(a, b):
    """行・セクションをつなぐ。英数字どうしが隣り合うときだけ空白を入れる（日本語は詰める）"""
    if a and b and a[-1].isascii() and a[-1].isalnum() and b[0].isascii() and b[0].isalnum():
        return a + " " + b
    return a + b


def build_text(sections):
    """アライメントに渡す台本全文"""
    text = ""
    for sec in sections:
        for line in sec.lines:
            text = _join(text, line)
    return text


@dataclass
class SectionTiming:
    start: float          # 開始時刻（秒）
    confidence: float | None   # セクション内の単語の平均確率（単語がなければ None）
    word_count: int


def _char_map(src, dst):
    """src の各文字位置 → dst の文字位置。対応がない位置は、次に対応する位置に寄せる。"""
    matcher = difflib.SequenceMatcher(None, src, dst, autojunk=False)
    mapping = [None] * (len(src) + 1)
    for a, b, size in matcher.get_matching_blocks():
        for k in range(size):
            mapping[a + k] = b + k
    mapping[len(src)] = len(dst)
    nxt = len(dst)
    for i in range(len(src), -1, -1):
        if mapping[i] is None:
            mapping[i] = nxt
        else:
            nxt = mapping[i]
    return mapping, matcher.ratio()


def section_timings(sections, words):
    """単語の並びから、各セクションの開始時刻と信頼度を求める。

    words: .word（文字列）, .start（秒）, .probability を持つオブジェクトの列（stable-ts の WordTiming）
    戻り値: (SectionTiming のリスト, 台本と単語列の一致度 0〜1)
    """
    words = [w for w in words if _norm(w.word)]
    if not words:
        raise ValueError("アライメント結果に単語がありません")

    # 台本側：セクションごとの文字範囲
    script = ""
    bounds = []
    for sec in sections:
        start = len(script)
        script += _norm("".join(sec.lines))
        bounds.append((start, len(script)))

    # 単語側：単語ごとの開始文字位置
    word_text = ""
    word_starts = []
    for w in words:
        word_starts.append(len(word_text))
        word_text += _norm(w.word)

    mapping, ratio = _char_map(script, word_text)

    def word_index(pos):
        return min(max(bisect.bisect_right(word_starts, pos) - 1, 0), len(words) - 1)

    timings = []
    for i, (a, b) in enumerate(bounds):
        wa, wb = mapping[a], mapping[b]
        first = word_index(wa)
        in_section = [w for w, ws in zip(words, word_starts) if wa <= ws < wb]
        probs = [w.probability for w in in_section if w.probability is not None]
        timings.append(SectionTiming(
            start=0.0 if i == 0 else float(words[first].start),
            confidence=sum(probs) / len(probs) if probs else None,
            word_count=len(in_section),
        ))
    return timings, ratio


def load_model(model_name, log=print):
    import stable_whisper
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        log("[警告] GPU が使えないため CPU で処理します（かなり遅くなります）")
    log(f"Whisper {model_name} を読み込み中（{device}）...")
    return stable_whisper.load_model(model_name, device=device)


def run_alignment(model, audio_path, text):
    """stable-ts で強制アライメントし、単語の列を返す"""
    result = model.align(audio_path, text, language="ja")
    if result is None:
        raise RuntimeError("アライメントに失敗しました（台本と音声が大きく違う可能性があります）")
    return result.all_words()


def save_words(words, folder):
    """単語ごとの結果を output/alignment.json に保存する（アライメントの確認・調査用）"""
    out_dir = os.path.join(folder, "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "alignment.json")
    data = [{"word": w.word, "start": w.start, "end": w.end, "probability": w.probability} for w in words]
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)
    return path
