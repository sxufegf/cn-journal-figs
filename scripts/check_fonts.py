#!/usr/bin/env python
"""
check_fonts.py — 中英混排字体自检（配合 references/font_spec.md 使用）

检查三件事：
  1. Times New Roman / SimSun 是否已安装、matplotlib 实际命中哪个字体文件；
  2. 指定字符串里有哪些字符在字体中缺字形（缺字 = 出图变方块）；
  3. 字符串是否同时含汉字与 `$...$`（mathtext 会吞掉汉字，见 font_spec.md 坑 1）。

用法
----
    python scripts/check_fonts.py                        # 默认字体 + 符号覆盖体检
    python scripts/check_fonts.py --text "通量 1.2×10⁻³ W·m⁻²"
    python scripts/check_fonts.py --text "MK 检验 $p<0.01$"   # 会报 BLOCK 级警告
    python scripts/check_fonts.py --font SimSun --text "趋势系数"

退出码：0 = 全部通过；1 = 有 FAIL/BLOCK 项。
"""

from __future__ import annotations

import argparse
import re
import sys

FONT_STACK = ["Times New Roman", "SimSun"]
DEFAULT_SAMPLE = "降水距平 Precipitation anomaly (mm) 1951–2020，趋势 -0.013·a⁻¹，α=0.05，R²=0.31，45°，10⁻³ W·m⁻²"

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")


def _resolved(family: str):
    from matplotlib import font_manager as fm

    try:
        path = fm.findfont(fm.FontProperties(family=family), fallback_to_default=False)
        return path
    except Exception:
        return None


def _cmap(path: str):
    from fontTools.ttLib import TTCollection, TTFont

    try:
        return TTFont(path).getBestCmap()
    except Exception:                      # .ttc 字体集合（如 SimSun.ttc）
        return TTCollection(path).fonts[0].getBestCmap()


def check_installed() -> list[str]:
    from matplotlib import font_manager as fm

    installed = {f.name for f in fm.fontManager.ttflist}
    problems = []
    print("=" * 62)
    print("1) 字体安装与命中")
    for fam in FONT_STACK:
        path = _resolved(fam)
        if fam not in installed or path is None:
            print(f"  [FAIL] {fam:18s} 未安装或无法解析")
            problems.append(f"{fam} 缺失")
        else:
            ok = "PASS"
            print(f"  [{ok}] {fam:18s} → {path}")
    if "SimSun" not in installed:
        print("         提示：Windows 字体在 C:\\Windows\\Fonts\\simsun.ttc；")
        print("         安装后删除 ~/.matplotlib/fontlist-*.json 重建缓存。")
    print(f"  字体栈顺序 = {FONT_STACK}（TNR 必须在前，否则英文数字会被宋体命中）")
    return problems


def check_glyphs(text: str, font: str | None = None) -> list[str]:
    """按字体栈语义检查：一个字符只要有任一字体提供字形即视为通过。"""
    print("=" * 62)
    fonts = [font] if font else FONT_STACK
    print(f"2) 字形覆盖（字体栈 {' → '.join(fonts)}）")

    available = [(f, _resolved(f)) for f in fonts]
    available = [(f, p) for f, p in available if p]
    if not available:
        print("  [FAIL] 字体栈中无一可用")
        return ["字体不可用"]
    try:
        cmaps = [(f, _cmap(p)) for f, p in available]
    except ImportError:
        print("  [WARN] 未安装 fontTools，无法逐字检查（pip install fonttools）")
        return []

    chars = {c for c in text if not c.isspace()}
    provider: dict[str, str] = {}
    missing = []
    for c in sorted(chars):
        for f, cm in cmaps:
            if ord(c) in cm:
                provider[c] = f
                break
        else:
            missing.append(c)

    if missing:
        print(f"  [FAIL] 字体栈内均无字形（{len(missing)} 个）: "
              + " ".join(f"{c}(U+{ord(c):04X})" for c in missing))
        problems = ["字体栈缺字"]
    else:
        print(f"  [PASS] {len(chars)} 个字符全部可渲染")
        problems = []

    # 展示回退分工：谁提供了汉字、谁提供了符号
    for f, _ in cmaps:
        got = [c for c, src in provider.items() if src == f]
        cjk_n = sum(1 for c in got if CJK.match(c))
        other_n = len(got) - cjk_n
        print(f"         {f:18s} 提供 {len(got):3d} 字符（汉字 {cjk_n}、其他 {other_n}）")
    return problems


def check_mathtext_risk(text: str) -> list[str]:
    print("=" * 62)
    print("4) mathtext 吞字风险")
    if "$" in text and CJK.search(text):
        print("  [BLOCK] 字符串同时含汉字与 `$...$`：整串会走 mathtext 管线，")
        print("          非数学段用 STIX 渲染，汉字将变成方块。")
        print("          处理：去掉 `$`，数学符号改 Unicode（mm·a⁻¹、R²、10⁻³、α、45°）；")
        print("                确需公式时把公式拆到独立的 ax.text()。")
        return ["mathtext 吞中文"]
    print("  [PASS] 无汉字与 `$...$` 混排")
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="中英混排字体自检")
    ap.add_argument("--text", default=DEFAULT_SAMPLE, help="待检查的标注字符串")
    ap.add_argument("--font", default=None,
                    help="只检查指定字体（默认检查整个字体栈，符合逐字形回退语义）")
    args = ap.parse_args()

    problems = []
    problems += check_installed()
    problems += check_glyphs(args.text, args.font)
    problems += check_mathtext_risk(args.text)

    print("=" * 62)
    if problems:
        print("结果：FAIL — " + "；".join(problems))
        return 1
    print("结果：全部通过 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
