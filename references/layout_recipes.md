# 组合图版式与常用图元代码配方

配合 `assets/journal_init.py` 中的 `CM / HALF_W / FULL_W / panel / center_bottom_left / savefig` 使用。
完整规范（判断标准、字体、色彩、地图合规等）见 `figure_spec.md`。

---

## 1 子图数 → 排布速查

| 子图数 | 排布 | 图幅 |
|---|---|---|
| 1 | 单幅 | 半栏 `HALF_W` 或通栏 `FULL_W` |
| 2 | 1 行 2 列 | `FULL_W` |
| **3** | **2×2，第二行 1 幅居中** | `FULL_W`，总高 10–12 cm |
| **4** | **2×2** | `FULL_W`，总高 10–12 cm |
| 5–6 | 2 行 3 列 | `FULL_W` |
| ≥7 | 拆成两张图（优先） | — |

铁律：同一图内各面板**等大**；阅读顺序 Z 形，(a)(b)(c) 不跳号；
间距 `wspace≈0.25–0.35`、`hspace≈0.35–0.45`；上下行 x 轴、左右列 y 轴必须对齐。

---

## 2 四面板：2×2

```python
fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 10 * CM), sharey="row")
# 依次绘制 (a)(b)(c)(d) ...
fig.tight_layout()
for ax, tag in zip(axes.flat, ["(a)", "(b)", "(c)", "(d)"]):
    panel(ax, tag)
savefig(fig, "W2_fig07_residual_diagnostics.png")   # 无 set_title
```

## 3 三面板：2×2 第二行居中

```python
fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 11 * CM))
# 绘制 axes[0,0] (a)、axes[0,1] (b)、axes[1,0] (c)
fig.tight_layout()                 # ★ 先 tight_layout 再平移
center_bottom_left(fig, axes)      # 删 axes[1,1]、axes[1,0] 水平居中（等大）
panel(axes[0, 0], "(a)"); panel(axes[0, 1], "(b)"); panel(axes[1, 0], "(c)")
savefig(fig, "W1_fig04_feature_engineering.png")
```

> `tight_layout()` 会撤销 `set_position()`，顺序不能反。`savefig(bbox_inches="tight")`
> 只裁白边，不会再动面板相对位置。

## 4 六面板：2 行 3 列

```python
fig, axes = plt.subplots(2, 3, figsize=(FULL_W, 9 * CM), sharey="row")
fig.tight_layout(h_pad=1.2, w_pad=0.8)
for ax, tag in zip(axes.flat, ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]):
    panel(ax, tag)
```

## 5 手动不均匀布局：GridSpec

需要某面板跨列/高宽不等时用 GridSpec，但各面板**等宽列、等高行**的基准网格不变：

```python
fig = plt.figure(figsize=(FULL_W, 11 * CM))
gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.3)
ax1 = fig.add_subplot(gs[0, :])    # (a) 占整行（如时间序列）
ax2 = fig.add_subplot(gs[1, 0])    # (b)
ax3 = fig.add_subplot(gs[1, 1])    # (c)
```

---

## 6 共享坐标轴

```python
fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 10 * CM), sharex="col", sharey="row")
```

- 内部面板重复刻度自动隐藏，属正常现象；标目只写最外侧面板；
- 各面板量级差超过一个数量级时不强行共享，改独立刻度。

## 7 双 y 轴（能不用就不用）

```python
ax2 = ax.twinx()
l1, = ax.plot(x, y1, color="#185FA5")          # 左轴量
l2, = ax2.plot(x, y2, color="#D85A30")         # 右轴量
ax.set_ylabel("蒸散发/mm", color="#185FA5")     # ★ 轴、刻度、曲线同色
ax2.set_ylabel("气温/℃", color="#D85A30")
ax.tick_params(axis="y", colors="#185FA5")
ax2.tick_params(axis="y", colors="#D85A30")
```

图注必须写明"左轴对应××，右轴对应××"；三个及以上 y 轴一律禁止。

## 8 多面板共用一个 colorbar（vmin/vmax 全局统一）

```python
vmin, vmax = float(data.min()), float(data.max())   # 全局范围，所有面板共用
fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 5.5 * CM))
for ax, d in zip(axes, [d1, d2]):
    im = ax.scatter(x, y, c=d, vmin=vmin, vmax=vmax, cmap="RdBu_r", s=14)
panel(axes[0], "(a)"); panel(axes[1], "(b)")
cbar = fig.colorbar(im, ax=axes.tolist(), shrink=0.9, pad=0.02)
cbar.set_label("残差/m", fontsize=9)                 # 标目同样用「量/单位」
```

分级设色时 colorbar 用离散色块、刻度落在分级断点上。

## 9 线型 + 标记三重编码（黑白打印可辨）

```python
STYLES = [  # 颜色 + 线型 + 标记，最多 4 个系列，再多拆图
    dict(color="#185FA5", linestyle="-",  marker="o",  markerfacecolor="#185FA5"),
    dict(color="#D85A30", linestyle="--", marker="s",  markerfacecolor="white"),
    dict(color="#0F6E56", linestyle="-.", marker="^",  markerfacecolor="#0F6E56"),
    dict(color="#534AB7", linestyle=":",  marker="o",  markerfacecolor="white"),
]
for kv, st in zip(data_dict.items(), STYLES):
    ax.plot(kv[1].index, kv[1].values, label=kv[0], **st, markersize=4)
```

同一篇文章内各图的系列样式必须稳定（同一模型不换色换型）。

## 10 图内标注与显著性

```python
# 条形末端标值与刻度二选一；标注不压线不压点
for rect, v in zip(bars, values):
    ax.text(rect.get_x() + rect.get_width() / 2, v + off, f"{v:.3f}",
            ha="center", va="bottom")

# 显著性 bracket
y_max = values.max() * 1.12
ax.plot([x1, x1, x2, x2], [y_max, y_max + h, y_max + h, y_max],
        lw=0.8, c="black")
ax.text((x1 + x2) / 2, y_max + h, "**", ha="center", va="bottom")  # 含义写图注
```

---

## 11 图注模板（图下 markdown 单元）

```markdown
> **图4**　(a) 性别、(b) 舱位等级、(c) 登船港口分组下的生还率，
> 虚线为整体基准生还率 38.4%，误差棒为 95% 置信区间。
> Sex 的组间差异最大，是最强的单因子。
>
> **Fig. 4**　Survival rate by (a) sex, (b) passenger class, (c) port of embarkation ...
```

四段齐全：① 编号+总述 ② 面板释义 ③ 符号约定（误差棒/虚线/颜色含义）④ 结论性解读。
地图类图件在图注末注明底图来源与审图号。

## 12 地图底图合规（红线）

- 底图必须来自自然资源部标准地图服务系统（`bzdt.ch.mnr.gov.cn`），不用随手 shp；
- 中国全图完整表示南海诸岛、台湾岛、钓鱼岛及其附属岛屿，不得漏绘错绘；
- 图廓外标注审图号 `GS(20XX)XXXX号`；图注写明投影参数；
- 指北针、比例尺、经纬网注记（`110°E`、`35°N`，间隔取整）齐全；无数据区浅灰填充并标注。
