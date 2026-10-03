#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build js/past_papers.js from data/past_papers/*.json for the Web Simulator.
"""

import json
import glob
import os

PROJECT_DIR = "/home/f1are/orca/projects/银行从业备考"
DATA_DIR = os.path.join(PROJECT_DIR, "data", "past_papers")
OUTPUT_JS = os.path.join(PROJECT_DIR, "js", "past_papers.js")

PAPER_ORDER = [
    # 2025 年 10 月最新机考回忆卷
    "2025_10_law",
    "2025_10_finance",
    "2024_2025_spotlight",
    # 法律法规历年真题
    "2024_10_law",
    "2024_06_law",
    "2025_06_law",
    "2023_06_law",
    "2023_10_law",
    # 个人理财历年真题
    "2024_10_finance",
    "2024_06_finance",
    "2025_06_finance",
    "2023_06_finance",
    "2023_10_finance",
]

def main():
    papers = {}
    
    for paper_id in PAPER_ORDER:
        file_path = os.path.join(DATA_DIR, f"{paper_id}.json")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found")
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            
        qs = raw.get("questions", [])
        formatted_qs = []
        total_score = 0.0
        
        is_full_paper = len(qs) >= 50
        
        for idx, q in enumerate(qs):
            raw_type = q.get("type", "单选题")
            if raw_type in ["多选题", "multiple"]:
                q_type = "multiple"
                section = "多项选择题"
                score = 1.0 if is_full_paper else 2.0
            elif raw_type in ["判断题", "judge"]:
                q_type = "judge"
                section = "判断题"
                score = 1.0
            else:
                q_type = "single"
                section = "单项选择题"
                score = 0.5 if is_full_paper else 1.0
                
            total_score += score
            
            formatted_qs.append({
                "id": q.get("id", f"{paper_id.upper()}-{idx+1:03d}"),
                "section": q.get("section", section),
                "type": q_type,
                "score": score,
                "question": q.get("question", "").strip(),
                "options": q.get("options", {}),
                "answer": q.get("answer", "").strip().upper(),
                "explanation": q.get("explanation", "").strip(),
                "mnemonic": q.get("mnemonic", "").strip(),
                "trap": q.get("trap", "").strip(),
                "is_reformed": bool(q.get("is_reformed", False))
            })
            
        duration = raw.get("durationMinutes", 120 if len(qs) >= 50 else (45 if len(qs) >= 20 else 20))
        
        papers[paper_id] = {
            "id": paper_id,
            "title": raw.get("title", f"银行从业真题卷 ({paper_id})"),
            "subject": raw.get("subject", "银行业初级职业资格"),
            "year": raw.get("year"),
            "session": raw.get("session"),
            "source": raw.get("source", "官方机考学员真题带刷"),
            "durationMinutes": duration,
            "totalScore": round(total_score, 1),
            "totalQuestions": len(formatted_qs),
            "questions": formatted_qs
        }
        print(f"Processed {paper_id}: {len(formatted_qs)} questions, duration {duration}m, totalScore {round(total_score, 1)}")

    header = """/**
 * 2023-2025 银行从业初级职业资格机考 · 历年官方真题试卷库 (past_papers.js)
 * 自动生成自 data/past_papers/*.json
 * 包含近三年 13 套权威真题卷，共计 591 道原版客观题
 */

var PAST_PAPERS = """
    
    footer = """;

// 自动注入全局预置试卷库
if (typeof window !== "undefined") {
  window.PAST_PAPERS = PAST_PAPERS;
  if (typeof PRESET_PAPERS !== "undefined") {
    Object.assign(PRESET_PAPERS, PAST_PAPERS);
  }
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = PAST_PAPERS;
}
"""

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(header)
        json.dump(papers, f, ensure_ascii=False, indent=2)
        f.write(footer)
        
    print(f"\nSuccessfully wrote {len(papers)} papers to {OUTPUT_JS} ({os.path.getsize(OUTPUT_JS)} bytes)")

if __name__ == '__main__':
    main()
