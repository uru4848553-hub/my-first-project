"""スキル「人生の断面図」（.claude/skills/jinsei-danmen）を、claude.ai にアップロードする zip にまとめる。

python tools/make_skill_zip.py  →  channel_produce/jinsei-danmen_skill.zip
スキルを更新したら毎回これを実行して、zip もコミットする。
"""
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
OUT = ROOT / "channel_produce" / "jinsei-danmen_skill.zip"


def main():
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SKILLS / "jinsei-danmen"):
            for name in sorted(files):
                path = Path(root) / name
                z.write(path, path.relative_to(SKILLS))
    print("ok:", OUT)


if __name__ == "__main__":
    main()
