---
name: cn-journal-figs
description: 中文核心期刊制图规范技能。用 matplotlib 为《地理学报》《地理研究》等中文核心期刊（及课程/论文）出图时必须使用本技能：初始化期刊级 rcParams（中文宋体 + Times New Roman、刻度朝内、图内无标题）、组合图版式（4 幅 2×2、3 幅 2×2 第二行居中）、图注四段式、PDF+PNG 双格式导出、Type3 字体检查、地图合规红线。触发词：画图、出图、绘图、可视化、期刊图、论文图、组合图、面板、图注、colorbar、matplotlib 制图、制图规范、宋体、审图号。
agent_created: true
---

# 中文核心期刊制图规范（cn-journal-figs）

将《时空大数据与数据挖掘》课程沉淀的《中文核心期刊制图规范》固化为出图工作流。
目标：任何一次 matplotlib 出图都直接达到《地理学报》《地理研究》级投稿标准，不走"先出图再返工"的弯路。

## 何时使用

- 用 matplotlib/seaborn 为论文、课程、报告出**任何图**（含修改已有图）；
- 组合图/多面板图的排布与对齐；
- 中文宋体 + Times New Roman 混排、PDF 字体嵌入问题；
- 地图类图件（投影、比例尺、审图号、南海诸岛合规）；
- 图件投稿前自检。

## 资源清单

| 资源 | 用途 |
|---|---|
| `assets/journal_init.py` | 初始化单元：rcParams 全套 + `savefig/panel/center_bottom_left/save_table` 辅助函数，整段复制到 notebook 首个代码单元 |
| `references/layout_recipes.md` | 组合图版式与常用图元代码配方（2×2、三图居中、GridSpec、colorbar、双 y 轴、三重编码、显著性 bracket、图注模板、地图合规） |
| `references/figure_spec.md` | 制图规范全文（12 节 + 检查清单），细节争议时查这一份 |
| `scripts/check_figure.py` | 图件自检脚本：PDF 字体嵌入/Type3、PNG 物理尺寸与 dpi、灰度可辨性 |

## 工作流

### 1. 初始化

从 `assets/journal_init.py` 复制整段初始化代码到 notebook 首个代码单元（或 .py 的 import 之后），按项目实际情况改 `find_root()` 的目录判定与 `FIG/TAB` 路径。**顺序铁律**：`sns.set_theme()` 在前、`font.family` 在后（set_theme 会覆盖字体设置）。中文出图一律用 conda 环境 `geospatial`，且必须先激活（否则 MKL DLL 静默崩溃）。

### 2. 出图（四条硬规则贯穿所有图）

1. **图内无标题**：禁用 `set_title`/`suptitle`，图题写在图下方 markdown 图注（四段式：编号总述 / 面板释义 / 符号约定 / 结论解读，见 `layout_recipes.md` 第 11 节模板）；
2. **按印刷尺寸出图**：半栏 8 cm（`HALF_W`）、通栏 15 cm（`FULL_W`），字号 9/8 pt 全局 rcParams，不逐图手写 `fontsize=`；
3. **面板编号**：`panel(ax, "(a)")`，统一在面板上方外侧左上角 `(0.03, 1.04)`；
4. **双格式落盘**：`savefig(fig, "...png")` 同时出矢量 PDF + 600 dpi PNG 并行内显示。

### 3. 组合图版式（用户重点约定）

| 子图数 | 排布 |
|---|---|
| 2 | 1 行 2 列 |
| **3** | **2×2，第二行 1 幅居中**：先 `fig.tight_layout()` 再 `center_bottom_left(fig, axes)`——顺序不能反，tight_layout 会撤销 set_position |
| **4** | **2×2** |
| 5–6 | 2 行 3 列 |
| ≥7 | 优先拆成两张图 |

各面板**等大**、坐标对齐、Z 形编号；量纲相同用 `sharex="col"`/`sharey="row"`；多面板共用 colorbar 时 `vmin/vmax` 显式取全局范围。代码配方见 `layout_recipes.md` 第 1–8 节。

### 4. 出图后自检

用 Python（含 Pillow 的环境，如 geospatial）运行：

```bash
python <skill目录>/scripts/check_figure.py figures/fig.pdf figures/fig.png
```

检查 PDF 字体嵌入与 Type3、PNG 物理宽度（8/15 cm）与 dpi、彩色类别灰度可辨性。FAIL 项必须修复后重出。

### 5. 特殊场景路由

- **地图类图件**：先读 `figure_spec.md` 第 9 节——底图必须来自标准地图服务系统（`bzdt.ch.mnr.gov.cn`）、中国全图完整表示南海诸岛与台湾岛、标注审图号、图注写明投影；这是法律合规红线，不是风格偏好；
- **表格**：三线表、表题在上、空缺用"—"，见 `figure_spec.md` 第 8 节；
- **色彩选择**：禁 `jet`；分类用定性色板、正负偏离用发散色板、黑白打印须灰度可分，见 `figure_spec.md` 第 6 节；
- **退修意见对照**：收到图件退修意见时，直接查 `figure_spec.md` 第 11 节对照表定位根因；
- **投稿前**：逐项过 `figure_spec.md` 第 12 节检查清单。

## 关键陷阱速记

- `sns.set_theme()` 覆盖字体 → 字体设置必须在其后；
- `pdf.fonttype=42` 不设 → Type3 伪字体，编辑部退回；
- `axes.unicode_minus=False` 不设 → 宋体缺 U+2212，负号显示为方块；
- tight_layout 后调用 set_position 无效 → 先 tight 后平移；
- `savefig(bbox_inches="tight")` 会改变物理尺寸（15 cm 可能变 14.8 cm），期刊严格要求尺寸时用 `subplots_adjust`；
- shap 等第三方库会重置字号/标题 → 出图后显式重设 `ax.set_xlabel(..., fontsize=9)`、清空自带标题。
