#!/usr/bin/env python3
"""把 WorkBuddy 接入 Herdr 的「Start an agent」菜单。

做的事情只有两件，都落在 ~/.config/herdr-app/ 下（可用 HERDR_APP_HOME 覆盖）：
  1. 放一份图标到 icons/workbuddy.svg
  2. 把 workbuddy 条目合并进 programs.json（不动你已有的条目）

Herdr 对 programs.json 是热加载的，存盘即生效，不用重启。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ICON_SRC = REPO / "assets" / "workbuddy.svg"

# programs.json 里要写入的条目。run 决定点菜单时启动什么命令，
# match 让跑起来的那个进程被识别成 WorkBuddy（否则显示成通用 agent）。
ENTRY = {
    "name": "WorkBuddy",
    "icon": "icons/workbuddy.svg",
    "tint": False,
    "tile": "#0EC7A8",
    "color": "#ffffff",
    "match": ["codebuddy", "cbc"],
    "run": ["codebuddy"],
}


def herdr_home() -> Path:
    env = os.environ.get("HERDR_APP_HOME", "").strip()
    return Path(env).expanduser() if env else Path.home() / ".config" / "herdr-app"


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def detect_cli() -> tuple[bool, str]:
    """确认 codebuddy 在哪、能不能跑。返回 (ok, 说明)。"""
    path = which("codebuddy")
    if not path:
        return False, (
            "没找到 codebuddy 命令。\n"
            "  WorkBuddy 桌面版自带的 CLI 不含交互式界面（只有 --serve 的 Web UI），\n"
            "  所以要另外装完整版：\n"
            "      npm install -g @tencent-ai/codebuddy-code\n"
            "  装完重开终端，确认 `codebuddy --version` 能出版本号。"
        )

    try:
        out = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=30
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return False, f"{path} 跑不起来：{e}"

    version = (out.stdout or out.stderr).strip().splitlines()
    ver = version[0] if version else "未知版本"
    if out.returncode != 0:
        return False, f"{path} --version 返回 {out.returncode}：{ver}"
    return True, f"{path}（{ver}）"


def load_programs(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(
            f"✗ {path} 不是合法 JSON（第 {e.lineno} 行）：{e.msg}\n"
            "  先修好这个文件再跑，否则 Herdr 会把它整份忽略掉。"
        )
    if not isinstance(data, dict):
        sys.exit(f"✗ {path} 的顶层应该是一个 JSON 对象。")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="把 WorkBuddy 接入 Herdr 的新建菜单")
    ap.add_argument(
        "--key",
        default="workbuddy",
        help="programs.json 里的条目名（默认 workbuddy）。同名条目会被覆盖。",
    )
    ap.add_argument(
        "--name",
        default=None,
        help="菜单里显示的名字（默认 WorkBuddy）。想同时接 CodeBuddy 就用 --name 区分。",
    )
    ap.add_argument(
        "--force", action="store_true", help="即使没找到 codebuddy 也写配置"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="只打印将要做的改动，不落盘"
    )
    args = ap.parse_args()

    home = herdr_home()
    if not home.is_dir():
        sys.exit(f"✗ 找不到 Herdr 配置目录：{home}\n  先装 Herdr 并跑起来一次。")

    ok, note = detect_cli()
    print(("✓ " if ok else "✗ ") + "codebuddy：" + note)
    if not ok and not args.force:
        print("\n没有写入任何配置。确认要强行写入就加 --force。")
        return 1

    icon_dst = home / "icons" / ENTRY["icon"].split("/", 1)[1]
    programs_path = home / "programs.json"

    data = load_programs(programs_path)
    programs = data.get("programs")
    if programs is None:
        programs = data["programs"] = {}
    if not isinstance(programs, dict):
        sys.exit(f"✗ {programs_path} 里的 programs 应该是一个 JSON 对象。")

    entry = dict(ENTRY)
    if args.name:
        entry["name"] = args.name
    existed = args.key in programs
    programs[args.key] = entry

    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    print(f"\n将写入：{programs_path}{'（已有同名条目，将被替换）' if existed else ''}")
    print(payload)
    print(f"图标：{icon_dst}")

    if args.dry_run:
        print("\n--dry-run：没有落盘。")
        return 0 if ok else 1

    icon_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ICON_SRC, icon_dst)
    programs_path.write_text(payload, encoding="utf-8")

    print("✓ 完成。Herdr 会热加载这份配置，打开「新建」菜单就能看到它了。")
    print("\n第一次点进去要自己登录一次：")
    print("  1. 问「Do you trust the files in this folder?」→ 选 1 回车")
    print("  2. 问登录方式 → 选 Log in via Chinese Site（登录 www.workbuddy.cn 那个站）")
    print("登录态存在 ~/.codebuddy/，之后直接进。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
