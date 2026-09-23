"""Resolve 自動配置アプリ（画面）。

台本・ナレーション・BGM・シーンごとの素材を選んで「スタート」を押すと、
動画フォルダを作り、autoedit.py を実行して DaVinci Resolve にタイムラインを作る。
（Resolve が起動していなければ起動する）

起動: アプリ起動.bat をダブルクリック（または run.bat app.py）
"""
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.assemble import assemble, auto_assign, validate  # noqa: E402
from core.script import parse_script  # noqa: E402

SETTINGS = os.path.join(ROOT, "app_settings.json")
AUDIO_TYPES = [("音声", "*.wav *.mp3 *.m4a"), ("すべて", "*.*")]
MEDIA_TYPES = [("動画・画像", "*.mp4 *.mov *.png *.jpg *.jpeg"), ("すべて", "*.*")]
SCRIPT_TYPES = [("台本", "*.md *.txt"), ("すべて", "*.*")]
EXAMPLE = """\
## S01
こんにちは、ヒロキです。今日はAI副業の始め方を話します。

## S02
まず結論から言うと、最初の3ヶ月は収益ゼロを覚悟してください。

## S03
[a] 実際の画面を見てください。ここで設定を開きます。
[b] すると、このように結果が表示されます。
"""
HELP = """\
・「## S01」「## S02」… でシーンを区切り、その下にナレーションの文章を書きます
・ナレーションの音声と同じ文章にしてください（違うと切り替え位置がずれます）
・1つのシーンで素材を切り替えるときは、行頭に [a] [b] … を付けます
・「//」で始まる行はメモ（テロップやカメラの指示など。読み上げない）"""


def load_settings():
    try:
        with open(SETTINGS, encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, ValueError):
        return {}


def save_settings(data):
    try:
        with open(SETTINGS, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
    except OSError:
        pass


def hide_console():
    """アプリ起動.bat から起動したときの黒い画面を隠す"""
    if os.name == "nt":
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)


class App:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.sections = []
        self.materials = {}          # {セクションのキー: 素材のパス}
        self.narration = tk.StringVar()
        self.bgm = tk.StringVar()
        self.name = tk.StringVar(value=self.settings.get("name", ""))
        self.base_dir = tk.StringVar(value=self.settings.get("base_dir", ""))
        self.project = tk.StringVar(value=self.settings.get("project", "自動編集"))
        self.launch = tk.BooleanVar(value=self.settings.get("launch", True))
        self.status = tk.StringVar(value="台本を入力してください")
        self.messages = queue.Queue()
        self.running = False
        self.last_folder = None
        self._parse_job = None

        root.title("Resolve 自動配置")
        root.geometry("980x900")
        root.minsize(820, 720)
        self._fonts()
        self._build()
        self.refresh_sections()
        root.after(100, self._drain)

    def _fonts(self):
        import tkinter.font as tkfont
        families = set(tkfont.families())
        family = next((f for f in ("Meiryo UI", "Yu Gothic UI", "Noto Sans CJK JP") if f in families), None)
        if family:
            for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkHeadingFont"):
                tkfont.nametofont(name).configure(family=family, size=10)
        ttk.Style().configure("Start.TButton", font=(family or "TkDefaultFont", 13, "bold"), padding=(24, 8))
        ttk.Style().configure("Step.TLabel", font=(family or "TkDefaultFont", 11, "bold"))

    # --- 画面 -----------------------------------------------------------

    def _build(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        # 1. 保存先
        step1 = ttk.LabelFrame(outer, text=" ① 動画の名前と保存先 ", padding=8)
        step1.grid(row=0, column=0, sticky="ew")
        step1.columnconfigure(1, weight=1)
        ttk.Label(step1, text="動画の名前").grid(row=0, column=0, sticky="w")
        ttk.Entry(step1, textvariable=self.name).grid(row=0, column=1, columnspan=2, sticky="ew", padx=6)
        ttk.Label(step1, text="保存先フォルダ").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(step1, textvariable=self.base_dir).grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
        ttk.Button(step1, text="選ぶ…", command=self.choose_base).grid(row=1, column=2, pady=(6, 0))
        ttk.Label(step1, text="保存先フォルダの中に「動画の名前」のフォルダを作り、素材をコピーします",
                  foreground="#666").grid(row=2, column=1, columnspan=2, sticky="w", padx=6)

        # 2. 台本
        step2 = ttk.LabelFrame(outer, text=" ② 台本 ", padding=8)
        step2.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        step2.columnconfigure(0, weight=1)
        step2.rowconfigure(1, weight=1)
        bar = ttk.Frame(step2)
        bar.grid(row=0, column=0, sticky="ew")
        ttk.Button(bar, text="ファイルから読み込む…", command=self.load_script).pack(side="left")
        ttk.Button(bar, text="書き方の例を入れる", command=self.insert_example).pack(side="left", padx=6)
        ttk.Button(bar, text="書き方", command=lambda: messagebox.showinfo("台本の書き方", HELP)).pack(side="left")
        self.script_status = ttk.Label(bar, text="", foreground="#666")
        self.script_status.pack(side="right")
        self.script = tk.Text(step2, height=6, wrap="word", undo=True)
        self.script.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        sb = ttk.Scrollbar(step2, command=self.script.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=(6, 0))
        self.script.configure(yscrollcommand=sb.set)
        self.script.insert("1.0", self.settings.get("script", ""))
        self.script.edit_modified(False)
        self.script.bind("<<Modified>>", self._script_changed)

        # 3. 音声
        step3 = ttk.LabelFrame(outer, text=" ③ ナレーションと BGM ", padding=8)
        step3.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        step3.columnconfigure(1, weight=1)
        ttk.Label(step3, text="ナレーション").grid(row=0, column=0, sticky="w")
        ttk.Entry(step3, textvariable=self.narration, state="readonly").grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(step3, text="選ぶ…", command=lambda: self.choose_audio(self.narration)).grid(row=0, column=2)
        ttk.Label(step3, text="BGM（なくてもよい）").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(step3, textvariable=self.bgm, state="readonly").grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
        btns = ttk.Frame(step3)
        btns.grid(row=1, column=2, pady=(6, 0))
        ttk.Button(btns, text="選ぶ…", command=lambda: self.choose_audio(self.bgm)).pack(side="left")
        ttk.Button(btns, text="外す", command=lambda: self.bgm.set("")).pack(side="left", padx=(4, 0))

        # 4. 素材
        step4 = ttk.LabelFrame(outer, text=" ④ シーンごとの素材（動画・画像） ", padding=8)
        step4.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        step4.columnconfigure(0, weight=1)
        step4.rowconfigure(1, weight=1)
        bar = ttk.Frame(step4)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Button(bar, text="まとめて追加…", command=self.add_many).pack(side="left")
        ttk.Button(bar, text="選んだシーンの素材を選ぶ…", command=self.choose_for_selected).pack(side="left", padx=6)
        ttk.Button(bar, text="選んだシーンから外す", command=self.clear_selected).pack(side="left")
        ttk.Label(bar, text="行をダブルクリックでも選べます", foreground="#666").pack(side="right")
        self.table = ttk.Treeview(step4, columns=("scene", "text", "file"), show="headings", height=8)
        for col, title, width in (("scene", "シーン", 80), ("text", "ナレーション（冒頭）", 360), ("file", "素材ファイル", 420)):
            self.table.heading(col, text=title)
            self.table.column(col, width=width, stretch=col != "scene")
        self.table.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        sb = ttk.Scrollbar(step4, command=self.table.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=(6, 0))
        self.table.configure(yscrollcommand=sb.set)
        self.table.bind("<Double-1>", lambda e: self.choose_for_selected())
        self.table.tag_configure("missing", foreground="#c0392b")

        # 5. スタート
        step5 = ttk.LabelFrame(outer, text=" ⑤ DaVinci Resolve に並べる ", padding=8)
        step5.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        step5.columnconfigure(0, weight=1)
        step5.rowconfigure(3, weight=1)
        opts = ttk.Frame(step5)
        opts.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(opts, text="Resolve のプロジェクト名").pack(side="left")
        ttk.Entry(opts, textvariable=self.project, width=24).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text="Resolve が起動していなければ起動する", variable=self.launch).pack(side="left", padx=12)
        run = ttk.Frame(step5)
        run.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.start_btn = ttk.Button(run, text="▶ スタート", style="Start.TButton", command=self.start)
        self.start_btn.pack(side="left")
        self.open_btn = ttk.Button(run, text="フォルダを開く", command=self.open_folder, state="disabled")
        self.open_btn.pack(side="left", padx=(12, 0))
        self.report_btn = ttk.Button(run, text="レポートを開く", command=self.open_report, state="disabled")
        self.report_btn.pack(side="left", padx=6)
        self.progress = ttk.Progressbar(run, mode="indeterminate", length=160)
        self.progress.pack(side="right")
        ttk.Label(step5, textvariable=self.status, style="Step.TLabel").grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self.log = tk.Text(step5, height=4, state="disabled", background="#1e1e1e", foreground="#e6e6e6",
                           insertbackground="#e6e6e6")
        self.log.grid(row=3, column=0, sticky="nsew", pady=(4, 0))
        sb = ttk.Scrollbar(step5, command=self.log.yview)
        sb.grid(row=3, column=1, sticky="ns", pady=(4, 0))
        self.log.configure(yscrollcommand=sb.set)

        outer.rowconfigure(1, weight=2)
        outer.rowconfigure(3, weight=3)
        outer.rowconfigure(4, weight=1)

    # --- 台本とシーン一覧 -----------------------------------------------

    def script_text(self):
        return self.script.get("1.0", "end-1c")

    def _script_changed(self, _event=None):
        if not self.script.edit_modified():
            return
        self.script.edit_modified(False)
        if self._parse_job:
            self.root.after_cancel(self._parse_job)
        self._parse_job = self.root.after(400, self.refresh_sections)

    def refresh_sections(self):
        self._parse_job = None
        result = parse_script(self.script_text())
        self.sections = result.sections if not result.errors else []
        if not self.script_text().strip():
            self.script_status.configure(text="台本を入力するか、ファイルから読み込んでください", foreground="#666")
        elif result.errors:
            self.script_status.configure(text=f"台本に問題があります：{result.errors[0]}", foreground="#c0392b")
        else:
            self.script_status.configure(text=f"{len(result.scenes)} シーン / {len(self.sections)} 素材", foreground="#2e7d32")
        self._fill_table()

    def _update_status(self):
        if self.running:
            return
        missing = [s.label for s in self.sections if s.key not in self.materials]
        if not self.sections:
            self.status.set("② 台本を入力してください")
        elif not self.narration.get():
            self.status.set("③ ナレーションの音声を選んでください")
        elif missing:
            self.status.set(f"④ 素材を選んでください（残り {len(missing)} シーン：{', '.join(missing[:5])}{' …' if len(missing) > 5 else ''}）")
        else:
            self.status.set("準備ができました。「スタート」を押してください")

    def _fill_table(self):
        self.table.delete(*self.table.get_children())
        for sec in self.sections:
            path = self.materials.get(sec.key)
            text = sec.text[:30] + ("…" if len(sec.text) > 30 else "")
            self.table.insert("", "end", iid=sec.key, values=(sec.label, text, os.path.basename(path) if path else "（未選択）"),
                              tags=() if path else ("missing",))
        self._update_status()

    def load_script(self):
        path = filedialog.askopenfilename(title="台本を選ぶ", filetypes=SCRIPT_TYPES)
        if not path:
            return
        with open(path, "rb") as fp:
            data = fp.read()
        for enc in ("utf-8-sig", "cp932"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            messagebox.showerror("読み込めません", "文字コードを判別できません。UTF-8 で保存し直してください")
            return
        self.script.delete("1.0", "end")
        self.script.insert("1.0", text)
        self.refresh_sections()

    def insert_example(self):
        if self.script_text().strip() and not messagebox.askyesno("確認", "今の台本を消して、例に置き換えますか？"):
            return
        self.script.delete("1.0", "end")
        self.script.insert("1.0", EXAMPLE)
        self.refresh_sections()

    # --- ファイルの選択 -------------------------------------------------

    def choose_base(self):
        path = filedialog.askdirectory(title="保存先フォルダを選ぶ", initialdir=self.base_dir.get() or None)
        if path:
            self.base_dir.set(os.path.normpath(path))

    def choose_audio(self, var):
        path = filedialog.askopenfilename(title="音声ファイルを選ぶ", filetypes=AUDIO_TYPES)
        if path:
            var.set(os.path.normpath(path))
            self._update_status()

    def add_many(self):
        if not self.sections:
            messagebox.showinfo("台本が先です", "先に台本を入力してください（シーンの一覧ができてから素材を追加します）")
            return
        paths = filedialog.askopenfilenames(title="素材をまとめて選ぶ", filetypes=MEDIA_TYPES)
        if not paths:
            return
        keys = [s.key for s in self.sections]
        self.materials, left = auto_assign(keys, [os.path.normpath(p) for p in paths], self.materials)
        self._fill_table()
        if left:
            messagebox.showwarning("入りきりません", "シーンより素材が多いため、次のファイルは割り当てていません:\n"
                                   + "\n".join(os.path.basename(p) for p in left))

    def choose_for_selected(self):
        keys = self.table.selection()
        if not keys:
            messagebox.showinfo("シーンを選んでください", "表からシーンを選んでから押してください")
            return
        path = filedialog.askopenfilename(title=f"{keys[0]} の素材を選ぶ", filetypes=MEDIA_TYPES)
        if path:
            for key in keys:
                self.materials[key] = os.path.normpath(path)
            self._fill_table()

    def clear_selected(self):
        for key in self.table.selection():
            self.materials.pop(key, None)
        self._fill_table()

    # --- 実行 -----------------------------------------------------------

    def start(self):
        if self.running:
            return
        self.refresh_sections()
        materials = {s.key: self.materials[s.key] for s in self.sections if s.key in self.materials}
        problems = []
        if not self.name.get().strip():
            problems.append("動画の名前を入力してください")
        if not self.base_dir.get().strip() or not os.path.isdir(self.base_dir.get()):
            problems.append("保存先フォルダを選んでください")
        result = parse_script(self.script_text())
        if result.errors:
            problems.append("台本に問題があります:\n  " + "\n  ".join(result.errors))
        problems += validate(self.sections, self.narration.get(), materials, self.bgm.get() or None)
        if problems:
            messagebox.showerror("入力を確認してください", "\n".join("・" + p for p in problems))
            return

        self.settings.update(name=self.name.get(), base_dir=self.base_dir.get(), project=self.project.get(),
                             launch=self.launch.get(), script=self.script_text())
        save_settings(self.settings)
        self._set_running(True)
        self._clear_log()
        # 画面の値は、別スレッドから触らないよう、ここで読み出して渡す
        job = dict(base_dir=self.base_dir.get(), name=self.name.get(), script=self.script_text(),
                   narration=self.narration.get(), bgm=self.bgm.get() or None, materials=materials,
                   project=self.project.get().strip(), launch=self.launch.get())
        threading.Thread(target=self._work, args=(job,), daemon=True).start()

    def _work(self, job):
        try:
            self._post("status", "素材をフォルダにコピー中...")
            folder = assemble(job["base_dir"], job["name"], job["script"], job["narration"],
                              job["materials"], job["bgm"], log=lambda m: self._post("log", m))
            self._post("folder", folder)
            self._post("log", f"動画フォルダ: {folder}")
            self._post("status", "処理中（読み上げとシーンの対応をとっています。数分かかります）...")
            cmd = [sys.executable, "-u", os.path.join(ROOT, "autoedit.py"), folder]
            if job["project"]:
                cmd += ["--project", job["project"]]
            if job["launch"]:
                cmd.append("--launch-resolve")
            cmd += os.environ.get("AUTOEDIT_APP_ARGS", "").split()   # 動作確認用（例: --fake-align --no-resolve）
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    env=env, creationflags=flags)
            for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").rstrip()
                self._post("log", line)
                if "Resolve に配置中" in line:
                    self._post("status", "DaVinci Resolve に並べています...")
                elif "起動しています" in line:
                    self._post("status", "DaVinci Resolve を起動しています...")
            self._post("done", proc.wait())
        except Exception as e:  # コピーの失敗なども画面に出す
            self._post("log", f"[エラー] {e}")
            self._post("done", 1)

    def _post(self, kind, value):
        self.messages.put((kind, value))

    def _drain(self):
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == "log":
                    self._append_log(value)
                elif kind == "status":
                    self.status.set(value)
                elif kind == "folder":
                    self.last_folder = value
                elif kind == "done":
                    self._finished(value)
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    def _finished(self, code):
        self._set_running(False)
        if self.last_folder:
            self.open_btn.configure(state="normal")
            if os.path.isfile(os.path.join(self.last_folder, "output", "report.md")):
                self.report_btn.configure(state="normal")
        if code == 0:
            self.status.set("完了しました。DaVinci Resolve で新しいタイムラインを確認してください")
            messagebox.showinfo("完了", "DaVinci Resolve にタイムラインを作成しました。\n内容を確認してください。")
        else:
            self.status.set("エラーで止まりました。下の表示とレポートを確認してください")
            messagebox.showerror("エラー", "途中で止まりました。\n画面下の表示と「レポートを開く」で理由を確認してください。")

    def _set_running(self, running):
        self.running = running
        self.start_btn.configure(state="disabled" if running else "normal")
        if running:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _append_log(self, line):
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def open_folder(self):
        if self.last_folder:
            _open(self.last_folder)

    def open_report(self):
        if self.last_folder:
            _open(os.path.join(self.last_folder, "output", "report.md"))


def _open(path):
    if os.name == "nt":
        if path.lower().endswith(".md"):
            subprocess.Popen(["notepad.exe", path])   # .md には既定のアプリがないことがある
        else:
            os.startfile(path)
    else:
        subprocess.Popen(["xdg-open", path])


def main():
    hide_console()
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
