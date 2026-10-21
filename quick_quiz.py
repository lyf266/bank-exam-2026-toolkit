#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业初级资格考试 · 本地全真机考极速自测与历年真题模拟系统 (quick_quiz.py)
特性：
- 零外部依赖（纯 Python 3 标准库）
- 动态直读近三年（2023~2025）全真机考题库（data/past_papers/*.json）
- 支持【全真套卷模考】（按年份/场次选择完整试卷，真实机考计分与及格判定）
- 支持【历年真题抽测】（跨卷随机抽刷 10/20/30/50 题速测）
- 支持【单科专项自测】（《银行业法律法规与综合能力》/《个人理财》）
- 全面融入 2024~2026 金融监管总局改革、民法典物权编、资管新规及 2025 年 1 月最新 M1 口径
- 智能高亮【2026新规校正提示】与【四步直观公式推导（$PV = C / r$）】
- 答错自动沉淀至工作区《错题本_盲区特训账本.md》
"""

import sys
import os
import glob
import json
import argparse
import random
import datetime
import re

from tools.coefficient_table import (
    interactive_coefficient_menu,
    interactive_lookup,
    get_coefficients_all,
    print_table_view
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "past_papers")
MISTAKE_LOG_PATH = os.path.join(BASE_DIR, "错题本_盲区特训账本.md")

# 颜色终端输出辅助
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"

def cprint(text, color=COLOR_RESET, bold=False):
    prefix = COLOR_BOLD if bold else ""
    print(f"{prefix}{color}{text}{COLOR_RESET}")

def load_all_papers():
    """扫描并加载 data/past_papers/ 下全部套卷 JSON"""
    if not os.path.exists(DATA_DIR):
        # 尝试生成
        try:
            from tools.generate_past_papers_json import main as gen_main
            gen_main()
        except Exception:
            pass

    paper_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
    papers = {}
    for pf in paper_files:
        try:
            with open(pf, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "paper_id" in d and "questions" in d:
                    papers[d["paper_id"]] = d
        except Exception as e:
            print(f"⚠️ 读取套卷文件失败 {pf}: {e}")
    return papers

def normalize_ans(ans_str):
    """规范化答案字符串便于对比"""
    s = ans_str.strip().upper()
    if s in ["A", "正确", "对", "T", "TRUE", "1", "√"]:
        return "A"
    if s in ["B", "错误", "错", "F", "FALSE", "0", "×"]:
        return "B"
    # 对于多选题，去除空格并排序，如 "BCA" -> "ABC"
    letters = [c for c in s if c in "ABCDE"]
    letters.sort()
    return "".join(letters)

def record_mistake_to_log(q, user_ans):
    """将错题自动追加沉淀至《错题本_盲区特训账本.md》"""
    if not os.path.exists(MISTAKE_LOG_PATH):
        return False
    try:
        with open(MISTAKE_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否已存在相同题目
        if q["question"][:30] in content:
            return False

        # 查找现有最大 MISTAKE 序号
        existing_nums = [int(m) for m in re.findall(r"MISTAKE-(\d+)", content)]
        next_num = max(existing_nums) + 1 if existing_nums else 1
        mistake_id = f"MISTAKE-{next_num:03d}"
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        # 提取科目简写
        subj_name = "法律法规" if "LAW" in q.get("id", "") or "法规" in q.get("id", "") else "个人理财"
        short_point = q.get("mnemonic", "").split("，")[0].strip() or q["question"][:20]

        # 构造表格行
        new_row = f"| **{mistake_id}** | {subj_name} | {q['type']} | {short_point} | **{q['answer']}** | 🟡 机考自测错题 | {today_str} |\n"

        # 插入到索引表格末尾
        table_end_marker = "\n---"
        if table_end_marker in content:
            idx = content.find(table_end_marker)
            # 找到表格最后一行的换行符
            table_part = content[:idx]
            rest_part = content[idx:]
            content = table_part + new_row + rest_part

        # 构造详情块
        opts_formatted = ""
        for k in sorted(q.get("options", {}).keys()):
            opts_formatted += f"  * {k}. {q['options'][k]}\n"

        new_detail = f"""
---

### 📌 {mistake_id}：{short_point}
* **题型**：{q['type']}
* **题干**：{q['question']}
* **选项**：
{opts_formatted}* **正确答案**：**{q['answer']}**（你的回答：{user_ans}）
* **盲区剖析**：
  * {q.get('explanation', '').replace(chr(10), chr(10) + '  * ')}
* **15字秒杀口诀**：`{q.get('mnemonic', '')}`
* **避坑指南**：{q.get('trap', '')}
"""
        content += new_detail

        with open(MISTAKE_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        return mistake_id
    except Exception as e:
        print(f"⚠️ 记录错题异常: {e}")
        return False

def run_quiz(questions, title="2026 银行从业全真机考极速自测", non_interactive=False, auto_log_mistake=True):
    """
    运行自测/模考引擎
    - 题目展示
    - 智能新规提示
    - 计分与错题自动记录
    """
    total = len(questions)
    if total == 0:
        cprint("⚠️ 题库中没有符合条件的题目！", COLOR_YELLOW)
        return

    cprint("=" * 70, COLOR_CYAN)
    cprint(f"🎯 {title} (本次测试共 {total} 题)", COLOR_CYAN, bold=True)
    cprint("💡 答题说明：单选输入 A/B/C/D；多选输入字母组合如 ABC；判断输入 A(正确)/B(错误)；输入 T 查机考专用系数表；输入 q 退出。", COLOR_YELLOW)
    cprint("=" * 70, COLOR_CYAN)

    score = 0.0
    max_score = 0.0
    correct_count = 0
    wrong_questions = []

    for idx, q in enumerate(questions, 1):
        q_type = q.get("type", "单选题")
        q_id = q.get("id", f"Q-{idx:03d}")
        
        # 分值设定
        if q_type == "多选题":
            weight = 1.0
        elif q_type == "判断题":
            weight = 1.0
        else:
            weight = 0.5
        max_score += weight

        # 题目题头
        print(f"\n【第 {idx}/{total} 题】[{q_type} · {weight}分] ({q_id})")
        
        # 新规提示徽章
        if q.get("is_reformed"):
            cprint("   🚨 [2026新规重点校准题 · 依据国家金融监管总局/2025新版M1口径修订]", COLOR_YELLOW, bold=True)

        print(f"{q['question']}")

        # 打印选项
        opts = q.get("options", {})
        for opt_k in sorted(opts.keys()):
            opt_v = opts[opt_k]
            if opt_v:
                print(f"   {opt_k}. {opt_v}")

        target_ans = q.get("answer", "").strip()
        norm_target = normalize_ans(target_ans)

        if non_interactive:
            user_input = target_ans
            print(f"👉 [流水线测试模式] 自动输入正确答案: {user_input}")
        else:
            prompt_tip = "A/B/C/D"
            if q_type == "多选题":
                prompt_tip = "输入选项组合，如 ABC (多选、少选、错选均不得分)"
            elif q_type == "判断题":
                prompt_tip = "A:正确 / B:错误"

            while True:
                try:
                    user_input = input(f"\n👉 请输入你的选项 ({prompt_tip} | 输入 T 查系数表 | q 退出): ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    print("\n测试已中断。")
                    return
                if user_input in ["T", "TABLE", "TAB", "XS", "XSB", "系数表"]:
                    interactive_coefficient_menu()
                    # 查表完毕后，重新打印题目简要提示，继续让考生作答当前题目
                    print(f"\n【继续作答 第 {idx}/{total} 题】[{q_type} · {weight}分] ({q_id})")
                    print(f"{q['question']}")
                    for opt_k in sorted(opts.keys()):
                        opt_v = opts[opt_k]
                        if opt_v:
                            print(f"   {opt_k}. {opt_v}")
                    continue
                if user_input == "Q":
                    print("\n测试已提前结束。")
                    break
                if user_input:
                    break
                print("⚠️ 输入不能为空，请输入选项字母，或输入 T 查阅机考专用系数表。")

            if user_input == "Q":
                break

        norm_user = normalize_ans(user_input)
        is_correct = (norm_user == norm_target)

        if is_correct:
            cprint(f"✅ 【回答正确！+ {weight}分】", COLOR_GREEN, bold=True)
            score += weight
            correct_count += 1
        else:
            cprint(f"❌ 【回答错误】 正确答案是: {target_ans} (你的选择: {user_input})", COLOR_RED, bold=True)
            wrong_questions.append((q, user_input))
            if auto_log_mistake and not non_interactive:
                mid = record_mistake_to_log(q, user_input)
                if mid:
                    cprint(f"   📌 已自动沉淀至错题特训账本: {mid}", COLOR_YELLOW)

        # 解析与口诀呈现
        print(f"\n💡 【核心考点精析】：\n{q.get('explanation', '暂无解析')}")
        if q.get("mnemonic"):
            cprint(f"🔑 【15字黄金秒杀口诀】：{q['mnemonic']}", COLOR_YELLOW, bold=True)
        if q.get("trap"):
            cprint(f"⚠️ 【机考高频避坑指南】：{q['trap']}", COLOR_CYAN)
        print("-" * 70)

    # 结分报告
    answered_count = idx if user_input != "Q" else idx - 1
    acc = (score / max_score) * 100 if max_score > 0 else 0
    cprint("\n" + "=" * 70, COLOR_CYAN)
    cprint(f"📊 测验完成！总得分：{score:.1f} / {max_score:.1f} 分 (正确率: {acc:.1f}%)", COLOR_BOLD)
    print(f"   • 做题进度: {answered_count} / {total} 题")
    print(f"   • 正确题数: {correct_count} 题 | 错题数: {len(wrong_questions)} 题")

    if max_score >= 60.0:
        if score >= 60.0:
            cprint("🎉 【恭喜通过】得分达到 60 分机考及格线！保持节奏，考场稳过！", COLOR_GREEN, bold=True)
        else:
            cprint(f"⚠️ 【未达合格线】距离 60 分还差 {60.0 - score:.1f} 分，建议集中强化错题账本中的薄弱知识点！", COLOR_RED, bold=True)
    else:
        if acc >= 60.0:
            cprint(f"🟢 正确率 {acc:.1f}% 达到稳过线！", COLOR_GREEN, bold=True)
        else:
            cprint(f"🟠 正确率 {acc:.1f}% 未达 60%，建议多背诵【15字黄金口诀】消除知识盲区。", COLOR_YELLOW, bold=True)
    cprint("=" * 70 + "\n", COLOR_CYAN)

def interactive_menu():
    """主交互菜单"""
    papers = load_all_papers()

    while True:
        cprint("\n" + "=" * 70, COLOR_CYAN)
        cprint("🏦 2026 银行从业初级资格考试 · 本地全真机考极速自测系统", COLOR_CYAN, bold=True)
        cprint("=" * 70, COLOR_CYAN)
        print("1. 🎯 历年全真套卷模考（按年份/场次选择 2023~2025 完整试卷，机考评分）")
        print("2. ⚡ 历年真题极速抽刷（跨卷随机抽 10/20/30 题，快速自测）")
        print("3. 🏛️ 《银行业法律法规与综合能力》（全量真题抽测）")
        print("4. 💰 《个人理财》（全量真题抽测，含 TVM 直观公式推导）")
        print("5. 📖 查阅工作区错题本与盲区特训账本")
        print("6. 📊 官方机考专用系数表与 TVM 速查系统 (全真机考官方附表 · 四大系数)")
        print("0. 退出系统")
        cprint("=" * 70, COLOR_CYAN)

        try:
            choice = input("👉 请选择功能菜单 (0-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！祝备考顺利，60分稳过！")
            break

        if choice == "0":
            print("\n再见！保持每日 45 分钟刷题节奏，通关毫无悬念！")
            break
        elif choice == "1":
            # 套卷选择子菜单
            paper_list = sorted(papers.values(), key=lambda p: (p.get("year", 0), p.get("session", ""), p.get("subject", "")), reverse=True)
            print("\n" + "=" * 70)
            cprint("📋 请选择要进行全真模考的历年试卷：", COLOR_BOLD)
            print("=" * 70)
            for idx, p in enumerate(paper_list, 1):
                reform_flag = " [含2026新规]" if any(q.get("is_reformed") for q in p["questions"]) else ""
                print(f"[{idx:2d}] [{p['year']}-{p['session']}] 《{p['subject']}》 {p['title']} ({p['total_questions']} 题){reform_flag}")
            print("[ 0] 返回上级菜单")
            print("=" * 70)

            sub_choice = input("👉 请输入试卷编号 (0-10): ").strip()
            if sub_choice.isdigit():
                s_idx = int(sub_choice)
                if 1 <= s_idx <= len(paper_list):
                    sel_p = paper_list[s_idx - 1]
                    run_quiz(sel_p["questions"], title=sel_p["title"])
        elif choice == "2":
            # 跨卷随机抽测
            all_qs = []
            for p in papers.values():
                all_qs.extend(p["questions"])
            num_input = input("👉 请输入本次抽测题量 (默认 15 题): ").strip()
            num = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 15
            num = min(num, len(all_qs))
            sample_qs = random.sample(all_qs, num)
            run_quiz(sample_qs, title=f"历年真题跨卷随机抽测 ({num} 题)")
        elif choice == "3":
            # 法律法规
            law_qs = []
            for p in papers.values():
                if "法律法规" in p.get("subject", ""):
                    law_qs.extend(p["questions"])
            num_input = input(f"👉 当前法律法规真题库共 {len(law_qs)} 题，请输入本次抽测题量 (默认 20 题): ").strip()
            num = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 20
            num = min(num, len(law_qs))
            sample_qs = random.sample(law_qs, num)
            run_quiz(sample_qs, title=f"《银行业法律法规与综合能力》专项真题自测 ({num} 题)")
        elif choice == "4":
            # 个人理财
            fin_qs = []
            for p in papers.values():
                if "个人理财" in p.get("subject", ""):
                    fin_qs.extend(p["questions"])
            num_input = input(f"👉 当前个人理财真题库共 {len(fin_qs)} 题，请输入本次抽测题量 (默认 20 题): ").strip()
            num = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 20
            num = min(num, len(fin_qs))
            sample_qs = random.sample(fin_qs, num)
            run_quiz(sample_qs, title=f"《个人理财》专项真题自测 ({num} 题)")
        elif choice == "5":
            if os.path.exists(MISTAKE_LOG_PATH):
                cprint(f"\n📖 正在打开工作区错题本: {MISTAKE_LOG_PATH}", COLOR_GREEN)
                with open(MISTAKE_LOG_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print("".join(lines[:45]))
                print(f"\n... (全文共 {len(lines)} 行，完整内容请在编辑器中查看《错题本_盲区特训账本.md》)")
            else:
                cprint("⚠️ 错题本文件尚不存在。", COLOR_YELLOW)
        elif choice == "6":
            # 官方机考专用系数表
            interactive_coefficient_menu()
        else:
            cprint("⚠️ 无效输入，请输入对应的菜单数字。", COLOR_YELLOW)

def main():
    parser = argparse.ArgumentParser(description="2026 银行从业初级资格考试 · 本地全真机考极速自测与历年真题模拟系统")
    parser.add_argument("--test", action="store_true", help="自动化流水线回归测试模式")
    parser.add_argument("--paper", type=str, default="", help="指定运行的套卷ID (如 2024_06_law)")
    parser.add_argument("--law", action="store_true", help="仅自测《银行业法律法规与综合能力》")
    parser.add_argument("--finance", action="store_true", help="仅自测《个人理财》")
    parser.add_argument("--num", type=int, default=0, help="随机抽取题目数量")
    parser.add_argument("--list", action="store_true", help="列出全部可用试卷与题量统计")
    parser.add_argument("--table", action="store_true", help="查阅官方机考专用系数表与 TVM 速查系统")
    parser.add_argument("--rate", type=float, default=0.0, help="指定利率 (如 5 代表 5%%) 用于快速查系数")
    parser.add_argument("-p", "--period", type=int, default=0, help="指定期数 n (如 5) 用于快速查系数")
    args = parser.parse_args()

    if args.table:
        if args.rate > 0 and args.period > 0:
            data = get_coefficients_all(args.rate, args.period)
            print("\n" + "=" * 68)
            print(f"📊 官方机考专用系数查询结果 (利率: {args.rate}%, 期数: {args.period}):")
            print("=" * 68)
            print(f"  • 复利终值系数 (F/P, {args.rate}%, {args.period}): {data['FP']:.4f}")
            print(f"  • 复利现值系数 (P/F, {args.rate}%, {args.period}): {data['PF']:.4f}")
            print(f"  • 年金终值系数 (F/A, {args.rate}%, {args.period}): {data['FA']:.4f}")
            print(f"  • 年金现值系数 (P/A, {args.rate}%, {args.period}): {data['PA']:.4f}")
            print(f"  • 偿债基金系数 (A/F): {data['sinking_fund']:.4f} | 投资回收系数 (A/P): {data['capital_recovery']:.4f}")
            print("=" * 68 + "\n")
        else:
            interactive_coefficient_menu()
        return

    papers = load_all_papers()

    if args.list:
        print("\n" + "=" * 70)
        print("📚 当前可用历年全真试卷与题量统计")
        print("=" * 70)
        total_q = 0
        for pid, p in sorted(papers.items()):
            cnt = len(p["questions"])
            total_q += cnt
            print(f"• ID: {pid:18s} | [{p['year']}-{p['session']}] 《{p['subject']}》 {p['title']} ({cnt} 题)")
        print(f"\n总计: {len(papers)} 套试卷，{total_q} 道全真试题")
        print("=" * 70)
        return

    # CLI 传参指定运行
    if args.paper:
        if args.paper in papers:
            p = papers[args.paper]
            run_quiz(p["questions"], title=p["title"], non_interactive=args.test)
        else:
            cprint(f"❌ 未找到 ID 为 '{args.paper}' 的套卷。可用套卷列表请运行 python3 quick_quiz.py --list", COLOR_RED)
            sys.exit(1)
        return

    if args.law:
        law_qs = []
        for p in papers.values():
            if "法律法规" in p.get("subject", ""):
                law_qs.extend(p["questions"])
        pool = law_qs
        title = "《银行业法律法规与综合能力》真题自测"
    elif args.finance:
        fin_qs = []
        for p in papers.values():
            if "个人理财" in p.get("subject", ""):
                fin_qs.extend(p["questions"])
        pool = fin_qs
        title = "《个人理财》真题自测"
    else:
        # 如果带有 --test 或 --num 参数，直接运行全量真题库抽测
        if args.test or args.num > 0:
            pool = []
            for p in papers.values():
                pool.extend(p["questions"])
            title = "银行从业全量真题抽测"
        else:
            # 无任何参数，进入主交互式菜单
            interactive_menu()
            return

    if args.num > 0 and args.num < len(pool):
        random.seed(42)
        pool = random.sample(pool, args.num)

    run_quiz(pool, title=title, non_interactive=args.test)

if __name__ == "__main__":
    main()
