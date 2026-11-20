#!/usr/bin/env python3
"""检查接入状态：Herdr 在不在、codebuddy 能不能跑、programs.json 写得对不对。

只读，不改任何文件。排查「菜单里没出现 WorkBuddy」时先跑这个。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

KEY = "workbuddy"


def herdr_home() -> Path:
    env = os.environ.get("HERDR_APP_HOME", "").strip()
    return Path(env).expanduser() if env else Path.home() / ".config" / "herdr-app"


def main() -> int:
    argparse.ArgumentParser(
        description="检查 WorkBuddy 的 Herdr 接入状态（只读，不改文件）"
    ).parse_args()

    problems = []
    home = herdr_home()

    print(f"Herdr 配置目录：{home}")
    if not home.is_dir():
        print("  ✗ 不存在。先装 Herdr 并跑起来一次。")
        return 1
    print("  ✓ 存在")

    programs_path = home / "programs.json"
    if not programs_path.exists():
        problems.append("programs.json 不存在 —— 还没跑过安装器？")
        print(f"\nprograms.json：✗ 不存在")
    else:
        try:
            data = json.loads(programs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"programs.json 不是合法 JSON（第 {e.lineno} 行）：{e.msg}")
            print(f"\nprograms.json：✗ JSON 解析失败")
            data = None
        else:
            print(f"\nprograms.json：✓ 合法 JSON")
        if isinstance(data, dict):
            entry = (data.get("programs") or {}).get(KEY)
            if entry is None:
                problems.append(f"programs.json 里没有 {KEY} 条目")
                print(f"  ✗ 没有 {KEY} 条目")
            else:
                print(f"  ✓ 有 {KEY} 条目：name={entry.get('name')!r} run={entry.get('run')}")
                icon = entry.get("icon")
                if icon:
                    icon_path = home / icon
                    if icon_path.exists():
                        print(f"  ✓ 图标在位：{icon_path}")
                    else:
                        problems.append(f"图标缺失：{icon_path}")
                        print(f"  ✗ 图标缺失：{icon_path}")

    print("\ncodebuddy：", end="")
    path = shutil.which("codebuddy")
    if not path:
        print("✗ 不在 PATH 里")
        problems.append("codebuddy 不在 PATH —— npm install -g @tencent-ai/codebuddy-code")
    else:
        print(f"✓ {path}")
        try:
            out = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=30
            )
            ver = (out.stdout or out.stderr).strip().splitlines()
            print(f"  版本：{ver[0] if ver else '未知'}")
        except (subprocess.TimeoutExpired, OSError) as e:
            problems.append(f"codebuddy --version 失败：{e}")

    print("\n登录态：", end="")
    cred = Path.home() / ".codebuddy"
    if (cred / "settings.json").exists() or (cred / "projects").is_dir():
        print(f"✓ 有配置痕迹（{cred}）")
        print("  注意：这里只能说明配置目录存在，是否已登录要看 herdr 里第一次跑的表现。")
    else:
        print(f"✗ 没有 {cred}")
        print("  第一次在 herdr 里点 WorkBuddy 时按提示登录即可。")

    print()
    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("✓ 全部检查通过。点 Herdr 标签栏右侧的 + 号，菜单里应该能看到 WorkBuddy。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
