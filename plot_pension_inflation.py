#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
养老金账户通胀侵蚀与年金涨幅精算分析图表生成器
技术栈: numpy, scipy, matplotlib
字体规范: Noto Sans CJK SC (思源黑体)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.optimize import root_scalar

# 1. 字体配置
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'Source Han Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

# 2. 基础财务数据
PAY_ANNUAL = 5000.0
PAY_YEARS = 5
BASE_RECEIVE = 8000.0
YEARS = 30 # 领取 30 年

def get_real_cashflows(n_years, inflation=0.025, g=0.0):
    cfs = [0.0] * (5 + n_years + 1)
    for t in range(1, 6):
        cfs[t] = -PAY_ANNUAL / ((1.0 + inflation) ** t)
    for k in range(n_years):
        t = 6 + k
        nom = BASE_RECEIVE * ((1.0 + g) ** k)
        cfs[t] = nom / ((1.0 + inflation) ** t)
    return cfs

def npv(r, cfs):
    return sum(c / ((1.0 + r) ** t) for t, c in enumerate(cfs))

def calc_irr(cfs):
    signs = [np.sign(c) for c in cfs if c != 0]
    if all(s > 0 for s in signs) or all(s < 0 for s in signs):
        return None
    try:
        res = root_scalar(lambda r: npv(r, cfs), bracket=[-0.6, 2.5], method='brentq')
        return res.root
    except Exception:
        return None

# 3. 计算购买力折算与现金流序列
t_timeline = np.arange(6, 36) # 第 6 年至第 35 年
k_timeline = np.arange(0, 30)

# 名义固定 (g=0)
cf_nom_fixed = np.full(30, BASE_RECEIVE)
# 实际购买力 (g=0, infl=2.5%)
cf_real_fixed_25 = BASE_RECEIVE / ((1.0 + 0.025) ** t_timeline)
# 实际购买力 (g=0, infl=3.0%)
cf_real_fixed_30 = BASE_RECEIVE / ((1.0 + 0.030) ** t_timeline)
# 实际购买力 (g=2.5% 递增, infl=2.5%)
cf_real_grow_match = (BASE_RECEIVE * ((1.0 + 0.025) ** k_timeline)) / ((1.0 + 0.025) ** t_timeline)
# 实际购买力 (g=3.5% 社保式递增, infl=2.5%)
cf_real_grow_social = (BASE_RECEIVE * ((1.0 + 0.035) ** k_timeline)) / ((1.0 + 0.025) ** t_timeline)

# 4. 计算 1~30 年不同情景下的 Real IRR
n_range = np.arange(1, 31)

irr_nom = [calc_irr(get_real_cashflows(yr, inflation=0.0, g=0.0)) * 100 for yr in n_range]
irr_real_inf25 = [calc_irr(get_real_cashflows(yr, inflation=0.025, g=0.0)) * 100 for yr in n_range]
irr_real_grow25 = [calc_irr(get_real_cashflows(yr, inflation=0.025, g=0.025)) * 100 for yr in n_range]
irr_real_grow35 = [calc_irr(get_real_cashflows(yr, inflation=0.025, g=0.035)) * 100 for yr in n_range]

# 5. 构建 2x2 四联对比看板
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("养老金全周期：通货膨胀侵蚀与年金涨幅动态精算对比", fontsize=18, fontweight='bold', y=0.98, color='#1A202C')

# ==================== 子图 1: 实际购买力衰减曲线 (8000 元的贬值历程) ====================
ax1 = axes[0, 0]
ax1.plot(t_timeline, cf_nom_fixed, color='#718096', linestyle='--', linewidth=2, label='名义固定给付 (每年 8,000 元)')
ax1.plot(t_timeline, cf_real_fixed_25, color='#E53E3E', linewidth=2.8, label='固定年金实际购买力 (通胀率 2.5%)')
ax1.plot(t_timeline, cf_real_grow_match, color='#3182CE', linewidth=2.5, linestyle='-.', label='保额递增年金 (年涨 2.5% 抵御通胀)')
ax1.plot(t_timeline, cf_real_grow_social, color='#38A169', linewidth=2.5, label='动态调整年金 (年涨 3.5% 超额购买力)')

# 标注购买力衰减点
ax1.scatter([6, 20, 35], [cf_real_fixed_25[0], cf_real_fixed_25[14], cf_real_fixed_25[29]], color='#E53E3E', s=60, zorder=5)
ax1.annotate(f'第6年起领购买力\n仅值 ¥{cf_real_fixed_25[0]:.0f}', xy=(6, cf_real_fixed_25[0]), xytext=(7.5, 7100),
             arrowprops=dict(arrowstyle='->', color='#E53E3E'), fontsize=9, fontweight='bold', color='#C53030')
ax1.annotate(f'第20年购买力\n仅值 ¥{cf_real_fixed_25[14]:.0f} (-39%)', xy=(20, cf_real_fixed_25[14]), xytext=(17, 3900),
             arrowprops=dict(arrowstyle='->', color='#E53E3E'), fontsize=9, fontweight='bold', color='#C53030')
ax1.annotate(f'第35年购买力\n仅值 ¥{cf_real_fixed_25[29]:.0f} (-58%)', xy=(35, cf_real_fixed_25[29]), xytext=(28, 2600),
             arrowprops=dict(arrowstyle='->', color='#E53E3E'), fontsize=9, fontweight='bold', color='#C53030')

ax1.set_title("① 通胀对未来年金购买力的长期侵蚀 (以现值折算)", fontsize=13, fontweight='bold', pad=10)
ax1.set_xlabel("投资经过保单年度 (年)", fontsize=11)
ax1.set_ylabel("年金当期实际购买力 (元/年)", fontsize=11)
ax1.set_ylim(2000, 11000)
ax1.grid(True, linestyle=':', alpha=0.5)
ax1.legend(loc='lower left', fontsize=9.5, framealpha=0.9)

# ==================== 子图 2: 实际内部收益率 (Real IRR) 对比曲线 ====================
ax2 = axes[0, 1]
ax2.plot(n_range, irr_nom, color='#718096', linestyle='--', linewidth=2, label='名义 IRR (无通胀基准, 极限 20.97%)')
ax2.plot(n_range, irr_real_inf25, color='#E53E3E', linewidth=2.8, label='固定年金实际 Real IRR (通胀 2.5%, 极限 18.06%)')
ax2.plot(n_range, irr_real_grow25, color='#3182CE', linewidth=2.2, linestyle='-.', label='递增年金 Real IRR (年金涨 2.5%, 极限 20.12%)')
ax2.plot(n_range, irr_real_grow35, color='#38A169', linewidth=2.5, label='社保式年金 Real IRR (年金涨 3.5%, 极限 20.96%)')

ax2.axhline(0, color='#CBD5E0', linestyle='-', linewidth=1)
ax2.axhline(2.5, color='#DD6B20', linestyle=':', linewidth=1.5, label='监管普通险预定利率基准 (2.5%)')

# 标注领4年与领30年的差异
ax2.scatter([4], [irr_real_inf25[3]], color='#E53E3E', s=70, zorder=5)
ax2.annotate(f'领4年 Real IRR: {irr_real_inf25[3]:.2f}%\n(名义值为 5.61%)', xy=(4, irr_real_inf25[3]), xytext=(5.5, -5),
             arrowprops=dict(arrowstyle='->', color='#E53E3E'), fontsize=9, fontweight='bold', color='#C53030')

ax2.set_title("② 名义 IRR vs 扣除通胀后的实际收益率 (Real IRR)", fontsize=13, fontweight='bold', pad=10)
ax2.set_xlabel("领取年限 N (年)", fontsize=11)
ax2.set_ylabel("内部收益率 (%)", fontsize=11)
ax2.set_ylim(-35, 26)
ax2.grid(True, linestyle=':', alpha=0.5)
ax2.legend(loc='lower right', fontsize=9, framealpha=0.9)

# ==================== 子图 3: 通胀与涨幅对【实际回本期】的影响 ====================
ax3 = axes[1, 0]
scenarios = [
    ("名义固定 (无通胀)", 3.125, "#3182CE"),
    ("固定年金 (通胀 2.0%)", 3.40, "#DD6B20"),
    ("固定年金 (通胀 2.5%)", 3.47, "#E53E3E"),
    ("固定年金 (通胀 3.0%)", 3.55, "#C53030"),
    ("递增年金 (涨3%, 通胀2.5%)", 3.35, "#38A169"),
]

labels = [s[0] for s in scenarios]
paybacks = [s[1] for s in scenarios]
colors = [s[2] for s in scenarios]

y_pos = np.arange(len(labels))
bars = ax3.barh(y_pos, paybacks, color=colors, height=0.55, alpha=0.85)

for bar, val in zip(bars, paybacks):
    ax3.text(val + 0.05, bar.get_y() + bar.get_height()/2, f"{val:.2f} 年", 
             va='center', ha='left', fontsize=10, fontweight='bold', color='#2D3748')

ax3.set_yticks(y_pos)
ax3.set_yticklabels(labels, fontsize=10.5)
ax3.set_xlim(0, 4.5)
ax3.set_title("③ 不同通胀与年金涨幅下的【起领后实际回本年限】", fontsize=13, fontweight='bold', pad=10)
ax3.set_xlabel("起领后实际购买力回收期 (年)", fontsize=11)
ax3.grid(True, linestyle=':', alpha=0.5, axis='x')

# ==================== 子图 4: 精算启示与养老配置深度指南 ====================
ax4 = axes[1, 1]
ax4.axis('off')

card_text = """
【 通胀与年金涨幅的精算启示 (第一性原理) 】
---------------------------------------------------------------------------------------------------------
➊ 为什么原题默认未计通胀？
   • 经典考题与常规金融宣传均采用【名义现金流】计量；
   • 原题“每年交 5,000，五年后每年收 8,000”，属于典型的【固定年金 (g=0)】。

➋ 通胀对养老金的“钝刀割肉”效应：
   • 若以长期平均通胀率 2.5% 测算：
     - 起领第 1 年（第 6 年末）：8,000 元实际价值仅相当于今天的 6,898 元；
     - 领到第 20 年（75 岁）：8,000 元实际价值缩水至 4,882 元 (折损 ~39%)；
     - 领到第 30 年（85 岁）：8,000 元实际价值缩水至 3,374 元 (折损 ~58%)！
   • 结论：固定年金看似安全，但 30 年长周期下会面临极严重的【购买力腰斩风险】。

➌ 实际收益率 (Real IRR) 修正规律：
   • 依据费雪方程式：实际收益率 ≈ 名义收益率 - 通货膨胀率；
   • 领 4 年实际 IRR 从 5.61% 降为 3.03%；
   • 终身实际 IRR 从 20.97% 降为 18.06% (被通胀吃掉约 2.9 个百分点)。

➍ 商业年金 vs 养老金三支柱对策：
   • 商业固定年金 (g=0)：锁定确定性现金流底仓，但抗通胀能力极弱；
   • 基本养老金 (社保第一支柱)：具备国家强制动态上调机制 (年均涨 3%~4%)；
   • 个人养老金 (第三支柱公募/分红型)：必须搭配权益资产或浮动分红平抑通胀！
"""

ax4.text(0.02, 0.98, card_text, transform=ax4.transAxes,
         fontsize=10.2, verticalalignment='top', fontfamily='Noto Sans CJK SC',
         bbox=dict(boxstyle='round,pad=0.7', facecolor='#F7FAFC', edgecolor='#CBD5E0', lw=1.5),
         color='#1A202C')

plt.tight_layout(rect=[0, 0, 1, 0.96])

output_path = "/home/f1are/orca/workspaces/银行从业备考/anki/pension_inflation_growth_analysis.png"
plt.savefig(output_path, dpi=300)
plt.close()
print(f"[SUCCESS] 通胀与年金涨幅分析图表已成功生成: {output_path}")
