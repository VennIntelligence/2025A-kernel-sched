# Plotting Standards — CVPR Academic Style

> 本文档定义了项目的绘图硬性标准。所有提交到论文、notebook 和报告的图表必须遵守。
> 标准实现见 `src/ks_core/plotting.py`。

---

## Typography

### Font

- **字体族**: serif (Times New Roman / Times / DejaVu Serif)
- **数学字体**: STIX (与 Times 衬线配套)
- **图表内容全部英文**；中文仅用于 notebook markdown 解读文字

### 字号层级 (固定值，不得随意偏离)

| 层级 | 大小 (pt) | 权重 | 用途 |
|------|-----------|------|------|
| `suptitle` | 11 | bold | 仅多面板 figure 的总标题 |
| `ax.set_title` | 10 | bold | 单 axes 标题 |
| `ax.set_xlabel/ylabel` | 9 | normal | 坐标轴标签 |
| tick labels | 8 | normal | 坐标轴刻度值 |
| legend text | 8 | normal | 图例文字 |
| annotation text | 7–8 | normal | heatmap 内数字、bar 顶端值 |
| colorbar label | 8 | normal | colorbar 侧标注 |

### 物理量标注规范

- 时间单位: `[cycles]`, `[ms]`, `[us]`
- 内存大小: `[KB]`, `[MB]`
- 百分比: `[%]`
- 无量纲指标: 不加单位，但 label 必须有描述
- 物理量 label 始终用「描述 + 单位」格式，例如 `"Total latency [cycles]"`
- **不要在 label 里放段落式长文**: axis label 不超过 50 个字符

---

## Figure Sizing

| Layout Key | Width × Height (inches) | 用途 |
|------------|------------------------|------|
| `single_col` | 3.5 × 2.6 | 论文单栏图 |
| `one_half_col` | 5.5 × 3.5 | 论文 1.5 栏图 |
| `double_col` | 7.2 × 4.0 | 论文双栏图 |
| `notebook` | 8.0 × 5.0 | Notebook 展示 |

- 高度以「内容呼吸空间充足、不挤压」为准
- 若 subplot 行数 > 2，宁可加大高度也不要让 tick label 叠字

---

## Colour Policy

### 主色板 (≤ 6 种方法对比时使用)

```python
METHOD_PALETTE = {
    "primary":    "#4C72B0",   # steel blue
    "secondary":  "#55A868",   # muted green
    "accent_1":   "#C44E52",   # soft red
    "accent_2":   "#8172B2",   # lavender purple
    "accent_3":   "#DD8452",   # warm orange
    "neutral":    "#937860",   # taupe
}
```

### Colormap 选择

| 场景 | Colormap | 说明 |
|------|----------|------|
| DAG 密度 / 节点权重 | `"inferno"` | 高对比、色盲友好 |
| 残差 heatmap (单侧 ≥ 0) | `"YlOrRd"` | 零值亮，高值暖红 |
| 残差 diff (双侧 ±) | `"RdBu_r"` | 对称发散色，零值白色 |
| coverage / utilisation | `"viridis"` | 感知均匀，打印友好 |

### 色盲安全

- 禁止仅用红-绿对比来区分数据；必须辅以 marker 形状或 line style 区分
- 如需 > 6 色，优先使用 `"tab10"` 子集

---

## Layout & Readability Rules

### 间距与防重叠

1. **子图间距**: 优先使用 `constrained_layout=True`
2. **tick label 不叠字**: 如果 x 轴 tick 过密，使用 `rotation=45, ha="right"` 或 `MaxNLocator`
3. **legend 不遮挡数据**:
   - 优先用 `bbox_to_anchor=(0.5, -0.15)` + `loc="upper center"` 放在图下方
   - **永远不要让 legend 覆盖数据点或曲线**
4. **colorbar 不挤压主图**: 使用 `fraction=0.046, pad=0.04`

### Spine 和 Grid

- 默认 **关闭** top + right spines
- Grid 仅在确实帮助读数的场景启用:
  ```python
  ax.grid(axis="y", alpha=0.3, linewidth=0.5)
  ```

### 参考线

- 阈值参考线使用 `ls="--"` 灰色 (`#666666`)，线宽 `0.8 – 1.0`
- 参考线必须有对应 legend entry 或 annotation

---

## Saving Conventions

```python
fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
```

- **dpi=300** 是论文提交最低要求
- **bbox_inches="tight"** 避免裁掉外置 legend
- **facecolor="white"** 避免透明背景
- 保存格式: notebook 展示用 `.png`；论文草稿用 `.pdf`（矢量）

---

## Anti-Patterns (禁止项)

| ❌ 禁止 | ✅ 应改为 |
|---------|----------|
| `font.family: sans-serif / Arial` | `font.family: serif / Times New Roman` |
| 在 figure 函数里写 `fontsize=12` | 统一由 rcParams 控制 |
| `savefig(dpi=180)` 或更低 | `savefig(dpi=300)` |
| 轴标签里写中文 | 图表内容全部英文 |
| `plt.show()` 在构建脚本里 | 只 `savefig` + `plt.close(fig)` |
| legend 覆盖数据区域 | legend 放图外或空白角落 |
| 使用 `"jet"` colormap | 使用 `"viridis"` / `"inferno"` / `"YlOrRd"` |
| 图中只用颜色区分类别 | 同时用 marker 形状或 linestyle 辅助区分 |

---

## Checklist (每张 figure 提交前必须过的检查点)

- [ ] 字体为 serif (Times New Roman)
- [ ] 所有 axis label 和 title 使用英文
- [ ] 所有物理量标注包含单位
- [ ] tick label 无重叠
- [ ] legend 不覆盖数据
- [ ] colorbar label 有描述和单位
- [ ] 无 `"jet"` colormap
- [ ] dpi ≥ 300
- [ ] 导出白色背景
- [ ] 在 3.5 英寸宽度下文字仍可阅读
