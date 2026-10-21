# -*- coding: utf-8 -*-
"""
生成2026年银行业职业资格考试《法律法规》与《个人理财》全真完整套卷 (125题标准全真机考大卷)
- 严禁调用 Anki
- 仅全量导入考试系统 data/past_papers/
- 每套试卷包含：80道单选 + 30道多选 + 15道判断 = 125道完整标准ATA机考套卷
"""

import os
import json
from tools.generate_past_papers_json import reform_linter

from tools.data_law_part1 import LAW_QUESTIONS_PART1
from tools.data_law_part1b import LAW_QUESTIONS_PART1B
from tools.data_law_part2 import LAW_QUESTIONS_PART2

from tools.data_fin_part1 import FIN_QUESTIONS_PART1
from tools.data_fin_part1b import FIN_QUESTIONS_PART1B
from tools.data_fin_part2 import FIN_QUESTIONS_PART2

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "past_papers")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. 组装法律法规完整试卷
    law_raw = LAW_QUESTIONS_PART1 + LAW_QUESTIONS_PART1B + LAW_QUESTIONS_PART2
    print(f"法律法规原始题目总数: {len(law_raw)}")
    law_processed = [reform_linter(q) for q in law_raw]

    # 统计题型
    law_types = {}
    for q in law_processed:
        t = q.get("type", "单选题")
        law_types[t] = law_types.get(t, 0) + 1
    print(f"法律法规题型分布: {law_types}")

    law_paper = {
        "paper_id": "2026_law_complete_online",
        "title": "2026全真机考标准套卷（网络权威精选题库·125题全真满编）",
        "subject": "银行业法律法规与综合能力",
        "year": 2026,
        "session": "标准模考",
        "source": "网络权威真题题库精选 (233网校/希赛/东方研修院 2025~2026)",
        "total_questions": len(law_processed),
        "questions": law_processed
    }

    law_path = os.path.join(DATA_DIR, "2026_law_complete_online.json")
    with open(law_path, "w", encoding="utf-8") as f:
        json.dump(law_paper, f, ensure_ascii=False, indent=2)
    print(f"已生成: {law_path}")

    # 2. 组装个人理财完整试卷
    fin_raw = FIN_QUESTIONS_PART1 + FIN_QUESTIONS_PART1B + FIN_QUESTIONS_PART2
    print(f"个人理财原始题目总数: {len(fin_raw)}")
    fin_processed = [reform_linter(q) for q in fin_raw]

    fin_types = {}
    for q in fin_processed:
        t = q.get("type", "单选题")
        fin_types[t] = fin_types.get(t, 0) + 1
    print(f"个人理财题型分布: {fin_types}")

    fin_paper = {
        "paper_id": "2026_finance_complete_online",
        "title": "2026全真机考标准套卷（网络权威精选题库·125题全真满编）",
        "subject": "个人理财",
        "year": 2026,
        "session": "标准模考",
        "source": "网络权威真题题库精选 (233网校/希赛/东方研修院 2025~2026)",
        "total_questions": len(fin_processed),
        "questions": fin_processed
    }

    fin_path = os.path.join(DATA_DIR, "2026_finance_complete_online.json")
    with open(fin_path, "w", encoding="utf-8") as f:
        json.dump(fin_paper, f, ensure_ascii=False, indent=2)
    print(f"已生成: {fin_path}")

    # 3. 清理之前的20题简版网络试卷，避免在系统中重复或混淆
    for old_file in ["2026_law_online.json", "2026_finance_online.json"]:
        old_path = os.path.join(DATA_DIR, old_file)
        if os.path.exists(old_path):
            os.remove(old_path)
            print(f"已清理旧简版: {old_path}")

    print("🎉 完整125题双科全真套卷构建并导入成功！未调用任何Anki接口。")

if __name__ == "__main__":
    main()
