#!/usr/bin/env python3
"""撤销安装：从 programs.json 删掉条目，删掉图标。

只删安装器自己放进去的东西。programs.json 里如果你还有别的条目，文件保留；
删完就空了则把文件也删掉（这样 Herdr 回到内置表，package.json 也不会留个空壳）。
"""

import argparse
import json
import os
import sys
from pathlib import Path

KEY = "workbuddy"
ICON = "icons/workbuddy.svg"


def herdr_home() -> Path:
    env = os.environ.get("HERDR_APP_HOME", "").strip()
    return Path(env).expanduser() if env else Path.home() / ".config" / "herdr-app"


def main() -> int:
    ap = argparse.ArgumentParser(description="撤销 WorkBuddy 的 Herdr 接入")
    ap.add_argument("--key", default=KEY, help=f"要删的条目名（默认 {KEY}）")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不落盘")
    args = ap.parse_args()

    home = herdr_home()
    programs_path = home / "programs.json"
    icon_path = home / ICON

    if not programs_path.exists():
        print(f"programs.json 不存在，无需清理：{programs_path}")
    else:
        try:
            data = json.loads(programs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"✗ programs.json 解析失败（第 {e.lineno} 行），先手动修好再来。")

        programs = data.get("programs") or {}
        if args.key not in programs:
            print(f"programs.json 里没有 {args.key} 条目，跳过。")
        else:
            removed = programs.pop(args.key)
            print(f"将删除条目 {args.key}（name={removed.get('name')!r}）")
            if programs:
                programs_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(f"  其余 {len(programs)} 个条目保留：{', '.join(programs)}")
            else:
                print("  删完没有别的条目了，连 programs.json 一起删掉。")
            if not args.dry_run:
                if not programs:
                    programs_path.unlink()

    if icon_path.exists():
        print(f"将删除图标：{icon_path}")
        if not args.dry_run:
            icon_path.unlink()
    else:
        print(f"图标本来就不在：{icon_path}")

    if args.dry_run:
        print("\n--dry-run：没有落盘。")
    else:
        print("✓ 完成。Herdr 会热加载配置，菜单里那一项随即消失。")
        print("  登录态（~/.codebuddy/）没有动，要清自己删。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
