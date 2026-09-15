#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业初级资格考试 · 本地高频考点极速自测 CLI (quick_quiz.py)
特性：
- 零外部依赖（纯 Python 3 标准库）
- 100% 同步 Anki 全真机考客观题库（含单选、多选、判断题）
- 依据 2024~2026 金融监管总局、民法典与资管新规编制
- 包含即时判定、考点解析、专属【15字黄金口诀】与【机考避坑指南】
- 支持单选、多选（如输入 ABCD 乱序兼容）、判断题判定
- 支持快速抽测模式（如 --num 10 抽取 10 道题快速刷题）
"""

import sys
import argparse
import random

try:
    from generate_bank_exam_cards import LAW_QUESTIONS, FINANCE_QUESTIONS
except ImportError:
    # 兼容独立运行
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from generate_bank_exam_cards import LAW_QUESTIONS, FINANCE_QUESTIONS

def normalize_ans(ans_str):
    """规范化答案字符串便于对比"""
    s = ans_str.strip().upper()
    if s in ["A", "正确", "对", "T", "TRUE", "1"]:
        return "A"
    if s in ["B", "错误", "错", "F", "FALSE", "0"]:
        return "B"
    # 对于多选题，去除空格并排序，如 "BCA" -> "ABC"
    letters = [c for c in s if c in "ABCDE"]
    letters.sort()
    return "".join(letters)

def run_quiz(questions, non_interactive=False):
    print("=" * 70)
    print(f"🎯 2026 银行从业初级 · 全真机考极速自测启动 (本次测试共 {len(questions)} 题)")
    print("=" * 70)
    
    score = 0
    total = len(questions)
    
    for idx, q in enumerate(questions, 1):
        q_type = q["type"]
        print(f"\n【第 {idx}/{total} 题】[{q_type}] ({q['id']}) {q['question']}")
        
        # 打印选项
        for opt_k in sorted(q["options"].keys()):
            opt_v = q["options"][opt_k]
            if opt_v:
                print(f"   {opt_k}. {opt_v}")
        
        target_ans = q["answer"].strip()
        norm_target = normalize_ans(target_ans)
        
        if non_interactive:
            user_input = target_ans
            print(f"👉 [测试模式] 自动输入正确答案: {user_input}")
        else:
            prompt_tip = "A/B/C/D"
            if q_type == "多选题":
                prompt_tip = "输入选项组合，如 ABC"
            elif q_type == "判断题":
                prompt_tip = "A:正确 / B:错误"
                
            while True:
                try:
                    user_input = input(f"\n👉 请输入你的选项 ({prompt_tip} 或 q 退出): ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    print("\n测试已中断。")
                    return
                if user_input == "Q":
                    print("\n测试已提前结束。")
                    return
                if user_input:
                    break
                print("⚠️ 输入不能为空，请输入对应选项。")
        
        norm_user = normalize_ans(user_input)
        
        is_correct = (norm_user == norm_target)
        if is_correct:
            print("✅ 【回答正确！】")
            score += 1
        else:
            print(f"❌ 【回答错误】 正确答案是: {target_ans}")
            
        print(f"💡 【核心解析】：{q['explanation']}")
        print(f"🔑 【速记口诀】：{q['mnemonic']}")
        if q.get("trap"):
            print(f"⚠️ 【避坑指南】：{q['trap']}")
        print("-" * 70)
        
    print("\n" + "=" * 70)
    acc = (score / total) * 100 if total > 0 else 0
    print(f"🎉 测验完成！得分：{score} / {total} (正确率: {acc:.1f}%)")
    if score == total:
        print("🌟 满分通关！机考高频重点已形成坚实肌肉记忆。")
    elif acc >= 60.0:
        print("🟢 达到 60% 稳过线！继续保持每日 45 分钟刷题节奏，通关毫无悬念。")
    else:
        print("🟠 未达 60% 及格线，建议翻阅解析与【15字黄金口诀】加深记忆。")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="2026 银行从业初级资格考试 · 本地高频极速自测 CLI")
    parser.add_argument("--test", action="store_true", help="自动化流水线测试模式")
    parser.add_argument("--law", action="store_true", help="仅自测《银行业法律法规与综合能力》")
    parser.add_argument("--finance", action="store_true", help="仅自测《个人理财》")
    parser.add_argument("--num", type=int, default=0, help="随机抽取题目数量（默认全量）")
    args = parser.parse_args()

    if args.law:
        pool = list(LAW_QUESTIONS)
    elif args.finance:
        pool = list(FINANCE_QUESTIONS)
    else:
        pool = list(LAW_QUESTIONS + FINANCE_QUESTIONS)

    if args.num > 0 and args.num < len(pool):
        random.seed(42)  # 保持测试可重现
        pool = random.sample(pool, args.num)

    run_quiz(pool, non_interactive=args.test)

if __name__ == "__main__":
    main()
