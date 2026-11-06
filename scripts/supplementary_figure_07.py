import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.ticker import ScalarFormatter
from matplotlib.patches import Patch


# ============================================================
# 1. 输入和输出路径
# ============================================================

from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
input_path=ROOT/'results'/'static_P10_P90_deltas.xlsx'
output_dir=ROOT/'figures'

os.makedirs(output_dir, exist_ok=True)

output_png = os.path.join(
    output_dir,
    "supplementary_figure_07.png"
)

summary_output = ROOT / "results" / "Static_structural_sensitivity_summary.xlsx"


# ============================================================
# 2. 静态变量及显示标签
# ============================================================

static_vars = [
    "Area",
    "Depth_available_for_roots",
    "drainage_density",
    "Mean_terrain_slope",
    "conductivity_hypres"
]

# 修改后的正式显示名称
static_labels = [
    "Area",
    "Depth Available for Roots",
    "Drainage Density",
    "Mean Terrain Slope",
    "Saturated Hydraulic Conductivity"
]

targets = [
    ("IQR1", "a"),
    ("IQR2", "b"),
    ("IQR3", "c")
]


# ============================================================
# 3. 读取数据
# ============================================================

if not os.path.exists(input_path):
    raise FileNotFoundError(
        f"未找到输入文件：\n{input_path}"
    )

df = pd.read_excel(input_path)

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_", regex=False)
)


# ============================================================
# 4. 提取每个静态变量的总体结构效应
# ============================================================

def extract_effect(data, variable, target):
    """
    提取静态变量从 P10 到 P90 时的预测差异。

    优先读取：
        variable_P90_minus_P10_target

    如果该字段不存在，则计算：
        variable_prediction_P90_target
        -
        variable_prediction_P10_target
    """

    delta_col = f"{variable}_P90_minus_P10_{target}"
    p10_col = f"{variable}_prediction_P10_{target}"
    p90_col = f"{variable}_prediction_P90_{target}"

    if delta_col in data.columns:

        values = pd.to_numeric(
            data[delta_col],
            errors="coerce"
        )

    elif p10_col in data.columns and p90_col in data.columns:

        values = (
            pd.to_numeric(
                data[p90_col],
                errors="coerce"
            )
            -
            pd.to_numeric(
                data[p10_col],
                errors="coerce"
            )
        )

    else:

        raise KeyError(
            f"无法找到 {variable} 的 {target} P10/P90结果。\n"
            f"需要字段：{delta_col}\n"
            f"或同时包含：{p10_col} 和 {p90_col}"
        )

    values = (
        values
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    if values.empty:
        raise ValueError(
            f"{variable} 的 {target} 没有有效结果。"
        )

    # 对于不包含交互项的加性 GAM，
    # P90−P10 效应在各流域中理论上基本一致。
    effect = values.median()

    # 检查不同流域之间是否存在数值变化
    value_range = values.max() - values.min()

    return effect, value_range


# ============================================================
# 5. 建立汇总表
# ============================================================

summary_rows = []

for target, panel_letter in targets:

    for variable, display_label in zip(
        static_vars,
        static_labels
    ):

        effect, value_range = extract_effect(
            data=df,
            variable=variable,
            target=target
        )

        summary_rows.append(
            {
                "Target": target,
                "Panel": panel_letter,
                "Variable": variable,
                "Label": display_label,
                "Effect": effect,
                "Across_catchment_range": value_range
            }
        )

summary_df = pd.DataFrame(summary_rows)


# ============================================================
# 6. 打印检查结果
# ============================================================

print("\n静态变量结构敏感性汇总：")

print(
    summary_df[
        [
            "Target",
            "Variable",
            "Effect",
            "Across_catchment_range"
        ]
    ].to_string(index=False)
)

print(
    "\n说明：Across_catchment_range 接近0表示"
    "P90−P10效应在不同流域之间基本相同。"
)


# ============================================================
# 7. 绘制三个水平柱状图
# ============================================================

fig, axes = plt.subplots(
    nrows=1,
    ncols=3,
    figsize=(16.5, 6.3)
)

y_positions = np.arange(
    len(static_vars)
)


for ax, (target, panel_letter) in zip(
    axes,
    targets
):

    plot_data = (
        summary_df[
            summary_df["Target"] == target
        ]
        .set_index("Variable")
        .loc[static_vars]
        .reset_index()
    )

    effects = plot_data["Effect"].to_numpy(
        dtype=float
    )

    min_effect = np.nanmin(effects)
    max_effect = np.nanmax(effects)

    max_abs = np.nanmax(
        np.abs(effects)
    )

    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0


    # ========================================================
    # 正值和负值使用不同颜色
    # ========================================================

    bar_colors = [
        "#D6604D" if value >= 0 else "#4393C3"
        for value in effects
    ]

    bars = ax.barh(
        y_positions,
        effects,
        color=bar_colors,
        edgecolor="black",
        linewidth=0.7,
        height=0.66,
        zorder=2
    )


    # ========================================================
    # 设置 x 轴范围
    # ========================================================

    # 全部为正值：
    # 让 0 与左侧 y 轴完全重合
    if min_effect >= 0:

        left_limit = 0
        right_limit = max_effect + max_abs * 0.40


    # 全部为负值：
    # 让 0 位于右边界
    elif max_effect <= 0:

        left_limit = min_effect - max_abs * 0.40
        right_limit = 0

        # IQR3 的负值标签位于柱子左侧，
        # 因此额外增加左侧空间
        if target == "IQR3":
            left_limit = min_effect - max_abs * 0.55


    # 同时存在正值和负值
    else:

        left_limit = min_effect - max_abs * 0.30
        right_limit = max_effect + max_abs * 0.32


    ax.set_xlim(
        left_limit,
        right_limit
    )


    # ========================================================
    # 0 线
    # ========================================================

    # 只有正负值同时存在时，绘制内部 0 线
    if min_effect < 0 and max_effect > 0:

        ax.axvline(
            0,
            color="black",
            linewidth=1.1,
            zorder=3
        )


    # ========================================================
    # y 轴设置
    # ========================================================

    ax.set_yticks(
        y_positions
    )

    ax.set_yticklabels(
        static_labels,
        fontsize=11.5
    )

    # Area 放在最上方
    ax.invert_yaxis()

    # 不设置 x 轴标题
    ax.set_xlabel("")


    ax.tick_params(
        axis="x",
        labelsize=11,
        direction="out",
        length=4,
        width=0.8
    )

    ax.tick_params(
        axis="y",
        labelsize=11,
        direction="out",
        length=4,
        width=0.8
    )


    # ========================================================
    # 网格线
    # ========================================================

    ax.grid(
        axis="x",
        linestyle="--",
        linewidth=0.6,
        alpha=0.35,
        zorder=0
    )

    ax.set_axisbelow(True)


    # ========================================================
    # IQR3 使用科学计数法
    # ========================================================

    if target == "IQR3":

        formatter = ScalarFormatter(
            useMathText=True
        )

        formatter.set_powerlimits(
            (-2, 2)
        )

        ax.xaxis.set_major_formatter(
            formatter
        )

        ax.ticklabel_format(
            axis="x",
            style="sci",
            scilimits=(-2, 2)
        )

        # ×10^-3 的字号
        ax.xaxis.get_offset_text().set_fontsize(10)


    # ========================================================
    # 数值标签
    # ========================================================

    x_min, x_max = ax.get_xlim()
    x_range = x_max - x_min

    text_offset = x_range * 0.025


    for bar, value in zip(
        bars,
        effects
    ):

        y_position = (
            bar.get_y()
            + bar.get_height() / 2
        )

        # ----------------------------------------------------
        # Fig. c：
        # 坐标轴已经显示 ×10^-3，
        # 因此标签乘以 1000 后只显示 -1.98、-1.44 等
        # ----------------------------------------------------
        if target == "IQR3":

            value_text = f"{value * 1000:.2f}"

        elif abs(value) >= 10:

            value_text = f"{value:.1f}"

        else:

            value_text = f"{value:.2f}"


        # 正值标签放在柱子右侧
        if value >= 0:

            ax.text(
                value + text_offset,
                y_position,
                value_text,
                va="center",
                ha="left",
                fontsize=10,
                clip_on=False
            )


        # 负值标签放在柱子左侧
        else:

            ax.text(
                value - text_offset,
                y_position,
                value_text,
                va="center",
                ha="right",
                fontsize=10,
                clip_on=False
            )


    # ========================================================
    # 面板编号
    # ========================================================

    ax.text(
        -0.03,
        1.055,
        panel_letter,
        transform=ax.transAxes,
        fontsize=17,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False
    )


    # ========================================================
    # 边框设置
    # ========================================================

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)


    # 全负值图中，0 位于右侧边界。
    # 单独绘制右侧 0 线。
    if max_effect <= 0:

        ax.axvline(
            0,
            color="black",
            linewidth=1.0,
            zorder=3
        )


# ============================================================
# 8. 图例和版式
# ============================================================

legend_elements = [

    Patch(
        facecolor="#D6604D",
        edgecolor="black",
        label="Positive effect"
    ),

    Patch(
        facecolor="#4393C3",
        edgecolor="black",
        label="Negative effect"
    )
]


fig.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=2,
    frameon=False,
    fontsize=12,
    bbox_to_anchor=(0.5, 0.015)
)


plt.subplots_adjust(
    left=0.145,
    right=0.985,
    top=0.90,
    bottom=0.15,
    wspace=0.53
)


# ============================================================
# 9. 保存图片
# ============================================================

plt.savefig(
    output_png,
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.08
)

plt.show()

plt.close(fig)


# ============================================================
# 10. 保存汇总数值
# ============================================================

summary_df.to_excel(
    summary_output,
    index=False
)


print(
    f"\n柱状图已保存：\n{output_png}"
)

print(
    f"\n汇总数值已保存：\n{summary_output}"
)