"""
font_mixing_demo.py — 中英混排字体配置示例（对应 references/font_spec.md）

产出 examples/font_mixing_demo.pdf（矢量投稿）与 .png（600 dpi 校对）。

要点：
  * 字体栈 ["Times New Roman", "SimSun"] → 数字/英文走 TNR，汉字走宋体；
  * 中文标注串里**不出现 `$...$`**，数学符号一律用 Unicode 上标（⁻¹ ² ³ ⁻³ · × ° α θ ±），
    否则 mathtext 会用 STIX 渲染非数学段，汉字变方块（font_spec.md 坑 1）；
  * 图内不设标题，面板编号置于上方外侧左上角，按通栏 15 cm 出图。

运行：python examples/font_mixing_demo.py
"""

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- 期刊级 rcParams（与 assets/journal_init.py 一致） ----------
CM = 1 / 2.54
HALF_W, FULL_W = 8 * CM, 15 * CM

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],
    "font.serif": ["Times New Roman", "SimSun", "STSong", "NSimSun"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
    "font.size": 8, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
    "lines.linewidth": 1.0, "lines.markersize": 4,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.facecolor": "white", "savefig.facecolor": "white",
})

OUT = Path(__file__).resolve().parent


def panel(ax, tag):
    ax.text(0.03, 1.04, tag, transform=ax.transAxes, ha="left", va="bottom", fontsize=8)


# ---------- 合成数据（仅用于检验字体渲染） ----------
rng = np.random.default_rng(7)
year = np.arange(1951, 2021)
anom = 0.6 * np.sin((year - 1951) / 6.0) + rng.normal(0, 0.45, year.size) + 0.010 * (year - 1951)

fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.45), gridspec_kw={"wspace": 0.32})

# (a) 汉字 + 英文 + 数字 + 负号 + Unicode 上标
ax = axes[0]
ax.axhline(0, color="0.55", lw=0.7, ls=(0, (4, 3)))
ax.plot(year, anom, "-o", mfc="white", mew=0.7, ms=3, color="#b03a2e",
        label="年降水距平 Annual anomaly")
k = np.polyfit(year, anom, 1)[0]
ax.plot(year, np.polyval(np.polyfit(year, anom, 1), year), "--", color="#1f3b57",
        lw=1.2, label=f"线性趋势 Trend ({k:+.3f} a⁻¹)")
ax.set_xlabel("年份 (Year)")
ax.set_ylabel("降水距平 Precipitation anomaly (mm)")
ax.legend(loc="lower left", handlelength=1.8, borderaxespad=0.2)
ax.text(0.03, 0.97, "MK 检验 p<0.01，R²=0.31", transform=ax.transAxes,
        ha="left", va="top", fontsize=7.5)
panel(ax, "(a)")

# (b) 希腊字母、角度、科学计数、复合单位
ax = axes[1]
bins = np.arange(1951, 2021, 10)
vals = np.array([-12.4, -8.1, 3.6, 9.8, 15.2, 22.7, 28.3])[: bins.size]
cols = ["#3a7ca5" if v < 0 else "#b03a2e" for v in vals]
ax.bar(bins + 4, vals, width=7.4, color=cols, edgecolor="k", linewidth=0.4)
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("年代 (Decade)")
ax.set_ylabel("趋势系数 Trend coef. (mm·a⁻¹)")
ax.text(0.04, 0.94, "α=0.05，θ=45°，增幅 +18.6%",
        transform=ax.transAxes, fontsize=7.5, va="top")
ax.text(0.04, 0.84, "通量 1.2×10⁻³ W·m⁻²",
        transform=ax.transAxes, fontsize=7.5, va="top")
panel(ax, "(b)")

# 用 subplots_adjust 而非 tight_layout + bbox_inches="tight"：
# 后两者会改变版本物理尺寸（15 cm 可能被裁成 13.3 cm），期刊严格限宽时不可用。
fig.subplots_adjust(left=0.082, right=0.995, bottom=0.185, top=0.915, wspace=0.42)
for path in (OUT / "font_mixing_demo.pdf", OUT / "font_mixing_demo.png"):
    fig.savefig(path, dpi=600 if path.suffix == ".png" else None,
                facecolor="white")
    print("saved →", path)
