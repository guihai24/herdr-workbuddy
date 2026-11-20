# herdr-workbuddy

把 [WorkBuddy](https://www.workbuddy.cn) 接进 [Herdr](https://herdr.dev) 的「Start an agent」菜单。

装完打开 Herdr 的新建菜单，就能像点 Claude Code / Codex 那样一点开一个 WorkBuddy 标签页：

```
  Terminal                    ⌘T
  Start an agent
  ●  Claude Code               1
  ●  Codex                     2
  ●  Gemini                    3
  ●  Hermes                    4
  ●  WorkBuddy                 5     ← 这个
```

## 先讲清楚一件事

**Herdr 里跑的是 `codebuddy` 命令，不是 WorkBuddy 桌面版。**

WorkBuddy 桌面版自带了一份 CLI，但它是**残缺的**——只有给 `--serve` 用的 Web UI 包，
没有交互式终端界面。实测：

| 尝试 | 结果 |
|---|---|
| `node dist/codebuddy-lite-wb.mjs`（真 pty 里） | 静默 exit 0，只吐一个改窗口标题的控制序列 |
| `node bin/codebuddy` | `Cannot find module '../dist/codebuddy'` |
| `node dist/codebuddy-lite-wb.mjs --serve` | 能起，但那是浏览器 Web UI，塞进终端面板没有交互价值 |

npm 上也没有 WorkBuddy 包（`workbuddy` / `@genie/agent-cli` 这些都是 404）。

所以需要另外装[CodeBuddy Code](https://copilot.tencent.com/cli)——完整的终端版：

```sh
npm install -g @tencent-ai/codebuddy-code
```

这也是 WorkBuddy 桌面版内部实际调用的同一个引擎（桌面版自己 spawn 的就是
`cli/bin/codebuddy --serve`）。所以能力对得上，只是它俩配置目录是独立的两套：

| | 配置目录 | 凭据 |
|---|---|---|
| `codebuddy`（本仓库接的） | `~/.codebuddy/` | CLI 自己的登录态 |
| WorkBuddy 桌面版 | `~/.workbuddy/` | Electron session + `~/.workbuddy/keyblob` |

**两套不共享。** 试过把 `CODEBUDDY_CONFIG_DIR` 指到 `~/.workbuddy`，CLI 依然报
`Authentication required`——桌面版的登录态 CLI 读不到。所以第一次用要在 CLI 里自己登录一次。

如果你想要的是「和桌面版完全同一个会话环境」，这个方案做不到，得等腾讯出完整的 CLI 发行版。

## 安装

需要 Herdr（0.1.x）、Python 3.9+，以及先装好 CodeBuddy Code（见上）。

```sh
git clone https://github.com/guihai24/herdr-workbuddy
cd herdr-workbuddy
python3 tools/install.py
```

安装器只做两件事，都落在 `~/.config/herdr-app/`（可用 `HERDR_APP_HOME` 覆盖）：

1. 放一份图标到 `icons/workbuddy.svg`
2. 把 `workbuddy` 条目**合并**进 `programs.json`——你已有的条目原样保留

Herdr 对 `programs.json` 是热加载的，存盘即生效，不用重启。
点标签栏右侧的 `+` 号就能看到新条目。

想看它要改什么而不真正落盘：

```sh
python3 tools/install.py --dry-run
```

### 第一次启动要登录

点菜单里的 WorkBuddy 后：

1. 问 `Do you trust the files in this folder?` → 选 `1` 回车
2. 问登录方式 → 选 **Log in via Chinese Site**（WorkBuddy 是 `www.workbuddy.cn` 国内站）

登录一次之后凭据存在 `~/.codebuddy/`，以后直接进。

## 排查

菜单里没出现？先跑：

```sh
python3 tools/doctor.py
```

它检查 Herdr 目录在不在、`programs.json` 是否合法、条目和图标齐不齐、`codebuddy` 在不在 PATH、有没有配置痕迹。只读，不改文件。

常见情况：

- **`codebuddy` 不在 PATH** — 没装，或装完没重开终端
- **`programs.json 不是合法 JSON`** — 这个文件一坏，Herdr 会整份忽略（错误在 `herdr-app status` 的 `errors` 里能看到），修好再跑
- **菜单里有了但点不开** — 看 `herdr-app status`，或直接在终端跑 `codebuddy` 看它报什么

## 卸载

```sh
python3 tools/uninstall.py
```

只删安装器放进去的东西（`programs.json` 里的 `workbuddy` 条目 + `icons/workbuddy.svg`）。
你的其它条目保留；删空了这个文件也会一并删掉。登录态 `~/.codebuddy/` 不动。

## 关于同时接 CodeBuddy 和 WorkBuddy

不建议。本仓库的条目 `run` 是 `["codebuddy"]`，靠 `match: ["codebuddy", "cbc"]`
把跑起来的进程认成 WorkBuddy。两个条目指向同一个命令、抢同一组进程名，
最终显示哪个图标取决于 Herdr 内部匹配顺序，不是你能稳定控制的。

真要让两者并存，得给它们跑不同的命令（比如包一层 wrapper），这超出本仓库范围。

## 配置长什么样

```json
{
  "programs": {
    "workbuddy": {
      "name": "WorkBuddy",
      "icon": "icons/workbuddy.svg",
      "tint": false,
      "tile": "#0EC7A8",
      "color": "#ffffff",
      "match": ["codebuddy", "cbc"],
      "run": ["codebuddy"]
    }
  }
}
```

- `run` — 点菜单时启动的命令
- `match` — 让跑起来的进程被认成 WorkBuddy，否则显示成通用 agent
- `icon` — 相对 `~/.config/herdr-app/` 的路径；`tint: false` 表示全彩图标（单色 glyph 要设 `true`）

字段的完整说明见 Herdr 自带的 `~/.config/herdr-app/AGENTS.md` 里 *Programs: programs.json* 一节。

## 为什么不用 `shared.json`

`shared.json` 里的 `new-menu.agents` 是 Herdr 的内置表，会被应用覆盖。自定义 agent
要写进 `programs.json`——它是在内置表之上做增补的那一层。

## 许可

MIT。图标提取自 WorkBuddy 桌面版，版权归腾讯所有，这里仅用于标识该产品。
