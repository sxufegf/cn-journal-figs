#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_figure.py —— 中文核心期刊图件自检脚本

用法:
    python check_figure.py 图1.pdf [图2.png ...]
    python check_figure.py figures/          # 递归检查目录下所有 pdf/png

检查项:
  PDF  — 字体嵌入（/FontFile2|3）、是否含 Type3 伪字体、/BaseFont 清单
  PNG  — 从 pHYs 块读取 dpi，换算实际物理宽度（cm），核对是否为半栏 8 / 通栏 15 cm
  灰度 — 对 PNG 做主色量化，检测亮度差 <10% 的主色对（黑白打印可能不可辨）

退出码 = FAIL 项数（0 = 全部通过）。仅依赖标准库 + Pillow（无 Pillow 时跳过像素类检查）。
"""
import re
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

HALF_W, FULL_W = 8.0, 15.0          # 目标版心宽度 cm（±0.6 cm 容差）
CM_TOL = 0.6


def check_pdf(path: Path) -> list:
    """返回 [(级别, 消息)]，级别 ∈ {PASS, WARN, FAIL}。"""
    results = []
    raw = path.read_bytes()
    fonts = sorted(set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-_,#]+)", raw)))
    if fonts:
        names = ", ".join(f.decode("ascii", "replace") for f in fonts)
        results.append(("PASS", f"字体清单: {names}"))
        for f in fonts:
            name = f.decode("ascii", "replace")
            if "Arial" in name or "DejaVu" in name or "SimHei" in name:
                results.append(("WARN", f"疑似混入非规范字体 {name}（应为 SimSun + TimesNewRoman）"))
        if not any("SimSun" in n or "Song" in n for n in names.split(", ")) and \
           not any("Times" in n for n in names.split(", ")):
            results.append(("WARN", "未见 SimSun 或 TimesNewRoman，请核对字体回退设置"))
    else:
        results.append(("WARN", "PDF 中未检出 /BaseFont（可能整页位图化，检查 savefig 设置）"))
    has_t3 = b"/Subtype /Type3" in raw
    if has_t3:
        results.append(("FAIL", "含 Type3 伪字体——文字已被位图化，须设 pdf.fonttype=42 重出"))
    else:
        results.append(("PASS", "无 Type3 伪字体"))
    embedded = b"/FontFile2" in raw or b"/FontFile3" in raw
    results.append(("PASS" if embedded else "FAIL",
                    "字体已嵌入" if embedded else "未检出字体嵌入（/FontFile2|3 缺失）"))
    return results


def _png_dpi(path: Path):
    """解析 PNG pHYs 块，返回 (x_dpi, y_dpi) 或 None。"""
    with open(path, "rb") as f:
        data = f.read(1024 * 1024)          # pHYs 通常在文件头部
    i = data.find(b"pHYs")
    if i < 0 or len(data) < i + 9:
        return None
    x_ppm, y_ppm, unit = struct.unpack(">IIB", data[i + 4:i + 13])
    if unit != 1 or x_ppm == 0:             # unit=1 表示像素/米
        return None
    return x_ppm * 0.0254, y_ppm * 0.0254   # 转 dpi


def check_png(path: Path) -> list:
    results = []
    dpi = _png_dpi(path)
    if not HAS_PIL:
        results.append(("WARN", "未安装 Pillow，跳过尺寸与灰度检查"))
        return results
    with Image.open(path) as im:
        w_px, h_px = im.size
        dpi_eff = dpi[0] if dpi else 600.0
        w_cm = w_px / dpi_eff * 2.54
        if abs(w_cm - HALF_W) <= CM_TOL:
            results.append(("PASS", f"半栏图 宽 {w_cm:.1f} cm（目标 8 cm）"))
        elif abs(w_cm - FULL_W) <= CM_TOL:
            results.append(("PASS", f"通栏图 宽 {w_cm:.1f} cm（目标 15 cm）"))
        else:
            results.append(("WARN", f"图宽 {w_cm:.1f} cm 不为半栏 8 / 通栏 15 cm，核对出图 figsize"))
        if dpi and dpi[0] < 590:
            results.append(("FAIL", f"dpi={dpi[0]:.0f} 低于 600，重出时 savefig(dpi=600)"))
        else:
            results.append(("PASS", f"dpi≈{dpi_eff:.0f}"))
        # 灰度可辨性：只比较"彩色主色对"（类别色）。
        # 近白背景 / 灰阶文字轴线 / 抗锯齿边缘色（低饱和度）不参与比较，
        # 否则白底 vs 浅灰抗锯齿会大量误报。
        small = im.convert("RGB").resize((128, 128))
        q = small.quantize(colors=12, method=Image.MEDIANCUT).convert("RGB")
        colors = sorted(q.getcolors(128 * 128) or [], reverse=True)
        dom = [c for n, c in colors if n >= 40][:12]         # 占比 ≥0.24% 的主色
        chromatic = []
        for r, g, b in dom:
            mx, mn = max(r, g, b), min(r, g, b)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if mx - mn >= 0.12 * 255 and lum < 0.92 * 255 and lum > 0.08 * 255:
                chromatic.append((lum, (r, g, b)))
        if len(chromatic) >= 2:
            warned = False
            for i in range(len(chromatic)):
                for j in range(i + 1, len(chromatic)):
                    l1, l2 = chromatic[i][0], chromatic[j][0]
                    if max(l1, l2) > 0 and abs(l1 - l2) / max(l1, l2) < 0.10:
                        results.append(("WARN",
                                        f"彩色类别 {chromatic[i][1]} / {chromatic[j][1]} "
                                        "灰度差 <10%，黑白打印可能不可辨（第 6 节色彩规范）"))
                        warned = True
            if not warned:
                results.append(("PASS", f"{len(chromatic)} 个彩色类别灰度两两可分"))
    return results


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 0
    targets = []
    for a in argv[1:]:
        p = Path(a)
        if p.is_dir():
            targets += sorted(p.rglob("*.pdf")) + sorted(p.rglob("*.png"))
        elif p.is_file():
            targets.append(p)
        else:
            print(f"[SKIP] 不存在: {p}")
    n_fail = 0
    for t in targets:
        print(f"\n■ {t}")
        checks = check_pdf(t) if t.suffix.lower() == ".pdf" else check_png(t)
        for level, msg in checks:
            print(f"  [{level}] {msg}")
            if level == "FAIL":
                n_fail += 1
    print(f"\n=== 共检查 {len(targets)} 个文件，FAIL {n_fail} 项"
          + ("，全部通过 ✔" if n_fail == 0 else "，请修复后重新自检") + " ===")
    return min(n_fail, 125)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
