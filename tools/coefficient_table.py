#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行从业初级资格考试 · 官方机考专用系数表与货币时间价值 (TVM) 检索引擎
(tools/coefficient_table.py)

参考标准：
- 中国银行业专业人员职业资格考试（东方银行业高级管理人员研修院 / ATA 机考系统）
- 《个人理财》（初级/中级）官方教材附表与机考系统内置数据规范

四大核心系数附表：
1. 附表一：复利终值系数表 FVIF (F/P, r, n) = (1 + r)^n
2. 附表二：复利现值系数表 PVIF (P/F, r, n) = (1 + r)^(-n)
3. 附表三：年金终值系数表 FVIFA (F/A, r, n) = [(1 + r)^n - 1] / r
4. 附表四：年金现值系数表 PVIFA (P/A, r, n) = [1 - (1 + r)^(-n)] / r
"""

import sys
import os
import math

# 官方机考基准利率梯度 (%)
OFFICIAL_RATES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0, 15.0, 16.0, 18.0, 20.0]

# 官方机考基准期数梯度 (年/期)
OFFICIAL_PERIODS = list(range(1, 21)) + [25, 30]

# 终端高亮着色代码
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"

def calc_fp(r_dec, n):
    """复利终值系数 (F/P, r, n) = (1 + r)^n"""
    return (1.0 + r_dec) ** n

def calc_pf(r_dec, n):
    """复利现值系数 (P/F, r, n) = (1 + r)^(-n)"""
    return (1.0 + r_dec) ** (-n)

def calc_fa(r_dec, n):
    """普通年金终值系数 (F/A, r, n) = [(1 + r)^n - 1] / r"""
    if abs(r_dec) < 1e-9:
        return float(n)
    return ((1.0 + r_dec) ** n - 1.0) / r_dec

def calc_pa(r_dec, n):
    """普通年金现值系数 (P/A, r, n) = [1 - (1 + r)^(-n)] / r"""
    if abs(r_dec) < 1e-9:
        return float(n)
    return (1.0 - (1.0 + r_dec) ** (-n)) / r_dec

COEFF_CALC_MAP = {
    "FP": ("复利终值系数 (F/P, r, n)", calc_fp, "已知现值 PV 求终值 FV = PV × (F/P, r, n)"),
    "PF": ("复利现值系数 (P/F, r, n)", calc_pf, "已知终值 FV 求现值 PV = FV × (P/F, r, n)"),
    "FA": ("年金终值系数 (F/A, r, n)", calc_fa, "已知每期等额年金 A 求终值 FV = A × (F/A, r, n)"),
    "PA": ("年金现值系数 (P/A, r, n)", calc_pa, "已知每期等额年金 A 求现值 PV = A × (P/A, r, n)")
}

def get_coefficients_all(r_pct, n):
    """计算给定利率 (%) 和期数 n 下的全部 4 大系数及核心换算数据"""
    r_dec = float(r_pct) / 100.0
    fp = calc_fp(r_dec, n)
    pf = calc_pf(r_dec, n)
    fa = calc_fa(r_dec, n)
    pa = calc_pa(r_dec, n)
    
    # 互为倒数的衍生系数
    sinking_fund = 1.0 / fa if fa != 0 else 0.0  # 偿债基金系数 (A/F)
    capital_recovery = 1.0 / pa if pa != 0 else 0.0  # 投资回收系数 (A/P)
    
    # 先付年金系数 (期初年金)
    due_fa = fa * (1.0 + r_dec)
    due_pa = pa * (1.0 + r_dec)

    return {
        "r_pct": r_pct,
        "n": n,
        "FP": round(fp, 4),
        "PF": round(pf, 4),
        "FA": round(fa, 4),
        "PA": round(pa, 4),
        "sinking_fund": round(sinking_fund, 4),
        "capital_recovery": round(capital_recovery, 4),
        "due_FA": round(due_fa, 4),
        "due_PA": round(due_pa, 4),
    }

def print_table_view(coeff_type="PF", rate_group=1):
    """
    在终端分页整齐输出官方机考系数表格
    rate_group:
      1: 1% ~ 5%
      2: 6% ~ 10%
      3: 12% ~ 20%
    """
    if coeff_type not in COEFF_CALC_MAP:
        coeff_type = "PF"

    name, func, usage = COEFF_CALC_MAP[coeff_type]

    if rate_group == 1:
        rates = [1.0, 2.0, 3.0, 4.0, 5.0]
        group_label = "【第 1 组：1% ~ 5% 常用温和利率档】"
    elif rate_group == 2:
        rates = [6.0, 7.0, 8.0, 9.0, 10.0]
        group_label = "【第 2 组：6% ~ 10% 核心高频利率档】"
    else:
        rates = [12.0, 14.0, 15.0, 16.0, 18.0, 20.0]
        group_label = "【第 3 组：12% ~ 20% 高收益/高贴现利率档】"

    print("\n" + "=" * 76)
    print(f"{COLOR_BOLD}{COLOR_CYAN}🏛️ 官方机考专用系数表 · {name}{COLOR_RESET}")
    print(f"{COLOR_YELLOW}📌 用途：{usage}{COLOR_RESET}")
    print(f"{COLOR_CYAN}📊 范围：{group_label} (保留4位小数，与官方机考系统完全一致){COLOR_RESET}")
    print("-" * 76)

    # 打印表头
    header = f"{'期数(n)':^9} | " + " | ".join([f"{int(r) if r.is_integer() else r:>5}%" for r in rates])
    print(f"{COLOR_BOLD}{header}{COLOR_RESET}")
    print("-" * 76)

    # 打印各期数据
    for n in OFFICIAL_PERIODS:
        row_vals = []
        for r in rates:
            val = func(r / 100.0, n)
            row_vals.append(f"{val:>6.4f}")
        row_str = f"  n={n:<3d}   | " + " | ".join(row_vals)
        # 高亮重点年限 (3年, 5年, 10年, 20年)
        if n in [3, 5, 10, 20]:
            print(f"{COLOR_GREEN}{row_str}{COLOR_RESET}")
        else:
            print(row_str)

    print("=" * 76)

def interactive_lookup():
    """交互式精确定位快速查表器"""
    print("\n" + "=" * 68)
    print(f"{COLOR_BOLD}{COLOR_CYAN}🔍 官方机考专用四大系数 · 交互式快速精确定位查询{COLOR_RESET}")
    print("=" * 68)
    try:
        r_input = input("👉 请输入年利率/折现率 r (如 5 代表 5%，支持小数如 5.5): ").strip()
        if not r_input:
            return
        r_val = float(r_input)

        n_input = input("👉 请输入计息期数 n (如 3 或 5 年): ").strip()
        if not n_input:
            return
        n_val = int(n_input)
    except ValueError:
        print(f"{COLOR_RED}⚠️ 输入格式有误，请输入合法数字。{COLOR_RESET}")
        return

    data = get_coefficients_all(r_val, n_val)
    print("\n" + "-" * 68)
    print(f"{COLOR_BOLD}📊 查询结果：当利率 r = {r_val}%，期数 n = {n_val} 期时：{COLOR_RESET}")
    print("-" * 68)
    print(f"  1. 复利终值系数 (F/P, {r_val}%, {n_val}) = {COLOR_GREEN}{data['FP']:<8.4f}{COLOR_RESET}  [推导: (1+{r_val}%)^{n_val}]")
    print(f"  2. 复利现值系数 (P/F, {r_val}%, {n_val}) = {COLOR_GREEN}{data['PF']:<8.4f}{COLOR_RESET}  [推导: (1+{r_val}%)^-{n_val}，与终值互为倒数]")
    print(f"  3. 年金终值系数 (F/A, {r_val}%, {n_val}) = {COLOR_GREEN}{data['FA']:<8.4f}{COLOR_RESET}  [推导: ((1+{r_val}%)^{n_val}-1)/{r_val}%]")
    print(f"  4. 年金现值系数 (P/A, {r_val}%, {n_val}) = {COLOR_GREEN}{data['PA']:<8.4f}{COLOR_RESET}  [推导: (1-(1+{r_val}%)^-{n_val})/{r_val}%]")
    print("  " + "·" * 60)
    print(f"  💡 衍生系数 (机考常考辨析):")
    print(f"     • 偿债基金系数 (A/F) = {data['sinking_fund']:.4f} (年金终值倒数)")
    print(f"     • 投资回收系数 (A/P) = {data['capital_recovery']:.4f} (年金现值倒数)")
    print(f"     • 期初/先付年金终值系数 = {data['due_FA']:.4f} (期末系数 × (1+{r_val}%))")
    print(f"     • 期初/先付年金现值系数 = {data['due_PA']:.4f} (期末系数 × (1+{r_val}%))")
    print("-" * 68)

    # 快捷金额代入计算
    amt_input = input("👉 是否代入具体金额一键计算? (输入本金/年金金额，直接回车跳过): ").strip()
    if amt_input:
        try:
            amt = float(amt_input.replace(",", ""))
            print("\n" + "·" * 68)
            print(f"💰 【金额一键换算】基于投入基数: {amt:,.2f} 元")
            print(f"  • 一次性投入，{n_val} 年后复利本利和 (FV): {amt * data['FP']:,.2f} 元")
            print(f"  • 未来获得该款项，折算到现在现值 (PV): {amt * data['PF']:,.2f} 元")
            print(f"  • 每年年末存入该金额，{n_val} 年后年金总终值 (FVA): {amt * data['FA']:,.2f} 元")
            print(f"  • 每年年末获得该金额，折算到现在总现值 (PVA): {amt * data['PA']:,.2f} 元")
            print("·" * 68)
        except ValueError:
            pass

def interactive_coefficient_menu():
    """系数表主呼出菜单（支持自测作答中随时呼出）"""
    while True:
        print("\n" + "=" * 70)
        print(f"{COLOR_BOLD}{COLOR_CYAN}🏛️ 2026 银行从业机考 · 官方全真考试专用系数表系统{COLOR_RESET}")
        print("=" * 70)
        print("1. 📉 复利现值系数表 (P/F, r, n)  [折现求现值 · 最常考]")
        print("2. 📈 复利终值系数表 (F/P, r, n)  [利滚利求未来终值]")
        print("3. 💶 普通年金现值系数表 (P/A, r, n) [分期等额现金流折现现值]")
        print("4. 💰 普通年金终值系数表 (F/A, r, n) [定期定额定投本利和]")
        print("5. 🔍 交互式精确定位快速查表 (输入任意 r 和 n 秒出结果与代入计算)")
        print("6. 🔑 考点核心转换法则与倒数速记口诀")
        print("0. 🔙 返回系统 / 继续作答题目")
        print("=" * 70)

        try:
            choice = input("👉 请选择要查阅的系数表或功能 (0-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "0" or not choice:
            print("🔙 正在返回...")
            break
        elif choice == "1":
            _show_table_sub_menu("PF")
        elif choice == "2":
            _show_table_sub_menu("FP")
        elif choice == "3":
            _show_table_sub_menu("PA")
        elif choice == "4":
            _show_table_sub_menu("FA")
        elif choice == "5":
            interactive_lookup()
        elif choice == "6":
            _show_rules_and_mnemonics()
        else:
            print("⚠️ 无效输入，请输入 0-6。")

def _show_table_sub_menu(coeff_type):
    name = COEFF_CALC_MAP[coeff_type][0]
    while True:
        print(f"\n📊 正在查看：{name}")
        print("  [1] 查看利率 1% ~ 5% 档位 (常用稳健/公积金/存款利率)")
        print("  [2] 查看利率 6% ~ 10% 档位 (核心机考题高频题眼利率)")
        print("  [3] 查看利率 12% ~ 20% 档位 (高贴现率/权益投资利率)")
        print("  [0] 返回上级菜单")
        sub = input("  👉 请选择利率档位 (1-3 或 0 返回): ").strip()
        if sub == "0" or not sub:
            break
        if sub in ["1", "2", "3"]:
            print_table_view(coeff_type, int(sub))
        else:
            print("⚠️ 请输入 1, 2, 3 或 0。")

def _show_rules_and_mnemonics():
    print("\n" + "=" * 70)
    print(f"{COLOR_BOLD}{COLOR_YELLOW}🔑 官方机考系数四大核心考点与倒数转换速记秘籍{COLOR_RESET}")
    print("=" * 70)
    print(f"""
1. 【三大互为倒数关系（机考判断题/多选题必考）】
   • 复利终值系数 (F/P) × 复利现值系数 (P/F) = 1
   • 普通年金终值系数 (F/A) × 偿债基金系数 (A/F) = 1
   • 普通年金现值系数 (P/A) × 投资回收系数 (A/P) = 1
   👉 15字秒杀口诀：`终现互倒年金配，偿债配终收配现。`

2. 【期初年金 (先付年金) 与 期末年金 (后付年金) 的换算】
   • 核心规律：每一笔资金都比期末多计息 1 期，因此直接乘以 (1 + r)！
   • 先付年金终值公式：FV_due = FV_ordinary × (1 + r) = A × [(F/A, r, n+1) - 1]
     👉 口诀：`期初终值期数加一、系数减一`
   • 先付年金现值公式：PV_due = PV_ordinary × (1 + r) = A × [(P/A, r, n-1) + 1]
     👉 口诀：`期初现值期数减一、系数加一`

3. 【永续年金现值秒杀公式】
   • 永续年金现值：PV = C / r  (每年固定分红 C，除以折现率 r，直接除出来！)
   • 增长型永续年金：PV = C1 / (r - g) (分母为贴现率减去恒定增长率)

4. 【72法则极速估算复利翻倍年限】
   • 投资翻一番所需年限 t ≈ 72 / (r × 100)
   • 例：年利率 8% 翻倍约需：72 / 8 = 9 年 (查表精确值 (1+8%)^9 = 1.9990 ≈ 2)
""")
    print("=" * 70)

def generate_markdown_doc():
    """生成工作区规范的 Markdown 专用系数表文档"""
    md = [
        "# 📊 2026 银行从业初级资格考试 · 官方机考专用系数速查表与货币时间价值全景手册\n",
        "> **官方考试标准对齐**：完全依据中国银行业专业人员职业资格机考系统（ATA系统）与《个人理财》教材附表编订。四位小数精准四舍五入，支持考场查表与极速口诀秒杀。\n",
        "---\n",
        "## 📑 目录索引",
        "- [一、附表一：复利终值系数表 (F/P, r, n)](#一附表一复利终值系数表-fpr-n)",
        "- [二、附表二：复利现值系数表 (P/F, r, n)](#二附表二复利现值系数表-pfr-n)",
        "- [三、附表三：普通年金终值系数表 (F/A, r, n)](#三附表三普通年金终值系数表-far-n)",
        "- [四、附表四：普通年金现值系数表 (P/A, r, n)](#四附表四普通年金现值系数表-par-n)",
        "- [五、官方机考高频换算与秒杀秘籍（倒数/先付年金/永续年金）](#五官方机考高频换算与秒杀秘籍)\n",
        "---\n"
    ]

    rates_part1 = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    rates_part2 = [9.0, 10.0, 12.0, 14.0, 15.0, 16.0, 18.0, 20.0]

    tables_info = [
        ("一、附表一：复利终值系数表 (F/P, r, n)", "FP", "求未来本利和：$FV = PV \\times (1 + r)^n$"),
        ("二、附表二：复利现值系数表 (P/F, r, n)", "PF", "求折现现值：$PV = FV \\times (1 + r)^{-n}$"),
        ("三、附表三：普通年金终值系数表 (F/A, r, n)", "FA", "求定期定额累积终值：$FV = A \\times \\frac{(1 + r)^n - 1}{r}$"),
        ("四、附表四：普通年金现值系数表 (P/A, r, n)", "PA", "求定期等额收付总现值：$PV = A \\times \\frac{1 - (1 + r)^{-n}}{r}$")
    ]

    for title, code, formula in tables_info:
        func = COEFF_CALC_MAP[code][1]
        md.append(f"## {title}\n")
        md.append(f"> **核心公式**：{formula}\n")

        # 利率梯队 1
        md.append(f"### 利率 1% ~ 8%\n")
        header1 = "| 期数 ($n$) | " + " | ".join([f"{int(r)}%" for r in rates_part1]) + " |"
        sep1 = "| :---: | " + " | ".join([":---:" for _ in rates_part1]) + " |"
        md.append(header1)
        md.append(sep1)
        for n in OFFICIAL_PERIODS:
            row = [f"**{n}**"] + [f"{func(r/100.0, n):.4f}" for r in rates_part1]
            md.append("| " + " | ".join(row) + " |")
        md.append("\n")

        # 利率梯队 2
        md.append(f"### 利率 9% ~ 20%\n")
        header2 = "| 期数 ($n$) | " + " | ".join([f"{int(r)}%" for r in rates_part2]) + " |"
        sep2 = "| :---: | " + " | ".join([":---:" for _ in rates_part2]) + " |"
        md.append(header2)
        md.append(sep2)
        for n in OFFICIAL_PERIODS:
            row = [f"**{n}**"] + [f"{func(r/100.0, n):.4f}" for r in rates_part2]
            md.append("| " + " | ".join(row) + " |")
        md.append("\n---\n")

    md.append("""## 五、官方机考高频换算与秒杀秘籍

### 1. 三大互为倒数关系（机考判断题/多选题必考）
* **复利终值系数** 与 **复利现值系数** 互为倒数：
  $$(F/P, r, n) \\times (P/F, r, n) = 1$$
* **普通年金终值系数** 与 **偿债基金系数** 互为倒数：
  $$(F/A, r, n) \\times (A/F, r, n) = 1 \\implies (A/F, r, n) = \\frac{1}{(F/A, r, n)}$$
* **普通年金现值系数** 与 **投资回收系数** 互为倒数：
  $$(P/A, r, n) \\times (A/P, r, n) = 1 \\implies (A/P, r, n) = \\frac{1}{(P/A, r, n)}$$
* 🔑 **15字速记口诀**：`终现互倒年金配，偿债配终收配现。`

### 2. 期初年金（先付年金）换算
* **期初年金终值**：
  $$FV_{\\text{due}} = FV_{\\text{ordinary}} \\times (1 + r) = A \\times \\left[ (F/A, r, n+1) - 1 \\right]$$
  *(口诀：期数加 1，系数减 1)*
* **期初年金现值**：
  $$PV_{\\text{due}} = PV_{\\text{ordinary}} \\times (1 + r) = A \\times \\left[ (P/A, r, n-1) + 1 \\right]$$
  *(口诀：期数减 1，系数加 1)*

### 3. 永续年金现值秒杀
* **标准永续年金**：$$PV = \\frac{C}{r}$$
* **增长型永续年金**：$$PV = \\frac{C_1}{r - g}$$
""")

    return "\n".join(md)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--export-md":
        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "官方机考专用系数速查表.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(generate_markdown_doc())
        print(f"✅ 已成功生成官方机考专用系数速查表: {out_path}")
    else:
        interactive_coefficient_menu()
