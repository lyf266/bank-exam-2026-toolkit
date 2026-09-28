#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tools/generate_past_papers_json.py

银行从业资格考试 · 近三年（2023~2025）全真题库结构化生成与新规校准流水线
- 提取 2024 年 4 套完整官方真题与押题密训卷（共 479 题）
- 汇编 2023 年历次机考回忆真题卷（2023-06, 2023-10）
- 编制 2025 年最新大纲（含 2025 年 1 月个人活期纳入 M1、金监总局最新制度）全真试卷
- 运行 2026 新规审校 Linter（双重视角对比提示 + 四步直观公式推导）
- 输出标准 JSON 题库至 data/past_papers/ 目录
"""

import os
import sys
import json
import re

# 引入已有的 PDF 解析与计算公式库
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from import_all_exam_papers import parse_exam_pdf, PDF_CONFIGS, CALCULATION_ENHANCEMENTS

OUTPUT_DIR = os.path.join(BASE_DIR, "data", "past_papers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def reform_linter(question_item):
    """
    智能 2026 新规校准与双重视角标注器
    - 检查'银保监会'/'银监会' -> 标注金融监管总局新规
    - 检查 M1/个人活期 -> 标注 2025 年 1 月最新口径
    - 检查刚兑理财 -> 标注净值化转型
    """
    stem = question_item["question"]
    exp = question_item.get("explanation", "")
    trap = question_item.get("trap", "")
    opts_str = " ".join(question_item.get("options", {}).values())
    all_text = f"{stem} {exp} {trap} {opts_str}"

    is_reformed = False
    notes = []

    # 1. 监管机构新规
    if any(k in all_text for k in ["银保监会", "银监会", "保监会", "银保监局", "银监局", "中国银行保险监督管理委员会"]):
        is_reformed = True
        notes.append("【2026新规校正提示】党和国家机构改革后，中国银保监会已撤销，统一由国家金融监督管理总局（NFRA）行使银行与保险业监管职责。")

    # 2. 货币供应量 M1 新口径 (2025年1月生效)
    if any(k in all_text for k in ["M1", "狭义货币", "准货币"]) and any(k in all_text for k in ["活期", "个人存款", "居民"]):
        is_reformed = True
        notes.append("【2026新规校正提示】中国人民银行自 2025 年 1 月起修订 M1 统计口径：个人活期存款和非银行支付机构客户备付金已正式纳入 M1！个人定期存款仍属于 M2 准货币。")

    # 3. 资管新规全面净值化
    if any(k in all_text for k in ["预期收益型", "保本保息", "打破刚兑", "刚兑"]):
        is_reformed = True
        notes.append("【2026新规校正提示】资管新规已全面落地，银行理财彻底打破刚兑、实行全面净值化，严禁承诺保本保息。")

    # 4. 民法典替换旧法
    if any(k in all_text for k in ["物权法", "担保法", "合同法", "继承法"]):
        is_reformed = True
        notes.append("【2026新规校正提示】原《物权法》《担保法》《合同法》《继承法》已被《中华人民共和国民法典》全面吸收并废止，现统一适用《民法典》。")

    if is_reformed and notes:
        combined_note = "\n".join(notes)
        if combined_note not in exp:
            question_item["explanation"] = exp + "\n\n💡 " + combined_note
        if not trap:
            question_item["trap"] = combined_note
        elif combined_note not in trap:
            question_item["trap"] = trap + " " + combined_note
        question_item["is_reformed"] = True
    else:
        question_item["is_reformed"] = False

    return question_item

def build_2024_papers():
    """解析并生成 2024 年 4 套核心真题与密训卷"""
    print("📦 正在解析并生成 2024 年全真试卷...")

    paper_meta_map = {
        "LAW-ZT": {
            "paper_id": "2024_06_law",
            "title": "2024年6月初级《银行业法律法规与综合能力》全真机考真题卷",
            "subject": "银行业法律法规与综合能力",
            "year": 2024,
            "session": "06月",
            "source": "官方机考学员真题带刷卷"
        },
        "LAW-MK": {
            "paper_id": "2024_10_law",
            "title": "2024年下半年初级《银行业法律法规与综合能力》全真模考金题卷",
            "subject": "银行业法律法规与综合能力",
            "year": 2024,
            "session": "10月",
            "source": "考前押题密训全真卷"
        },
        "FIN-ZT": {
            "paper_id": "2024_06_finance",
            "title": "2024年6月初级《个人理财》全真机考真题卷",
            "subject": "个人理财",
            "year": 2024,
            "session": "06月",
            "source": "官方机考学员真题带刷卷"
        },
        "FIN-MK": {
            "paper_id": "2024_10_finance",
            "title": "2024年下半年初级《个人理财》全真模考金题卷",
            "subject": "个人理财",
            "year": 2024,
            "session": "10月",
            "source": "考前押题密训全真卷"
        }
    }

    results = {}
    for cfg in PDF_CONFIGS:
        prefix = cfg["tag_prefix"]
        if prefix not in paper_meta_map:
            continue
        meta = paper_meta_map[prefix]
        print(f"   • 解析 {meta['title']} (PDF: {os.path.basename(cfg['pdf_path'])})")
        raw_qs = parse_exam_pdf(cfg)
        calibrated_qs = [reform_linter(q) for q in raw_qs]

        paper_data = {
            "paper_id": meta["paper_id"],
            "title": meta["title"],
            "subject": meta["subject"],
            "year": meta["year"],
            "session": meta["session"],
            "source": meta["source"],
            "total_questions": len(calibrated_qs),
            "questions": calibrated_qs
        }
        out_path = os.path.join(OUTPUT_DIR, f"{meta['paper_id']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(paper_data, f, ensure_ascii=False, indent=2)
        print(f"     ✅ 已写入 {out_path}，包含 {len(calibrated_qs)} 题")
        results[meta["paper_id"]] = paper_data

    return results

def build_2023_2025_papers():
    """解析并生成 2023 与 2025 年各场次机考回忆与新考纲密训卷"""
    from tools.data_source_2023_2025 import PAPERS_2023_2025

    print("\n📦 正在生成 2023 与 2025 年历次机考回忆与最新大纲试卷...")
    results = {}

    for paper_id, data in PAPERS_2023_2025.items():
        title = data["title"]
        print(f"   • 处理 {title} ({paper_id})")
        qs = [reform_linter(q) for q in data["questions"]]

        paper_data = {
            "paper_id": data["paper_id"],
            "title": data["title"],
            "subject": data["subject"],
            "year": data["year"],
            "session": data["session"],
            "source": data["source"],
            "total_questions": len(qs),
            "questions": qs
        }

        out_path = os.path.join(OUTPUT_DIR, f"{paper_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(paper_data, f, ensure_ascii=False, indent=2)
        print(f"     ✅ 已写入 {out_path}，包含 {len(qs)} 题")
        results[paper_id] = paper_data

    return results

def main():
    print("=" * 70)
    print("🏦 银行从业资格考试 · 近三年（2023~2025）全真题库 JSON 构建流水线")
    print("=" * 70)

    p2024 = build_2024_papers()
    p_other = build_2023_2025_papers()

    all_papers = {**p2024, **p_other}
    total_qs = sum(p["total_questions"] for p in all_papers.values())

    print("\n" + "=" * 70)
    print("📊 近三年（2023~2025）银行从业全真题库构建完成总报告")
    print("=" * 70)
    print(f"📁 题库存储目录: {OUTPUT_DIR}")
    print(f"📚 套卷总数: {len(all_papers)} 套")
    print(f"📝 题目总数: {total_qs} 道全真客观题\n")

    for pid, p in sorted(all_papers.items()):
        print(f"   • [{p['year']}-{p['session']}] 《{p['subject']}》 {p['title']} ({p['total_questions']} 题)")

    print("=" * 70)
    print("🎉 题库生成与 2026 新规审校全部完成！")

if __name__ == "__main__":
    main()

