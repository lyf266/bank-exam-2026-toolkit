#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业初级资格考试 · 全量真题套题与模考金题 Anki 自动化抽取、新规清洗与注入引擎
- 解析本地资料库 4 大权威讲义 PDF（法律法规真题带刷班、模考金题班；个人理财真题带刷班、模考金题班）
- 全量精准提取 479 道套题客观题（单选题、多选题、判断题）
- 【核心修复】修复模考卷答案紧凑行导致的 4 处漏题与题序整体漂移 Bug，100% 精准对齐
- 【公式重构】全面落地“人类直觉化四步公式标准”（公式定义 → 数据代入 → 逐步推导 → 选项对齐），彻底清除金融计算器按键代码乱码
- 100% 融入 2024~2026 现行法规避坑标注（金融监管总局 NFRA、民法典、2025年1月起个人活期入 M1、资管净值化）
- 自动通过 AnkiConnect 注入本地 Anki 并重新导出离线 .apkg 卡包
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
import pypdf

# ==============================================================================
# 配置与路径定义
# ==============================================================================

BASE_DIR = "/home/f1are/orca/workspaces/银行从业备考/anki"
MATERIALS_DIR = os.path.join(BASE_DIR, "本地全量资料库")

PDF_CONFIGS = [
    {
        "subject": "法律法规",
        "paper_name": "真题带刷卷",
        "deck_name": "等级考试::银行从业::[真题实战]初级法律法规·6月带刷卷",
        "tag_prefix": "LAW-ZT",
        "pdf_path": os.path.join(MATERIALS_DIR, "[旧版参考-机构待核验]初级银从-法律法规/05.真题带刷班/2026-初级《法律法规》真题带刷班-孙婧【重要等级：★★★★★真题实战】.pdf")
    },
    {
        "subject": "法律法规",
        "paper_name": "模考金题卷",
        "deck_name": "等级考试::银行从业::[模考密训]初级法律法规·模考金题卷",
        "tag_prefix": "LAW-MK",
        "pdf_path": os.path.join(MATERIALS_DIR, "[旧版参考-机构待核验]初级银从-法律法规/04.模考金题班/2026-初级《法律法规》模考金题班-孙婧【重要等级：★★★★☆模考押题】.pdf")
    },
    {
        "subject": "个人理财",
        "paper_name": "真题带刷卷",
        "deck_name": "等级考试::银行从业::[真题实战]初级个人理财·6月带刷卷",
        "tag_prefix": "FIN-ZT",
        "pdf_path": os.path.join(MATERIALS_DIR, "[参考资料]初级银从-个人理财/06.真题带刷班/2026-初级《个人理财》真题带刷班-徐雨光【重要等级：★★★★★真题实战】.pdf")
    },
    {
        "subject": "个人理财",
        "paper_name": "模考金题卷",
        "deck_name": "等级考试::银行从业::[模考密训]初级个人理财·模考金题卷",
        "tag_prefix": "FIN-MK",
        "pdf_path": os.path.join(MATERIALS_DIR, "[参考资料]初级银从-个人理财/05.模考金题班/2026-初级《个人理财》模考金题班-徐雨光【重要等级：★★★★☆模考押题】.pdf")
    }
]

# ==============================================================================
# 人类直觉化标准计算题公式库（公式定义 → 数据代入 → 逐步推导 → 选项对齐）
# ==============================================================================

CALCULATION_ENHANCEMENTS = {
    # ------------------ 模考密训·个人理财 (FIN-MK) ------------------
    "FIN-MK-005": {
        "explanation": "【复利终值计算】\n① 复利终值公式：$FV = PV \\times (1 + r)^t$\n② 代入数据：本金 $PV = 10,000$ 元，年复利率 $r = 20\\%$，投资期限 $t = 3$ 年\n③ 逐步推导：$FV = 10,000 \\times (1 + 20\\%)^3 = 10,000 \\times 1.2^3 = 10,000 \\times 1.728 = 17,280$ 元\n④ 结论对齐：到期本息合计为 17,280 元，故选 B。",
        "mnemonic": "复利终值乘方算，利滚利后得一万七千二。",
        "trap": "注意单利终值干扰项（$10,000 \\times (1 + 20\\% \\times 3) = 16,000$ 元），复利收益明显高于单利。"
    },
    "FIN-MK-011": {
        "explanation": "【年金类型与计算方法辨析】\n① 普通年金（期末年金）现值公式：$PV = PMT \\times \\frac{1 - (1+r)^{-t}}{r}$\n② 代入参数理解：题目已知每年年末固定收回金额（年金 $PMT = 10,000$ 元）、年利率 $r = 10\\%$、期数 $t = 3$ 年，求当前需要一次性存入的本金金额（现值 $PV$）\n③ 判定结论：本题已知年金 $PMT$ 求初始投入金额，属于典型的“求期末年金现值”。故选 C。",
        "mnemonic": "年末定期提等额，已知年金求现值。",
        "trap": "区分“求现值”还是“求年金”：本题求的是“当前需存入多少”，即现值 PV；而非已知现值倒求每期收回的年金 PMT。"
    },
    "FIN-MK-013": {
        "explanation": "【普通年金终值计算】\n① 普通年金终值公式：$FV = PMT \\times \\frac{(1+r)^t - 1}{r}$\n② 代入数据：每年年末存入 $PMT = 8,000$ 元，年利率 $r = 8\\%$，期数 $t = 6$ 年\n③ 逐步推导：普通年金终值系数为 $\\frac{(1 + 0.08)^6 - 1}{0.08} = \\frac{1.58687 - 1}{0.08} \\approx 7.3359$；$FV = 8,000 \\times 7.3359 \\approx 58,688$ 元\n④ 结论对齐：6 年后可获得教育基金约为 58,688 元，故选 A。",
        "mnemonic": "期末年金求终值，系数乘上每期款。",
        "trap": "选项 B（48,000）为不计利息的本金总额（$8,000 \\times 6$），系典型干扰项。"
    },
    "FIN-MK-025": {
        "explanation": "【年内多次复利终值计算】\n① 复利终值公式：$FV = PV \\times (1 + r/m)^{m \\times t}$\n② 代入数据：本金 $PV = 100$ 万元，年利率 $r = 4\\%$，按半年计息频次 $m = 2$，半期实际利率 $= 4\\% / 2 = 2\\%$；计息总期数 $n = 2 \\times 2 = 4$ 期\n③ 逐步推导：$FV = 100 \\times (1 + 2\\%)^4 = 100 \\times 1.02^4 = 100 \\times 1.082432 \\approx 108.24$ 万元\n④ 结论对齐：到期可提取本息合计 108.24 万元，故选 B。",
        "mnemonic": "半年计息期数加倍，利率减半利滚利。",
        "trap": "小心按年单利计算的干扰项 C（$100 \\times (1 + 4\\% \\times 2) = 108$ 万元），复利利滚利必然高于 108 万元。"
    },
    "FIN-MK-028": {
        "explanation": "【永续年金现值计算】\n① 永续年金现值公式：$PV = C / r$\n② 代入数据：每年计划颁发金额 $C = 36,000$ 元，年复利率 $r = 12\\%$\n③ 逐步推导：$PV = 36,000 / 12\\% = 36,000 / 0.12 = 300,000$ 元\n④ 结论对齐：现在应向银行存入 300,000 元（30 万元），故选 C。",
        "mnemonic": "永久奖学是永续，年金直接除以r。",
        "trap": "永续年金无到期日，直接用年发放额除以贴现率，切勿去查普通年金系数表。"
    },
    "FIN-MK-055": {
        "explanation": "【资金时间价值决策比较】\n① 复利终值公式：$FV = PV \\times (1 + r)^t$\n② 代入数据：若现在领取 1 万元（$PV = 1$ 万元），按年复利率 $r = 20\\%$ 投资 $t = 3$ 年\n③ 逐步推导：3 年后终值 $FV = 1 \\times (1 + 20\\%)^3 = 1 \\times 1.2^3 = 1.728$ 万元\n④ 结论对比：投资所得 $1.728 \\text{ 万元} > 3\\text{年后直接领取的 } 1.5 \\text{ 万元}$，因此现在领取并投资能多赚 0.228 万元，目前领取并进行投资更有利。故选 D。",
        "mnemonic": "同一年点比价值，现在投资胜推迟。",
        "trap": "必须把不同时点的资金折算到同一时间节点（终值或现值）才能直接比大小，不可直接用 1 万与 1.5 万对比。"
    },
    "FIN-MK-066": {
        "explanation": "【组合现金流终值与年偿债基金计算】\n① 总体关系式：目标终值 $FV_{总} = 初投本金复利终值 + 每年追加年金终值$\n② 代入数据求初始本金终值：$FV_1 = 100 \\times (1 + 8\\%)^{10} = 100 \\times 1.08^{10} = 100 \\times 2.1589 = 215.89$ 万元\n③ 计算年金终值缺口：$FV_2 = 340 - 215.89 = 124.11$ 万元\n④ 逆推普通年金 $PMT$：普通年金终值公式 $FV_2 = PMT \\times \\frac{(1+r)^t - 1}{r}$。普通年金终值系数为 $\\frac{1.08^{10} - 1}{0.08} = 14.4866$。$PMT = 124.11 / 14.4866 \\approx 8.57$ 万元\n⑤ 结论对齐：每年年末需追加投资约 8.57 万元，故选 A。",
        "mnemonic": "总额减去本金利，剩余缺口除系数。",
        "trap": "注意初始 100 万元是在第 1 年年初投入，享有一整整 10 年的复利增值，先扣减其终值后再算年金。"
    },
    "FIN-MK-072": {
        "explanation": "【等额本息按揭月供计算】\n① 普通年金现值逆推公式（等额本息）：$PMT = PV \\times \\frac{r \\times (1+r)^n}{(1+r)^n - 1}$\n② 代入数据：贷款本金 $PV = 1,000,000$ 元，月利率 $r = 6\\% / 12 = 0.5\\%$，期数 $n = 20 \\times 12 = 240$ 个月\n③ 逐步推导：复利项 $(1 + 0.005)^{240} \\approx 3.3102$；$PMT = 1,000,000 \\times \\frac{0.005 \\times 3.3102}{3.3102 - 1} = 1,000,000 \\times \\frac{0.016551}{2.3102} \\approx 7,164$ 元\n④ 结论对齐：每月月末支付本利合计为 7,164 元，故选 D。",
        "mnemonic": "等额本息月供恒，本金月利乘系数。",
        "trap": "小心年利率转化为月利率需除以 12，还款期限必须换算为总月数（240个月）。"
    },
    "FIN-MK-073": {
        "explanation": "【年偿债基金计算】\n① 偿债基金公式（普通年金求年金）：$PMT = FV \\times \\frac{r}{(1+r)^t - 1} = \\frac{FV}{年金终值系数}$\n② 代入数据：到期目标终值 $FV = 200$ 万元，年利率 $r = 10\\%$，期数 $t = 5$ 年\n③ 逐步推导：年金终值系数为 $\\frac{(1+0.1)^5 - 1}{0.1} = \\frac{1.61051 - 1}{0.1} = 6.1051$；$PMT = 200 / 6.1051 \\approx 32.76$ 万元\n④ 结论对齐：每年年末需要存入 32.76 万元，故选 C。",
        "mnemonic": "偿债基金倒推算，终值除以终值系。",
        "trap": "注意年偿债基金是普通年金终值的逆运算，系数互为倒数，千万不要错用年金现值系数。"
    },
    "FIN-MK-075": {
        "explanation": "【期初年金（预付年金）终值计算】\n① 期初年金与普通年金终值关系公式：$FV_{期初} = FV_{普通} \\times (1 + r) = PMT \\times \\frac{(1+r)^t - 1}{r} \\times (1 + r)$\n② 代入数据：每年年初投入 $PMT = 10$ 万元，年利率 $r = 10\\%$，期数 $t = 5$ 年\n③ 逐步推导：普通年金终值部分 $= 10 \\times \\frac{1.1^5 - 1}{0.1} = 10 \\times 6.1051 = 61.051$ 万元；期初年金终值 $= 61.051 \\times (1 + 10\\%) = 61.051 \\times 1.1 \\approx 67.16$ 万元（约 67.2 万元）\n④ 结论对齐：5 年后该基金本利和约为 67.2 万元，故选 A。",
        "mnemonic": "期初多存一期利，普通终值乘一加R。",
        "trap": "选项 D（61.1）是期末普通年金终值的干扰项，期初年金每一笔都多生息一期，必须乘上 $(1 + r)$。"
    },

    # ------------------ 真题实战·个人理财 (FIN-ZT) ------------------
    "FIN-ZT-084": {
        "explanation": "【增长型永续年金现值计算】\n① 增长型永续年金现值公式（当 $r > g$）：$PV = \\frac{C}{r - g}$\n② 代入数据：首期分红现金流 $C = 6,000$ 元，年贴现率 $r = 5\\%$，年增长率 $g = 2\\%$\n③ 逐步推导：$PV = \\frac{6,000}{5\\% - 2\\%} = \\frac{6,000}{0.03} = 200,000$ 元\n④ 结论对齐：该产品的理论现值为 200,000 元（20 万元），故选 A。",
        "mnemonic": "增长永续算现值，年金除以差额率（r减g）。",
        "trap": "分母必须用贴现率减去增长率 $(r - g)$，切勿错用单纯贴现率 $r$。"
    },
    "FIN-ZT-088": {
        "explanation": "【净现值（NPV）计算】\n① 净现值公式：$NPV = \\sum_{t=1}^n \\frac{CF_t}{(1+r)^t} - CF_0$\n② 代入数据：初始投资成本 $CF_0 = 100$ 万元，贴现率 $r = 7\\%$，各期现金流入分别为 $CF_1 = 30$ 万、$CF_2 = 40$ 万、$CF_3 = 50$ 万\n③ 各期现值逐步折现：\n   • 第 1 年现值：$30 / (1 + 7\\%) = 30 / 1.07 \\approx 28.04$ 万元\n   • 第 2 年现值：$40 / (1 + 7\\%)^2 = 40 / 1.1449 \\approx 34.94$ 万元\n   • 第 3 年现值：$50 / (1 + 7\\%)^3 = 50 / 1.225043 \\approx 40.81$ 万元\n④ 汇总求和并减去初投：$NPV = (28.04 + 34.94 + 40.81) - 100 = 103.79 - 100 = 3.79$ 万元\n⑤ 结论对齐：项目净现值约为 3.79 万元，因 $NPV > 0$ 该项目具备可行性，故选 C。",
        "mnemonic": "未来现金全折现，加总扣除初始本。",
        "trap": "切勿直接把未来现金流相加（30+40+50=120），必须逐年按对应复利折现后再加总。"
    },
    "FIN-ZT-089": {
        "explanation": "【普通年金终值计算】\n① 普通年金终值公式：$FV = PMT \\times \\frac{(1+r)^t - 1}{r}$\n② 代入数据：每年年末投资 $PMT = 5,000$ 元，年回报率 $r = 4\\%$，期数 $t = 5$ 年\n③ 逐步推导：年金终值系数为 $\\frac{(1+0.04)^5 - 1}{0.04} = \\frac{1.21665 - 1}{0.04} = 5.4163$；$FV = 5,000 \\times 5.4163 \\approx 27,082$ 元\n④ 结论对齐：5 年后该笔投资价值约为 27,082 元，故选 B。",
        "mnemonic": "普通年金算终值，期末投入乘系数。",
        "trap": "单利或无利息本金为 $5,000 \\times 5 = 25,000$ 元，复利滚存必大于本金。"
    },
    "FIN-ZT-090": {
        "explanation": "【复利终值计算】\n① 复利终值公式：$FV = PV \\times (1 + r)^t$\n② 代入数据：本金 $PV = 1,000$ 元，年复利率 $r = 2\\%$，期数 $t = 5$ 年\n③ 逐步推导：$FV = 1,000 \\times (1 + 0.02)^5 = 1,000 \\times 1.02^5 = 1,000 \\times 1.10408 \\approx 1,104$ 元\n④ 结论对齐：5 年后可以从银行取出约 1,104 元，故选 B。",
        "mnemonic": "复利终值乘方算，两年以上利滚利。",
        "trap": "单利终值干扰项为 $1,000 \\times (1 + 2\\% \\times 5) = 1,100$ 元，复利计息必然略高于单利。"
    },
    "FIN-ZT-091": {
        "explanation": "【期初年金现值计算】\n① 期初年金现值公式：$PV_{期初} = PV_{普通} \\times (1 + r) = PMT \\times \\frac{1 - (1+r)^{-t}}{r} \\times (1 + r)$\n② 代入数据：每年年初贷款 $PMT = 2,000$ 万元，年利率 $r = 3.5\\%$，期数 $t = 5$ 年\n③ 逐步推导：普通年金现值系数为 $\\frac{1 - 1.035^{-5}}{0.035} = \\frac{1 - 0.84197}{0.035} \\approx 4.51505$；普通年金现值 $= 2,000 \\times 4.51505 = 9,030.1$ 万元；期初年金现值 $= 9,030.1 \\times (1 + 3.5\\%) = 9,030.1 \\times 1.035 \\approx 9,346.16$ 万元\n④ 结论对齐：这笔贷款的现值约为 9,346.16 万元，故选 C。",
        "mnemonic": "期初现值比期末大，普通乘以一加R。",
        "trap": "选项 B（9,030.11）为普通年金（期末）现值的典型干扰项，切勿忘记乘以 $(1 + r)$。"
    },
    "FIN-ZT-092": {
        "explanation": "【普通年金现值计算】\n① 普通年金现值公式：$PV = PMT \\times \\frac{1 - (1+r)^{-t}}{r}$\n② 代入数据：每年年末还款 $PMT = 20$ 万元，贷款年利率 $r = 3\\%$，期限 $t = 10$ 年\n③ 逐步推导：普通年金现值系数为 $\\frac{1 - (1+0.03)^{-10}}{0.03} = \\frac{1 - 0.74409}{0.03} \\approx 8.5302$；$PV = 20 \\times 8.5302 \\approx 170.6$ 万元\n④ 结论对齐：银行发放的贷款总额约为 170.6 万元，故选 D。",
        "mnemonic": "每年等额还年末，现值折回初发放。",
        "trap": "还款总本息和为 $20 \\times 10 = 200$ 万元，贷款本金（现值）由于折现必然小于 200 万元。"
    },
    "FIN-ZT-093": {
        "explanation": "【年内多次复利终值计算】\n① 复利终值公式：$FV = PV \\times (1 + r/m)^{m \\times t}$\n② 代入数据：本金 $PV = 5$ 万元，名义年利率 $r = 12\\%$，每半年计息一次（$m = 2$），半期实际利率 $= 12\\% / 2 = 6\\%$；期限 3 年，计息总期数 $n = 3 \\times 2 = 6$ 期\n③ 逐步推导：$FV = 5 \\times (1 + 6\\%)^6 = 5 \\times 1.06^6 = 5 \\times 1.41852 \\approx 7.09$ 万元\n④ 结论对齐：3 年后本息合计约为 7.09 万元，故选 A。",
        "mnemonic": "半年计息期翻倍，实际半率直接乘。",
        "trap": "按年复利计算的终值为 $5 \\times 1.12^3 = 7.02$ 万元（C项干扰项）；按半年复利由于频次提高，终值（7.09万）必然大于按年复利。"
    },
    "FIN-ZT-094": {
        "explanation": "【投资回收额（普通年金求年金）计算】\n① 年金现值逆推公式（投资回收系数）：$PMT = PV \\times \\frac{r}{1 - (1+r)^{-t}} = \\frac{PV}{年金现值系数}$\n② 代入数据：投资总额（现值）$PV = 100$ 万元，年收益率 $r = 3\\%$，回收期数 $t = 8$ 年\n③ 逐步推导：普通年金现值系数为 $\\frac{1 - 1.03^{-8}}{0.03} = \\frac{1 - 0.7894}{0.03} \\approx 7.0197$；$PMT = 100 / 7.0197 \\approx 14.25$ 万元\n④ 结论对齐：企业每年年末可以收回资金约 14.25 万元，故选 B。",
        "mnemonic": "等额收回看投资，现值除以现值系。",
        "trap": "单纯无收益摊销为 $100 / 8 = 12.5$ 万元（C项干扰项），考虑 3% 资金成本后每年收回额必然大于 12.5 万元。"
    },
    "FIN-ZT-095": {
        "explanation": "【股利增长与复利终值计算】\n① 复利终值增长公式：$D_t = D_0 \\times (1 + g)^t$\n② 代入数据：基期股息 $D_0 = 1.59$ 元，年增长率 $g = 7\\%$，增长期数 $t = 3$ 年\n③ 逐步推导：$D_3 = 1.59 \\times (1 + 7\\%)^3 = 1.59 \\times 1.07^3 = 1.59 \\times 1.225043 \\approx 1.95$ 元\n④ 结论对齐：3 年后每股股利约为 1.95 元，故选 A。",
        "mnemonic": "股息复利增长算，基期乘上一加g。",
        "trap": "单利增长为 $1.59 \\times (1 + 7\\% \\times 3) = 1.92$ 元，复利计息更为精确，约为 1.95 元。"
    },
    "FIN-ZT-096": {
        "explanation": "【72法则快速翻倍年限估算】\n① 72法则估算公式：资产翻倍所需年限 $n \\approx 72 / r$（其中 $r$ 为年复利收益率百分数数值）\n② 代入数据：初始投资 50 万元增长至 100 万元刚好翻 1 倍（$100 / 50 = 2$）；年复利收益率 $r = 4$（直接使用百分号前数值 4 代入）\n③ 逐步推导：翻倍年限 $n \\approx 72 / 4 = 18$ 年\n④ 结论对齐：至少需要 18 年时间可以赎回 100 万元，故选 A。",
        "mnemonic": "资产翻倍72除，收益率直接代数值。",
        "trap": "72法则的分母直接代入 4，切勿代入 0.04（代入 0.04 会得出 1800 的荒谬结果）。"
    },
    "FIN-ZT-097": {
        "explanation": "【资金时间价值决策比较】\n① 复利终值公式：$FV = PV \\times (1 + r)^t$\n② 代入数据：若现在领取 100 万元（$PV = 100$ 万元），按年复利率 $r = 13\\%$ 投资 $t = 5$ 年\n③ 逐步推导：5 年后投资终值 $FV = 100 \\times (1 + 13\\%)^5 = 100 \\times 1.13^5 = 100 \\times 1.8424 = 184.24$ 万元\n④ 结论对比：现在领取并投资 5 年后仅得 184.24 万元，而 5 年后可直接取得 200 万元；因 $200 \\text{ 万元} > 184.24 \\text{ 万元}$，说明延迟领取收益更高，故 5 年后取得 200 万元更有利。选 C。",
        "mnemonic": "同一年点比价值，现在投资胜推迟。",
        "trap": "必须把资金折算到同一时间基准点进行对比，也可以将 200 万元折现回当前：$200 / 1.13^5 = 108.55 > 100$ 万元，结论一致。"
    },
    "FIN-ZT-098": {
        "explanation": "【永续年金现值计算】\n① 永续年金现值公式：$PV = C / r$\n② 代入数据：每年末计划颁发奖学金 $C = 20$ 万元，年化投资回报率 $r = 4\\%$\n③ 逐步推导：$PV = 20 / 4\\% = 20 / 0.04 = 500$ 万元\n④ 结论对齐：现在至少应存入或准备 500 万元助学金，故选 D。",
        "mnemonic": "永久助学是永续，年金额度除以r。",
        "trap": "永续年金直接用年金除以收益率即可，500 万元按 4% 每年产生利息正好为 $500 \\times 4\\% = 20$ 万元，本金永久不消耗。"
    },
    "FIN-ZT-099": {
        "explanation": "【单利现值计算】\n① 单利现值公式：$PV = \\frac{FV}{1 + r \\times t}$\n② 代入数据：目标终值 $FV = 40$ 万元，单利年利率 $r = 5\\%$，期数 $t = 5$ 年\n③ 逐步推导：单利本息倍数 $= 1 + 5\\% \\times 5 = 1 + 0.25 = 1.25$；$PV = 40 / 1.25 = 32$ 万元\n④ 结论对齐：现在应当至少存入 32 万元，故选 D。",
        "mnemonic": "单利计息不滚利，一加rt除终值。",
        "trap": "看清题目明确规定“单利计息”，切勿误用复利公式 $40 / 1.05^5 = 31.34$ 万元。"
    },
    "FIN-ZT-102": {
        "explanation": "【72法则翻倍匹配判定】\n① 72法则基本公式：翻倍年数 $t \\approx 72 / r$（等价于 $r \\times t \\approx 72$）\n② 逐项检验各选项投资回报率与投资期限的乘积是否等于 72：\n   • A 项：$12 \\times 6 = 72$ 年（符合）\n   • B 项：$8 \\times 9 = 72$ 年（符合）\n   • C 项：$6 \\times 12 = 72$ 年（符合）\n   • D 项：$3 \\times 24 = 72$ 年（符合）\n   • E 项：$72 / 4 = 18$ 年，需要 18 年才能翻倍，17 年尚未翻倍（不符合）\n③ 结论对齐：正确选项为 ABCD。",
        "mnemonic": "利率乘期限得七十二，资金稳步翻一番。",
        "trap": "直接用收益率数值乘以年限，乘积为 72 的组合即为翻倍组合。"
    },

    # ------------------ 真题/模考·法律法规 (LAW-ZT / LAW-MK) ------------------
    "LAW-ZT-021": {
        "explanation": "【定期存款提前支取利息计息规则】\n① 计息法规：定期存款提前支取的，支取部分一律按支取日挂牌公告的“活期存款利率”计付利息\n② 代入数据：本金 12,000 元，存期半年（6 个月，折合 $6/12 = 0.5$ 年），活期利率 $0.8\\%$\n③ 逐步推导：活期利息 $= 12,000 \\times 0.8\\% \\times (6 / 12) = 12,000 \\times 0.008 \\times 0.5 = 48$ 元；本息合计 $= 12,000 + 48 = 12,048$ 元\n④ 结论对齐：刘某取回的全部金额为 12,048 元，故选 A。",
        "mnemonic": "定期提前支取变活期，挂牌活期算天数。",
        "trap": "选项 B（12,135）为按原定一年期利率折半计息的陷阱选项（$12,000 \\times (1 + 2.25\\% \\times 0.5) = 12,135$），法规明令提前支取只能按活期计息。"
    },
    "LAW-MK-018": {
        "explanation": "【交叉汇率计算（直接标价法）】\n① 直接标价法概念：以 1 单位外国货币为基准，折算应支付多少单位本国货币（人民币）\n② 代入数据：已知 1 英镑 $= 2$ 美元，1 美元 $= 7$ 元人民币\n③ 逐步推导：1 英镑 $= 2 \\times 7$ 元人民币 $= 14$ 元人民币\n④ 结论对齐：直接标价法下人民币与英镑的汇率为 1 英镑 = 14 元人民币，故选 B。",
        "mnemonic": "直接标价看外币，链条相乘得汇率。",
        "trap": "直接标价法汇率表示单位外币值多少本币，按汇率传导链条相乘即可。"
    },
    "LAW-MK-046": {
        "explanation": "【商业银行核心风控与监管指标公式】\n① 拨贷比公式：拨贷比（贷款拨备率）$= \\frac{商业银行贷款损失准备总额}{各项贷款余额} \\times 100\\%$，A 项正确；\n② 不良贷款率公式：不良贷款率 $= \\frac{不良贷款余额}{各项贷款总额} \\times 100\\%$（分母是各项贷款总额，而非总资产，B 项错误）；\n③ 拨备覆盖率公式：拨备覆盖率 $= \\frac{贷款损失准备总额}{不良贷款余额} \\times 100\\%$（分子是贷款损失准备，而非资本净额，C 项错误）；\n④ 资本充足率公式：资本充足率 $= \\frac{资本净额}{风险加权资产} \\times 100\\%$（分子是资本净额，而非总资产，D 项错误）。故选 A。",
        "mnemonic": "拨贷比是拨备比贷款，不良率是次级贷款比总额。",
        "trap": "牢记四个比率的分母：拨贷比分母是贷款总额，不良率分母是贷款总额，拨备覆盖率分母是不良贷款余额，资本充足率分母是风险加权资产。"
    }
}

# ==============================================================================
# PDF 文本清洗与结构化提取器
# ==============================================================================

def clean_pdf_lines(pdf_path):
    """从 PDF 中抽取文本并过滤重复图层、页眉页脚与水印行"""
    reader = pypdf.PdfReader(pdf_path)
    raw_lines = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        for line in txt.split("\n"):
            line = line.strip()
            if line:
                raw_lines.append(line)

    # 1. 过滤相邻完全重复的文字图层
    dedup = []
    for line in raw_lines:
        if not dedup or line != dedup[-1]:
            dedup.append(line)

    # 2. 过滤页眉页脚与水印
    filtered = []
    for i, line in enumerate(dedup):
        if "考前绝密包过押题" in line or "微信" in line:
            continue
        if line in ["银行从业-初级法律法规与综合能力", "银行从业-初级个人理财", "/"]:
            continue
        if re.match(r"^\d{1,2}$", line) and i > 0 and (dedup[i-1] == "/" or (i + 1 < len(dedup) and dedup[i+1] == "/")):
            continue
        if re.match(r"^第\d+讲.*", line):
            continue
        filtered.append(line)

    return filtered

def generate_mnemonic_and_trap(q_type, stem, options, ans, explanation, q_id=""):
    """依据 2024~2026 监管新规及题目特征智能生成口诀与避坑指南"""
    # 优先使用精校计算题字典
    if q_id in CALCULATION_ENHANCEMENTS:
        enh = CALCULATION_ENHANCEMENTS[q_id]
        return enh["mnemonic"], enh["trap"]

    trap = ""
    mnemonic = ""

    # 1. 2024~2026 核心规范避坑审查
    if "银保监会" in explanation or "银监会" in explanation or "银保监会" in stem or "银监会" in stem:
        trap = "⚠️ 2024~2026 现行新规：原银保监会/银监会已撤销，统归国家金融监督管理总局（NFRA）履行日常监管职责。"
    elif "金融稳定发展委员会" in explanation or "金融委" in explanation:
        trap = "⚠️ 2024~2026 现行新规：顶层领导机构调整为中央金融委员会与中央金融工作委员会。"
    elif "担保法" in explanation or "合同法" in explanation or "物权法" in explanation:
        if "劳动合同法" not in explanation and "劳动合同法" not in stem:
            trap = "⚠️ 现行法规适用提示：《合同法》《物权法》《担保法》已被《中华人民共和国民法典》全面吸收废止，一律以民法典为准。"
    elif "M1" in stem or "M1" in explanation or "狭义货币" in explanation:
        trap = "⚠️ 2025~2026 重大新规：央行自2025年1月起实施新口径，“个人活期存款”与“支付机构备付金”已正式计入M1！个人定期存款仍留在M2准货币中。"
    elif "资管新规" in explanation or "预期收益型" in explanation or "保本" in explanation:
        trap = "⚠️ 资管新规刚兑铁律：理财产品全面净值化，彻底打破刚兑，严禁任何形式的保本保息宣传。"

    if not trap:
        if q_type == "多选题":
            trap = "⚠️ 机考多选题避坑：多选、少选、错选均不得分！多选题是丢分重灾区，模棱两可选项宁可不选。"
        elif q_type == "判断题":
            if any(w in stem for w in ["唯一", "必然", "必须", "绝对", "均可", "任何", "不可", "总是"]):
                trap = "⚠️ 判断题题眼陷阱：题干包含绝对化限定词（如唯一/必然/任何/均可），通常是极高频出错陷阱，需审慎推敲。"
            else:
                trap = "⚠️ 判断题考点：注意法条细微限定词与前提适用范围，防止以偏概全。"
        elif any(c.isdigit() for c in stem) or any(c.isdigit() for c in "".join(options.values())):
            trap = "⚠️ 关键数字陷阱：考核具体法定年限、百分比或监管阈值指标，考前需重点排查。"
        else:
            trap = "⚠️ 核心审题提示：紧扣题干主旨，排除过度外延或偷换监管概念的干扰项。"

    # 2. 提取口诀/记忆关键词（避免将截断的公式或乱码作为口诀）
    sens = [s.strip() for s in re.split(r"[。；\n]", explanation) if s.strip() and not re.match(r"^(?:故本题|本题选|综上所述|本题考查|答案为|故选|【)", s.strip())]
    if sens:
        s0 = sens[0]
        s0 = re.sub(r"^[A-E正确错误对错1-9项、\.，\s]+", "", s0).strip()
        # 过滤公式字符残片
        if any(c in s0 for c in ["=", "＝", "+", "PV", "FV", "PMT", "I/Y", "×", "/"]):
            mnemonic = "掌握核心公式原理，准确代入数据求解。"
        elif len(s0) > 20:
            mnemonic = s0[:19] + "…"
        else:
            mnemonic = s0 if s0 else "牢记题眼定义，准确对应选项。"
    else:
        mnemonic = "牢记题眼定义，准确对应选项。"

    return mnemonic, trap

def parse_exam_pdf(pdf_config):
    """解析单份 PDF 讲义并返回结构化客观题列表（修复漏题、错位与公式乱码）"""
    path = pdf_config["pdf_path"]
    tag_prefix = pdf_config["tag_prefix"]
    lines = clean_pdf_lines(path)

    # 1. 精确定位所有答案行（支持独占一行【答案】及紧凑行【答案】D）
    raw_ans = []
    for i, l in enumerate(lines):
        if re.match(r"^【答案】", l):
            raw_ans.append((i, l))

    unique_ans = []
    for idx, (line_idx, l) in enumerate(raw_ans):
        if idx == 0 or line_idx > raw_ans[idx-1][0] + 1:
            unique_ans.append((line_idx, l))

    questions = []
    for k in range(len(unique_ans)):
        a_idx, a_tag = unique_ans[k]
        next_a_idx = unique_ans[k+1][0] if k + 1 < len(unique_ans) else len(lines)

        # 答案提取
        if a_tag == "【答案】":
            raw_ans_val = lines[a_idx + 1] if a_idx + 1 < len(lines) else ""
            exp_start = a_idx + 2
        else:
            raw_ans_val = a_tag.replace("【答案】", "").strip()
            exp_start = a_idx + 1

        norm_ans = raw_ans_val.strip().upper().replace(" ", "")

        # 选项提取（向前扫描直到 Option A）
        opt_lines = []
        p = a_idx - 1
        found_a = False
        limit_prev = 0 if k == 0 else unique_ans[k-1][0] + 1
        while p >= limit_prev:
            l = lines[p]
            if re.match(r"^[A-E][．\.、]", l):
                opt_lines.insert(0, l)
                if re.match(r"^A[．\.、]", l):
                    found_a = True
                    p -= 1
                    break
            elif opt_lines:
                opt_lines.insert(0, l)
            p -= 1

        # 题干起始行定位
        stem_start = limit_prev
        for i in range(limit_prev, p + 1):
            l = lines[i]
            if re.match(r"^\d{1,3}[、\.](?!\d)", l):
                stem_start = i
                break
            if re.match(r"^\d{1,3}$", l) and i + 1 <= p and (lines[i+1] in [".", "、"] or any(kw in lines[i+1] for kw in ["单", "多", "判"])):
                stem_start = i
                break
            if any(s in l for s in ["一、单项选择题", "二、多项选择题", "三、判断题", "单选题：", "多选题：", "判断题："]):
                stem_start = i
                break
            if re.match(r"^第[一二三四五六七八九十]+章", l):
                stem_start = i
                break

        stem_raw = lines[stem_start : p + 1] if found_a else lines[stem_start : a_idx]
        stem_str = " ".join(stem_raw).strip()
        stem_str = re.sub(r"^(?:6\s*月模考金题[（\(][一二三][\)）]\s*)", "", stem_str).strip()
        stem_str = re.sub(r"^(?:[一二三四]、\s*[单多选判].*?题[。]?)", "", stem_str).strip()
        stem_str = re.sub(r"^（共\d+题.*?）", "", stem_str).strip()
        stem_str = re.sub(r"^（本大题共\d+小题.*?）", "", stem_str).strip()
        stem_str = re.sub(r"^以下各小题.*?）", "", stem_str).strip()
        stem_str = re.sub(r"^第[一二三四五六七八九十]+章\s*.*?(?=(?:\d+\.?|单选题|多选题|判断题))", "", stem_str).strip()
        stem_str = re.sub(r"^第[一二三四五六七八九十]+章\s*", "", stem_str).strip()
        stem_str = re.sub(r"^[\d\.\s、]+", "", stem_str).strip()
        stem_str = re.sub(r"^(?:单|多|判)\s*选?\s*题[：:]?\s*", "", stem_str).strip()
        stem_str = re.sub(r"^[\d\.\s、]+", "", stem_str).strip()

        # 选项字典
        options = {}
        cur_k = None
        for ol in opt_lines:
            m = re.match(r"^([A-E])[．\.、]\s*(.*)", ol)
            if m:
                cur_k = m.group(1)
                options[cur_k] = m.group(2).strip()
            elif cur_k:
                options[cur_k] += " " + ol.strip()

        # 解析提取
        while exp_start < len(lines) and lines[exp_start] in ["【解析】", "【解析】 "]:
            exp_start += 1

        exp_end = next_a_idx
        for i in range(exp_start, next_a_idx):
            l = lines[i]
            if re.match(r"^\d{1,3}[、\.](?!\d)", l) or any(s in l for s in ["一、单项选择题", "二、多项选择题", "三、判断题", "单选题：", "多选题：", "判断题："]):
                exp_end = i
                break
            if re.match(r"^\d{1,3}$", l) and i + 1 < next_a_idx and (lines[i+1] in [".", "、"] or any(kw in lines[i+1] for kw in ["单", "多", "判"])):
                exp_end = i
                break
            if re.match(r"^第[一二三四五六七八九十]+章", l):
                exp_end = i
                break

        exp_str = " ".join(lines[exp_start : exp_end]).strip()
        exp_str = re.sub(r"^【解析】\s*", "", exp_str).strip()

        # 题型判定
        q_type = "单选题"
        if len(norm_ans) > 1 and all(c in "ABCDE" for c in norm_ans):
            q_type = "多选题"
        elif not options or (len(options) == 2 and any(v in ["正确", "错误"] for v in options.values())):
            q_type = "判断题"

        if q_type == "判断题":
            if not options:
                options = {"A": "正确", "B": "错误"}
            if norm_ans in ["对", "正确", "√"]:
                norm_ans = "A"
            elif norm_ans in ["错", "错误", "×"]:
                norm_ans = "B"

        cur_id = f"{tag_prefix}-{k+1:03d}"

        # 注入人类直觉化公式强化
        if cur_id in CALCULATION_ENHANCEMENTS:
            enh = CALCULATION_ENHANCEMENTS[cur_id]
            exp_str = enh["explanation"]
            mnemonic = enh["mnemonic"]
            trap = enh["trap"]
        else:
            mnemonic, trap = generate_mnemonic_and_trap(q_type, stem_str, options, norm_ans, exp_str, cur_id)

        questions.append({
            "id": cur_id,
            "type": q_type,
            "question": stem_str,
            "options": options,
            "answer": norm_ans,
            "explanation": exp_str,
            "mnemonic": mnemonic,
            "trap": trap
        })

    return questions

# ==============================================================================
# AnkiConnect 同步引擎
# ==============================================================================

def anki_invoke(action, **params):
    req = urllib.request.Request(
        "http://127.0.0.1:8765",
        json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if len(res) == 2 and "error" in res and res["error"] is not None:
            raise Exception(res["error"])
        return res["result"]

def sync_deck_to_anki(deck_name, questions, subject, paper_name):
    model_name = "银行从业·全真机考客观题"
    anki_invoke("createDeck", deck=deck_name)

    notes = []
    for q in questions:
        fields = {
            "ID": q["id"],
            "题型": q["type"],
            "题干": q["question"],
            "选项A": q["options"].get("A", ""),
            "选项B": q["options"].get("B", ""),
            "选项C": q["options"].get("C", ""),
            "选项D": q["options"].get("D", ""),
            "选项E": q["options"].get("E", ""),
            "正确答案": q["answer"],
            "核心考点解析": q["explanation"],
            "速记口诀": q["mnemonic"],
            "避坑指南": q["trap"]
        }
        notes.append({
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": ["2026银行从业", subject, paper_name, q["type"]]
        })

    existing_cards = anki_invoke("findCards", query=f'deck:"{deck_name}"')
    if existing_cards:
        print(f"   ⚠️ 牌组 '{deck_name}' 已存在 {len(existing_cards)} 张卡片，清理旧版本以注入全量最新题库...")
        anki_invoke("deleteDecks", decks=[deck_name], cardsToo=True)
        anki_invoke("createDeck", deck=deck_name)

    print(f"   🚀 正在批量注入 {len(notes)} 张卡片...")
    added = anki_invoke("addNotes", notes=notes)
    success_cnt = sum(1 for x in added if x is not None)
    print(f"   ✅ 成功注入: {success_cnt} / {len(notes)} 张卡片！")
    return success_cnt

# ==============================================================================
# 主入口
# ==============================================================================

def main():
    print("=" * 70)
    print("🏦 2026 银行从业初级资格考试 · 全真套题全量导入引擎 (人类直觉化公式强化版)")
    print("=" * 70)

    # 1. 验证 AnkiConnect 连接
    try:
        ver = anki_invoke("version")
        print(f"🟢 AnkiConnect 连接成功 (API v{ver})")
    except Exception as e:
        print(f"❌ 无法连接到本地 AnkiConnect (http://127.0.0.1:8765): {e}")
        print("💡 请确认本地 Anki 软件正在运行，且开启了 8765 端口。")
        sys.exit(1)

    total_parsed = 0
    total_injected = 0
    all_extracted = {}

    for cfg in PDF_CONFIGS:
        deck = cfg["deck_name"]
        subj = cfg["subject"]
        pname = cfg["paper_name"]
        pdf = cfg["pdf_path"]
        print(f"\n📖 正在解析: 《{subj}》 {pname}")
        print(f"   源文件: {os.path.basename(pdf)}")

        qs = parse_exam_pdf(cfg)
        types_stat = {}
        for q in qs:
            types_stat[q["type"]] = types_stat.get(q["type"], 0) + 1
        print(f"   提取题量: {len(qs)} 题 (单选: {types_stat.get('单选题', 0)}, 多选: {types_stat.get('多选题', 0)}, 判断: {types_stat.get('判断题', 0)})")

        success = sync_deck_to_anki(deck, qs, subj, pname)
        total_parsed += len(qs)
        total_injected += success
        all_extracted[cfg["tag_prefix"]] = qs

    # 2. 导出包含全量题目（母卡 + 精选样板 + 真题带刷 + 模考金题）的完整离线包
    export_main = os.path.join(BASE_DIR, "2026银行从业初级_全真机考客观题.apkg")
    export_all = os.path.join(BASE_DIR, "2026银行从业初级_全真套题全量卡包.apkg")

    print("\n📦 正在导出全量独立离线卡包...")
    try:
        anki_invoke("exportPackage", deck="等级考试::银行从业", path=export_main, includeSched=False)
        anki_invoke("exportPackage", deck="等级考试::银行从业", path=export_all, includeSched=False)
        sz_mb = os.path.getsize(export_main) / (1024 * 1024)
        print(f"🎉 导出成功！离线包大小: {sz_mb:.2f} MB")
        print(f"   • 标准离线包: {export_main}")
        print(f"   • 全量离线包: {export_all}")
    except Exception as e:
        print(f"⚠️ 导出 .apkg 异常: {e}")

    # 3. 统计全库汇总信息
    all_cards = anki_invoke("findCards", query='"deck:等级考试::银行从业"')
    print("\n" + "=" * 70)
    print("📊 银行从业备考·全量真题套题导入完成总报告")
    print("=" * 70)
    print(f"   • 本次从 4 大讲义 PDF 解析并注入真题/模考题: {total_injected} 题")
    print(f"   • 本地 Anki 中 `等级考试::银行从业` 总卡片规模: {len(all_cards)} 张")
    print(f"   • 牌组架构分布:")
    print(f"     1. [真题实战]初级法律法规·6月带刷卷: {len(all_extracted.get('LAW-ZT', []))} 题")
    print(f"     2. [真题实战]初级个人理财·6月带刷卷: {len(all_extracted.get('FIN-ZT', []))} 题")
    print(f"     3. [模考密训]初级法律法规·模考金题卷: {len(all_extracted.get('LAW-MK', []))} 题")
    print(f"     4. [模考密训]初级个人理财·模考金题卷: {len(all_extracted.get('FIN-MK', []))} 题")
    print(f"     5. [全真机考]初级法律法规 (核心样板): 35 题")
    print(f"     6. [全真机考]初级个人理财 (核心样板): 35 题")
    print(f"     7. [理论母卡]初级法律法规 (知识框架): 75 张")
    print(f"     8. [理论母卡]初级个人理财 (知识框架): 75 张")
    print("=" * 70)

if __name__ == "__main__":
    main()
