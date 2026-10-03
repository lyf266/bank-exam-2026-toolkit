#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate standardized JSON files for 2025-10 and spotlight papers from the docx file.
"""

import docx
import re
import json
import os

DOCX_PATH = "/home/f1are/下载/银行业专业人员职业资格考试历年真题汇编（2023-2025考生回忆版）.docx"
OUTPUT_DIR = "/home/f1are/orca/projects/银行从业备考/data/past_papers"

def extract_all():
    doc = docx.Document(DOCX_PATH)
    elements = []
    for child in doc.element.body:
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            p = docx.text.paragraph.Paragraph(child, doc)
            t = p.text.strip()
            if t:
                elements.append(("P", t))
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            table = docx.table.Table(child, doc)
            rows_data = []
            for row in table.rows:
                row_texts = [c.text.strip().replace("\n", " ") for c in row.cells]
                rows_data.append(row_texts)
            elements.append(("TBL", rows_data))

    ranges = [
        ("2025_10_law_am", 19, 106, "2025年10月25日上午场 初级《银行业法律法规与综合能力》真题（考生回忆版）", "银行业法律法规与综合能力", 2025, "10月"),
        ("2025_10_law_pm", 106, 149, "2025年10月25日下午场 初级《银行业法律法规与综合能力》真题（考生回忆版）", "银行业法律法规与综合能力", 2025, "10月"),
        ("2025_06_law_recall", 149, 174, "2025年6月14日上午场 初级《银行业法律法规与综合能力》真题（考生回忆版）", "银行业法律法规与综合能力", 2025, "06月"),
        ("2024_06_law_recall", 174, 204, "2024年6月1—2日场 初级《银行业法律法规与综合能力》真题考点精选（考生回忆）", "银行业法律法规与综合能力", 2024, "06月"),
        ("2025_10_finance_pri", 204, 244, "2025年10月25日场 初级《个人理财》真题（考生回忆版）", "个人理财", 2025, "10月"),
        ("2025_10_finance_mid", 244, 260, "2025年10月25日上午场 中级《个人理财》真题（考生回忆版）", "个人理财", 2025, "10月"),
        ("2024_06_finance_recall", 260, len(elements), "2024年6月1—2日场 初级《个人理财》真题考点精选（考生回忆）", "个人理财", 2024, "06月")
    ]

    parsed_sections = {}

    for p_id, start_idx, end_idx, title, sub, yr, sess in ranges:
        chunk = elements[start_idx:end_idx]
        ans_idx = -1
        for i, (k, v) in enumerate(chunk):
            if k == "P" and "答案与解析" in v:
                ans_idx = i
                break
                
        q_chunk = chunk[:ans_idx] if ans_idx != -1 else chunk
        a_chunk = chunk[ans_idx:] if ans_idx != -1 else []
        
        # 1. Parse answer table
        ans_map = {}
        for k, v in a_chunk:
            if k == "TBL":
                for r in range(0, len(v), 2):
                    if r + 1 < len(v):
                        nums = [c.strip() for c in v[r]]
                        vals = [c.strip() for c in v[r+1]]
                        for n, val in zip(nums, vals):
                            if n.isdigit():
                                ans_map[int(n)] = val.upper()

        # 2. Parse explanations & extract answer from explanation if missing
        exp_map = {}
        last_exp_num = None
        for k, v in a_chunk:
            if k == "P" and re.match(r"^\d+[\.、]\s*", v):
                m = re.match(r"^(\d+)[\.、]\s*(.*)", v)
                num = int(m.group(1))
                body = m.group(2).strip()
                exp_map[num] = body
                last_exp_num = num
                
                ans_match = re.search(r"(?:故本题选|答案为|故选|应选|正确答案为?)\s*([A-E]+)", body)
                if ans_match:
                    ans_map[num] = ans_match.group(1).upper()
            elif k == "P" and "考查考点：" in v and last_exp_num:
                exp_map[last_exp_num] += "\n💡 " + v.strip()

        # 3. Parse questions & options
        qs = []
        curr_q = None
        for k, v in q_chunk:
            if k == "P" and re.match(r"^\d+[\.、]\s*", v):
                m = re.match(r"^(\d+)[\.、]\s*(.*)", v)
                num = int(m.group(1))
                curr_q = {"num": num, "stem": m.group(2).strip(), "options": {}}
                qs.append(curr_q)
            elif k == "P" and re.match(r"^[A-E][\.、\s]", v) and curr_q:
                m = re.match(r"^([A-E])[\.、\s]\s*(.*)", v)
                if m:
                    curr_q["options"][m.group(1)] = m.group(2).strip()
            elif k == "TBL" and curr_q:
                for row in v:
                    for cell in row:
                        m = re.match(r"^([A-E])[\.、\s]\s*(.*)", cell)
                        if m:
                            curr_q["options"][m.group(1)] = m.group(2).strip()

        # Build list of questions
        built_qs = []
        for q in qs:
            num = q["num"]
            stem = q["stem"]
            opts = q["options"]
            ans = ans_map.get(num, "A")
            exp = exp_map.get(num, "暂无详细解析")
            
            # Fix known incomplete options from recall
            if "按照基金运作方式的不同，可以分为开放式" in opts.get("B", ""):
                opts["B"] = "按照基金运作方式的不同，可以分为开放式基金和封闭式基金"
            if num == 9 and "小李目前有一套价值600万元的房屋" in stem and "小李目前有一套价值600万元的房屋" in stem:
                exp = """【等额本息置换房贷期限计算】
① 净资产与新房首付计算：旧房现值 600 万元，剩余房贷 300 万元，出售后净得现金 = 600 - 300 = 300 万元。新房总价 1000 万元，首付 300 万元，新房需贷款本金 $PV_{新} = 1000 - 300 = 700$ 万元。
② 旧房年供款推算：旧房剩余本金 300 万元，期限 6 年，利率 5%，按年等额本息，年还款额 $PMT = 300 \times \\frac{0.05}{1 - (1+0.05)^{-6}} \\approx 59.105$ 万元。
③ 新房还款年限逆推：新房贷款 $PV_{新} = 700$ 万元，年还款额相同 $PMT = 59.105$ 万元，利率 5%。
由年金现值公式 $700 = 59.105 \times \\frac{1 - (1+0.05)^{-N}}{0.05}$，解得 $(1.05)^{-N} \\approx 0.4078$，两边取对数得 $N \\approx 18.38$ 年，约等于 19 年。
故本题选 B。"""
                
            q_type = "single"
            section = "单项选择题"
            if len(ans) > 1:
                q_type = "multiple"
                section = "多项选择题"
                
            # Mnemonic extraction
            mnemonic = ""
            m_mne = re.search(r"(?:【?口诀】?|助记口诀)[:：]?\s*(.*)", exp)
            if m_mne:
                mnemonic = m_mne.group(1).strip()
            else:
                # generate short memorable mnemonic from first sentence of explanation
                mnemonic = exp.split("；")[0].split("，")[0].replace("根据", "").replace("的规定", "")[:18]
                
            built_qs.append({
                "id": f"{p_id.upper()}-{num:02d}",
                "section": section,
                "type": q_type,
                "score": 1.0,
                "question": stem,
                "options": opts,
                "answer": ans,
                "explanation": exp,
                "mnemonic": mnemonic,
                "trap": "⚠️ 2025~2026 机考回忆真题：紧扣题干主旨，排除过度外延或偷换监管概念的干扰项。",
                "is_reformed": "国家金融监督管理总局" in exp or "民法典" in exp or "资管新规" in exp
            })
            
        parsed_sections[p_id] = built_qs

    # Paper 1: 2025_10_law (Combine AM 20 + PM 10 = 30 questions)
    law_2025_10_qs = []
    for idx, q in enumerate(parsed_sections["2025_10_law_am"] + parsed_sections["2025_10_law_pm"]):
        q_copy = dict(q)
        q_copy["id"] = f"2025-10-LAW-{idx+1:03d}"
        law_2025_10_qs.append(q_copy)
        
    law_paper = {
        "paper_id": "2025_10_law",
        "title": "2025年10月25日初级《银行业法律法规与综合能力》最新机考回忆卷",
        "subject": "银行业法律法规与综合能力",
        "year": 2025,
        "session": "10月",
        "source": "官方机考考生回忆还原版（希赛网/233网校精编）",
        "total_questions": len(law_2025_10_qs),
        "durationMinutes": 60,
        "totalScore": len(law_2025_10_qs) * 1.0,
        "questions": law_2025_10_qs
    }
    with open(os.path.join(OUTPUT_DIR, "2025_10_law.json"), "w", encoding="utf-8") as f:
        json.dump(law_paper, f, ensure_ascii=False, indent=2)
    print(f"Generated 2025_10_law.json with {len(law_2025_10_qs)} questions")

    # Paper 2: 2025_10_finance (Combine Primary 10 + Mid 3 = 13 questions)
    fin_2025_10_qs = []
    for idx, q in enumerate(parsed_sections["2025_10_finance_pri"] + parsed_sections["2025_10_finance_mid"]):
        q_copy = dict(q)
        q_copy["id"] = f"2025-10-FIN-{idx+1:03d}"
        fin_2025_10_qs.append(q_copy)
        
    fin_paper = {
        "paper_id": "2025_10_finance",
        "title": "2025年10月25日初级《个人理财》最新机考回忆卷",
        "subject": "个人理财",
        "year": 2025,
        "session": "10月",
        "source": "官方机考考生回忆还原版（希赛网/233网校精编）",
        "total_questions": len(fin_2025_10_qs),
        "durationMinutes": 30,
        "totalScore": len(fin_2025_10_qs) * 1.0,
        "questions": fin_2025_10_qs
    }
    with open(os.path.join(OUTPUT_DIR, "2025_10_finance.json"), "w", encoding="utf-8") as f:
        json.dump(fin_paper, f, ensure_ascii=False, indent=2)
    print(f"Generated 2025_10_finance.json with {len(fin_2025_10_qs)} questions")

    # Paper 3: 2024_2025_spotlight (Combine 2025_06 5 + 2024_06 law 4 + 2024_06 fin 1 = 10 questions)
    spotlight_qs = []
    for idx, q in enumerate(parsed_sections["2025_06_law_recall"] + parsed_sections["2024_06_law_recall"] + parsed_sections["2024_06_finance_recall"]):
        q_copy = dict(q)
        q_copy["id"] = f"SPOTLIGHT-{idx+1:03d}"
        spotlight_qs.append(q_copy)
        
    spotlight_paper = {
        "paper_id": "2024_2025_spotlight",
        "title": "2024-2025 银行业专业人员职业资格机考高频考点密训卷",
        "subject": "综合双科密训",
        "year": 2025,
        "session": "综合密训",
        "source": "官方机考考生回忆高频考点精编",
        "total_questions": len(spotlight_qs),
        "durationMinutes": 25,
        "totalScore": len(spotlight_qs) * 1.0,
        "questions": spotlight_qs
    }
    with open(os.path.join(OUTPUT_DIR, "2024_2025_spotlight.json"), "w", encoding="utf-8") as f:
        json.dump(spotlight_paper, f, ensure_ascii=False, indent=2)
    print(f"Generated 2024_2025_spotlight.json with {len(spotlight_qs)} questions")

if __name__ == '__main__':
    extract_all()
