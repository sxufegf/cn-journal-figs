# ============================================================
# 中文核心期刊制图 · matplotlib 初始化单元（assets/journal_init.py）
# 用法：整段复制到 notebook 首个代码单元，或在 .py 中 import 前粘贴。
# 详细规范见 references/figure_spec.md
# ============================================================
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import seaborn as sns

# ---- 路径：向上找到同时含 data/ 与 notebook/ 的目录作为项目根 ----
def find_root(start: Path = Path.cwd()) -> Path:
    for p in [start, *start.parents]:
        if (p / "data").is_dir() and (p / "notebook").is_dir():
            return p
    return start

ROOT = find_root()
FIG = ROOT / "figures"
TAB = ROOT / "tables"
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

# ---- 版心尺寸（厘米 → 英寸）----
CM = 1 / 2.54
HALF_W, FULL_W = 8 * CM, 15 * CM

# ---- 顺序不能颠倒：先 set_theme，后设字体（set_theme 会覆盖字体）----
sns.set_theme(style="ticks", context="paper")

plt.rcParams.update({
    # 字体：中文宋体，数字/英文/单位 Times New Roman（matplotlib>=3.6 逐字形回退）
    "font.family": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,          # 负号用连字符渲染，防宋体缺 U+2212 出方块
    # 字号：按印刷后实际大小，全局统一，不逐图手写 fontsize=
    "font.size": 8,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    # 坐标轴：刻度朝内、四周齐全、封闭图框
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "xtick.minor.visible": False,
    "axes.linewidth": 0.8,
    # 图例无边框；线宽点径
    "legend.frameon": False,
    "lines.linewidth": 1.0,
    "lines.markersize": 4,
    # PDF 字体以 TrueType 嵌入（避免 Type3）
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    # 白底、紧凑边距
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
})

# 在 notebook 中使用时取消下一行注释
# %matplotlib inline


def savefig(fig, filename: str, dpi: int = 600):
    """矢量 PDF（投稿）+ 600 dpi PNG（校对）双格式落盘，并 plt.show() 行内显示。"""
    stem = filename.rsplit(".", 1)[0]
    for path in (FIG / f"{stem}.pdf", FIG / filename):
        fig.savefig(path, dpi=dpi if path.suffix == ".png" else None,
                    bbox_inches="tight", facecolor="white")
    plt.show()
    print(f"  已保存 → figures/{stem}.pdf, figures/{filename}")
    return FIG / filename


def panel(ax, tag: str) -> None:
    """面板编号 (a)(b)(c)：统一置于面板上方外侧左上角，全篇同一坐标。"""
    ax.text(0.03, 1.04, tag, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8)


def center_bottom_left(fig, axes) -> None:
    """3 幅子图的 2×2 版式：第二行 1 幅水平居中，面板尺寸与第一行完全一致。

    ★ 必须在 fig.tight_layout() 之后调用——tight_layout 会撤销 set_position。
    """
    ax = axes[1, 0]
    axes[1, 1].remove()
    pos = ax.get_position()
    ax.set_position([(1 - pos.width) / 2, pos.y0, pos.width, pos.height])


def save_table(df, filename: str):
    """表格落盘：utf-8-sig 编码，Excel 双击打开不乱码。"""
    path = TAB / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  已保存 → tables/{filename}")
    return path
