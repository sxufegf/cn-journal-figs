# 字体配置规范：中文宋体 + Times New Roman 同时正常渲染

> 本节规范解决中文期刊制图最基础也最容易翻车的一件事：**图里汉字走宋体、数字英文走
> Times New Roman，两者在同一幅图里同时正常显示**。
> 配套：`assets/journal_init.py`（初始化单元）、`scripts/check_fonts.py`（字体自检）、
> `examples/font_mixing_demo.py`（混排示例）。

---

## 1 核心机制：逐字形回退（一行配置解决混排）

matplotlib ≥ 3.6 支持**按字形逐个回退**（per-glyph font fallback）：字符串中每个字符
依次在字体栈里找到第一个含有该字形的字体。因此把 **Times New Roman 放第一位、
SimSun（宋体）放第二位**，即可自动实现"数字/英文/单位走 TNR，汉字落宋体"，
全程无需手工切换：

```python
plt.rcParams["font.family"] = ["Times New Roman", "SimSun"]
```

**顺序不可反**：若 SimSun 在前，宋体自身也含拉丁字母与数字（半角），英文数字会被
宋体先命中，出图风格立刻变成"宋体英文"，与期刊要求不符。

前提是本机确实装了这两种字体（Windows 自带 `C:\Windows\Fonts\times.ttf`、
`simsun.ttc`）。用 `scripts/check_fonts.py` 一键确认：

```bash
python scripts/check_fonts.py
# [PASS] Times New Roman → times.ttf
# [PASS] SimSun          → simsun.ttc
```

---

## 2 必设参数（缺一不可）

```python
plt.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],   # 顺序不能反
    "font.serif":  ["Times New Roman", "SimSun", "STSong", "NSimSun"],
    "mathtext.fontset": "stix",      # 数学字体与 TNR 同风格
    "axes.unicode_minus": False,     # ★ 宋体缺 U+2212，不设则负号变方块
    "pdf.fonttype": 42,              # ★ TrueType 嵌入，Type3 会被编辑部退回
    "ps.fonttype": 42,
    "svg.fonttype": "none",          # SVG 保留可编辑文本
})
```

| 参数 | 缺失后果 |
|---|---|
| `font.family` 字体栈 | 中文或英文落入 DejaVu Sans，风格不统一 |
| `axes.unicode_minus=False` | 负数刻度显示为方块 □ |
| `pdf.fonttype=42` | PDF 内为 Type3 伪字体，编辑无法重排、印刷模糊 |
| `mathtext.fontset="stix"` | 公式字体与正文 TNR 割裂 |

---

## 3 字号与字符类型对应关系

| 字符类型 | 字体 | 字号 |
|---|---|---|
| 汉字 | 宋体 SimSun | 标目 9 pt / 刻度图例 8 pt |
| 数字、英文、单位符号 | Times New Roman | 同上 |
| 数学符号、公式变量 | TNR 斜体（mathtext STIX） | 同上 |
| **禁用** | 黑体、微软雅黑、楷体做正文标注；Arial/DejaVu 混入 | — |

字号只在 rcParams 里设一次，**不逐图手写 `fontsize=`**；按印刷尺寸出图
（半栏 8 cm / 通栏 15 cm），印刷后即为设定值。

---

## 4 标注写法约定

| 内容 | 写法 | 示例 |
|---|---|---|
| 标目 | `中文 (English) (单位)`，单位半角括号 | `降水距平 Precipitation anomaly (mm)` |
| 上下标 | **Unicode 字符**，不用 mathtext | `mm·a⁻¹`、`R²`、`10⁻³`、`W·m⁻²`、`45°` |
| 希腊字母 | Unicode（TNR 已覆盖） | `α=0.05`、`θ`、`±` |
| 负值 | 连字符自动渲染 | `-0.15` |
| 百分号 | 半角 | `+18.6%` |

已实测 Times New Roman 字符覆盖：`⁻ ¹ ² ³ ° · × α θ ± % ℃` 全部有字形；
中文标点（，；（））由宋体兜底。不确定时用 `scripts/check_fonts.py --text "待检字符串"`
逐字检查。

---

## 5 五个必踩的坑

1. **mathtext 吞中文（最隐蔽）**
   同一个字符串里同时出现汉字与 `$...$`，例如 `"MK 检验 $p<0.01$"`，matplotlib 会把
   整串送进 mathtext 管线，非数学段也用 mathtext 的默认字体（STIX）渲染，
   而 STIX 无汉字字形 → **汉字全部变方块**，并刷一屏
   `Font 'default' does not have a glyph for ...` 警告。
   **规则：中文标注串里禁止出现 `$`**。数学符号改用第 4 节的 Unicode 上下标；
   确需公式时，把公式拆成独立的 `ax.text()` 对象（该对象内不出现汉字）。

   ```python
   # ✗ 错误：汉字被 mathtext 吞掉
   ax.set_ylabel("趋势系数 (mm·$a^{-1}$)")
   ax.text(0.1, 0.9, "MK 检验 $p<0.01$，$R^2=0.31$")
   # ✓ 正确：Unicode 上标，整串走普通文本管线
   ax.set_ylabel("趋势系数 (mm·a⁻¹)")
   ax.text(0.1, 0.9, "MK 检验 p<0.01，R²=0.31")
   ```

2. **`sns.set_theme()` 覆盖字体**：set_theme 会重置字体相关 rcParams，
   **必须先 set_theme、后设字体**，顺序颠倒则前功尽弃。
3. **字体缓存陈旧**：装了字体但 `findfont` 仍报警 → 删除
   `~/.matplotlib/fontlist-*.json`（Windows：`C:\Users\<用户>\.matplotlib\`）后重跑。
4. **`bbox_inches="tight"` 改变物理尺寸**：15 cm 设定裁边后可能变 13–14 cm。
   期刊严格要求尺寸时改用 `fig.subplots_adjust(...)` 控制边距，不依赖裁边。
5. **第三方库重置样式**：shap 等库会重设字号与标题 → 出图后显式重设
   `ax.set_xlabel(..., fontsize=9)` 并清空其自带标题。

---

## 6 复用方式

```python
# 1) notebook / 脚本首个单元整段粘贴 assets/journal_init.py
# 2) 之后所有图：
fig, ax = plt.subplots(figsize=(HALF_W, 2.6))
ax.plot(year, anom)
ax.set_xlabel("年份 (Year)")
ax.set_ylabel("降水距平 Precipitation anomaly (mm)")
panel(ax, "(a)")
savefig(fig, "fig01_anomaly.png")     # PDF(矢量投稿) + PNG(600 dpi) 双格式
```

`assets/journal_init.py` 已包含上表全部 rcParams 与 `savefig` / `panel` /
`center_bottom_left` / `save_table` 四个辅助函数。

---

## 7 出图后自检

```bash
# 字体与字形自检（本规范专用）
python scripts/check_fonts.py
python scripts/check_fonts.py --text "通量 1.2×10⁻³ W·m⁻²"

# 图件整体自检（字体嵌入 / Type3 / 尺寸 / dpi / 灰度可辨）
python scripts/check_figure.py examples/font_mixing_demo.pdf examples/font_mixing_demo.png
```

`examples/font_mixing_demo.py` 的实际自检输出：

```
■ font_mixing_demo.pdf
  [PASS] 字体清单: TimesNewRomanPSMT, SimSun
  [PASS] 无 Type3 伪字体
  [PASS] 字体已嵌入
■ font_mixing_demo.png
  [PASS] dpi≈600
  [PASS] 2 个彩色类别灰度两两可分
```

---

## 8 故障对照

| 症状 | 根因 | 处理 |
|---|---|---|
| 中文变方块 □ | 字体栈缺 SimSun；或中文串里混入 `$...$` | 补字体 / 去 `$` 改 Unicode |
| 负号变方块 | 未设 `axes.unicode_minus=False` | 加参数 |
| 英文呈宋体风格 | 字体栈顺序反了 | TNR 放第一位 |
| 英文呈 Arial/DejaVu 风格 | 字体栈缺 TNR | 补 TNR 并清字体缓存 |
| PDF 被编辑部退回 | Type3 伪字体 | `pdf.fonttype=42` |
| 满屏 `Font 'default' does not have a glyph` | mathtext 遇到汉字 | 按坑 1 处理 |
| 出图进程直接崩溃、无 traceback（`0xC06D007E`/`0xC06D007F`） | conda 环境缺 `libiomp5md.dll`（MKL 的 Intel OpenMP） | 补该 DLL，或改 OpenBLAS 后端 |
