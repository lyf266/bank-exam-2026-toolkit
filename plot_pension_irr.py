#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
养老金账户回本周期、动态 IRR 测算与多维评估图表生成器
技术栈: numpy, scipy, matplotlib
字体规范: Noto Sans CJK SC (思源黑体)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.optimize import root_scalar

# 1. 字体与绘图环境配置 (严格执行思源黑体规范)
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'Source Han Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

# 2. 基础财务数据与精算函数
PAY_ANNUAL = 5000.0       # 每年缴费
PAY_YEARS = 5             # 缴费年数
TOTAL_PAY = PAY_ANNUAL * PAY_YEARS # 总缴费 25,000 元
RECEIVE_ANNUAL = 8000.0   # 每年领取
START_YEAR = 6            # 第6年末开始领第一笔
DISCOUNT_RATE = 0.025     # 基准贴现率 2.5% (对齐长期国债基准)

def get_cash_flows(n_receive_years):
    """生成前 5 年缴费 + n 年领取的现金流数组 (索引 t=0..5+n)"""
    total_len = 5 + n_receive_years + 1
    cfs = [0.0] * total_len
    for t in range(1, 6):
        cfs[t] = -PAY_ANNUAL
    for t in range(6, 6 + n_receive_years):
        cfs[t] = RECEIVE_ANNUAL
    return cfs

def npv(r, cfs):
    """计算净现值 NPV"""
    return sum(c / ((1.0 + r) ** t) for t, c in enumerate(cfs))

def calc_irr(cfs):
    """精确求解 IRR"""
    signs = [np.sign(c) for c in cfs if c != 0]
    if all(s > 0 for s in signs) or all(s < 0 for s in signs):
        return None
    try:
        res = root_scalar(lambda r: npv(r, cfs), bracket=[-0.6, 2.5], method='brentq')
        return res.root
    except Exception:
        return None

# 3. 计算回本周期与动态指标
# 静态回本: 25000 / 8000 = 3.125 年 (领取起第 3.125 年 / 自投资起第 8.125 年)
static_payback_receive = TOTAL_PAY / RECEIVE_ANNUAL
static_payback_total = 5.0 + static_payback_receive

# 动态回本 (r=2.5%):
pv_pay = sum(PAY_ANNUAL / ((1.0 + DISCOUNT_RATE) ** t) for t in range(1, 6))
# 找到动态现值转正点
dynamic_payback_total = None
cum_pv = -pv_pay
for t in range(6, 25):
    pv_rec = RECEIVE_ANNUAL / ((1.0 + DISCOUNT_RATE) ** t)
    prev_cum = cum_pv
    cum_pv += pv_rec
    if prev_cum < 0 and cum_pv >= 0:
        # 线性内插获得精确动态回本年份
        frac = (-prev_cum) / pv_rec
        dynamic_payback_total = (t - 1) + frac
        break

dynamic_payback_receive = dynamic_payback_total - 5.0

# 4. 计算 1~30 年领取期限的动态 IRR 与 NPV
years_range = np.arange(1, 31)
irr_list = []
npv_0_list = []
npv_25_list = []
npv_50_list = []

for yr in years_range:
    cfs = get_cash_flows(yr)
    irr_val = calc_irr(cfs)
    irr_list.append(irr_val * 100 if irr_val is not None else np.nan)
    npv_0_list.append(npv(0.0, cfs))
    npv_25_list.append(npv(0.025, cfs))
    npv_50_list.append(npv(0.050, cfs))

irr_array = np.array(irr_list)

# 5. 构建专业 2x2 四联看板
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("养老金账户回本周期、动态 IRR 测算与可行性精算分析", fontsize=18, fontweight='bold', y=0.98, color='#1A202C')

# ==================== 子图 1: 现金流时序瀑布与回本平衡点 ====================
ax1 = axes[0, 0]
timeline_years = np.arange(1, 16) # 展示前 15 年
cf_timeline = np.array([get_cash_flows(10)[t] for t in timeline_years])
cum_cf_timeline = np.cumsum(cf_timeline)

# 绘制柱状图
bar_colors = ['#E53E3E' if c < 0 else '#319795' for c in cf_timeline]
bars = ax1.bar(timeline_years - 0.15, cf_timeline, width=0.5, color=bar_colors, alpha=0.85, label='当期净现金流 (元)')

# 叠加累计现金流折线
ax1_twin = ax1.twinx()
ax1_twin.plot(timeline_years, cum_cf_timeline, color='#2B6CB0', marker='o', linewidth=2.5, label='累计净现金流 (元)')
ax1_twin.axhline(0, color='#718096', linestyle='--', linewidth=1.2, alpha=0.8)

# 标注静态回本点
ax1_twin.axvline(static_payback_total, color='#D69E2E', linestyle='-.', linewidth=2, label=f'静态回本点: 第 {static_payback_total:.2f} 年')
ax1_twin.scatter([static_payback_total], [0], color='#D69E2E', s=100, zorder=5)
ax1_twin.annotate(f'静态回本\n第 {static_payback_total:.2f} 年\n(起领后 {static_payback_receive:.2f} 年)', 
                  xy=(static_payback_total, 0), xytext=(static_payback_total - 2.8, 12000),
                  arrowprops=dict(arrowstyle='->', color='#D69E2E', lw=1.5),
                  fontsize=10, fontweight='bold', color='#B7791F',
                  bbox=dict(boxstyle='round,pad=0.4', facecolor='#FEFCBF', edgecolor='#D69E2E', alpha=0.9))

ax1.set_title("① 现金流时序与回本周期平衡点 (前 15 年)", fontsize=13, fontweight='bold', pad=10, color='#2D3748')
ax1.set_xlabel("投资经过保单年度 (年)", fontsize=11)
ax1.set_ylabel("当期现金流 (元)", fontsize=11, color='#2D3748')
ax1_twin.set_ylabel("累计净现金流 (元)", fontsize=11, color='#2B6CB0')
ax1.set_xticks(timeline_years)
ax1.grid(True, linestyle=':', alpha=0.5)

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

# ==================== 子图 2: 内部收益率 (IRR) 敏感性精算收敛曲线 ====================
ax2 = axes[0, 1]
ax2.plot(years_range, irr_array, color='#3182CE', linewidth=2.8, marker='s', markersize=4, label='实际内部收益率 IRR(N)')

# 关键基准线
ax2.axhline(0, color='#A0AEC0', linestyle='--', linewidth=1, label='盈亏平衡线 (0.0%)')
ax2.axhline(1.8, color='#38A169', linestyle=':', linewidth=1.5, label='银行 5 年定存基准 (~1.8%)')
ax2.axhline(2.2, color='#D69E2E', linestyle=':', linewidth=1.5, label='30 年超长期国债 (~2.2%)')
ax2.axhline(2.5, color='#E53E3E', linestyle='--', linewidth=1.5, label='监管普通险预定利率上限 (2.5%)')
ax2.axhline(20.97, color='#805AD5', linestyle='-.', linewidth=1.2, label='30 年渐近理论极限 (~20.97%)')

# 标注关键数据点
key_points = [
    (3, irr_array[2], f"领3年: {irr_array[2]:.2f}%\n(未达保本)"),
    (4, irr_array[3], f"领4年: {irr_array[3]:.2f}%\n(跑赢国债)"),
    (5, irr_array[4], f"领5年: {irr_array[4]:.2f}%"),
    (10, irr_array[9], f"领10年: {irr_array[9]:.2f}%"),
    (20, irr_array[19], f"领20年: {irr_array[19]:.2f}%"),
    (30, irr_array[29], f"领30年: {irr_array[29]:.2f}%")
]

for yr, val, txt in key_points:
    ax2.scatter(yr, val, color='#E53E3E' if val < 0 else '#2B6CB0', s=60, zorder=4)
    y_offset = -8 if yr == 3 else (6 if yr in [4, 5] else (-6 if yr == 10 else 4))
    x_offset = 0.5 if yr <= 10 else -2.5
    ax2.annotate(txt, xy=(yr, val), xytext=(yr + x_offset, val + y_offset),
                 fontsize=8.5, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color='#4A5568', lw=1),
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#EDF2F7', edgecolor='#CBD5E0', alpha=0.85))

ax2.set_title("② 内部收益率 (IRR) 随领取年限收敛曲线", fontsize=13, fontweight='bold', pad=10, color='#2D3748')
ax2.set_xlabel("领取年限 N (自第 6 年起连续领取年数)", fontsize=11)
ax2.set_ylabel("内部收益率 IRR (%)", fontsize=11)
ax2.set_ylim(-40, 26)
ax2.set_xlim(0, 31)
ax2.grid(True, linestyle=':', alpha=0.5)
ax2.legend(loc='lower right', fontsize=9, framealpha=0.9)

# ==================== 子图 3: 多贴现率下净现值 (NPV) 增长曲面 ====================
ax3 = axes[1, 0]
ax3.plot(years_range, npv_0_list, color='#2B6CB0', linewidth=2.2, label='贴现率 r = 0.0% (名义累积净现金流)')
ax3.plot(years_range, npv_25_list, color='#DD6B20', linewidth=2.5, label='贴现率 r = 2.5% (长期国债/社会基准)')
ax3.plot(years_range, npv_50_list, color='#805AD5', linewidth=2.0, linestyle='--', label='贴现率 r = 5.0% (高风险贴现)')

ax3.axhline(0, color='#E53E3E', linestyle='-', linewidth=1.2, alpha=0.7)

# 标出 r=2.5% 时的转正点
ax3.axvline(dynamic_payback_receive, color='#DD6B20', linestyle=':', linewidth=1.5)
ax3.scatter([dynamic_payback_receive], [0], color='#DD6B20', s=80, zorder=5)
ax3.annotate(f'动态回本点 (r=2.5%)\n起领第 {dynamic_payback_receive:.2f} 年\n(投资第 {dynamic_payback_total:.2f} 年)', 
             xy=(dynamic_payback_receive, 0), xytext=(dynamic_payback_receive + 1.5, -25000),
             arrowprops=dict(arrowstyle='->', color='#DD6B20', lw=1.5),
             fontsize=9.5, fontweight='bold', color='#C05621',
             bbox=dict(boxstyle='round,pad=0.35', facecolor='#FEEBC8', edgecolor='#DD6B20', alpha=0.9))

ax3.set_title("③ 不同贴现率下的净现值 (NPV) 增长趋势", fontsize=13, fontweight='bold', pad=10, color='#2D3748')
ax3.set_xlabel("领取年限 N (年)", fontsize=11)
ax3.set_ylabel("净现值 NPV (元)", fontsize=11)
ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{x/10000:.1f}万'))
ax3.grid(True, linestyle=':', alpha=0.5)
ax3.legend(loc='upper left', fontsize=9.5, framealpha=0.9)

# ==================== 子图 4: 核心财务决策看板与金融穿透预警 ====================
ax4 = axes[1, 1]
ax4.axis('off')

# 构建富文本卡片
card_text = """
【 核心精算结论与回本指标 】
---------------------------------------------------------------------------------------------------------
• 初始投入本金：每年交 5,000 元 × 5 年 = 共交 25,000 元 (期末年金, PV: 0)
• 每年返还金额：自第 6 年末起，每年领取 8,000 元 (年返本率高达 32.0%)
• 静态回本周期：起领后 3.125 年 (约 3 年 1 个半月) ｜ 投资全周期 8.125 年
• 动态贴现回本：基准利率 2.5% 下，起领后 3.49 年 (投资全周期 8.49 年)
• 动态 IRR 收敛区间：
    - 领 3 年：IRR = -1.02% (累计拿回 2.4 万元，本金微亏 1000 元)
    - 领 4 年：IRR = +5.61% (累计 3.2 万元，已大幅跑赢长债与定存)
    - 领 5 年：IRR = +9.86% ｜ 领 10 年：IRR = +18.09% ｜ 领 20 年：IRR = +20.71%
    - 领 30 年(终身)：极限逼近 +20.97% (累计领取 24.0 万元，净收益 21.5 万元)

---------------------------------------------------------------------------------------------------------
【 投资可行性穿透研判：值得投吗？ 】
---------------------------------------------------------------------------------------------------------
➊ 【纯数学理论与试题视角】：★★★★★ 极其超值、稳赚不赔！
     只需活过第 9 年（领满 4 年），锁定年化超 5.6% 确定性复利，寿命越长回报越惊人。
➋ 【真实金融世界与监管常识】：⚠️ 极度高危！违背金融第一性原理！
     • 监管红线对比：金融监管总局规定，正规人身保险法定预定利率上限仅 2.5%。
     • 风险穿透警示：任何正规持牌机构都不可能承诺“年返 32%”且保本终身。
     • 常见套路甄别：
       ① 资金盘/庞氏骗局：用后人本金返前人，2~3 年后暴雷跑路；
       ② 隐瞒领取年限：合同中可能隐藏“仅限期领取 3 年”，届时刚好不保本 (IRR -1%)；
       ③ 演示浮动非保证分红：将极端高风险结算包装成刚性兑付。
"""

ax4.text(0.02, 0.98, card_text, transform=ax4.transAxes,
         fontsize=10.2, verticalalignment='top', fontfamily='Noto Sans CJK SC',
         bbox=dict(boxstyle='round,pad=0.7', facecolor='#F7FAFC', edgecolor='#CBD5E0', lw=1.5),
         color='#1A202C')

plt.tight_layout(rect=[0, 0, 1, 0.96])

output_path = "/home/f1are/orca/workspaces/银行从业备考/anki/pension_cashflow_irr_analysis.png"
plt.savefig(output_path, dpi=300)
plt.close()

print(f"[SUCCESS] 图表已成功生成并保存至: {output_path}")
