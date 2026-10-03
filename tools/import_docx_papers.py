#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parse 53 questions from 银行业专业人员职业资格考试历年真题汇编（2023-2025考生回忆版）.docx
and generate standardized JSON past exam papers.
"""

import docx
import re
import json
import os

DOCX_PATH = "/home/f1are/下载/银行业专业人员职业资格考试历年真题汇编（2023-2025考生回忆版）.docx"
OUTPUT_DIR = "/home/f1are/orca/projects/银行从业备考/data/past_papers"

def parse_docx():
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

    all_sections = {}

    for p_id, start_idx, end_idx, title, sub, yr, sess in ranges:
        chunk = elements[start_idx:end_idx]
        ans_idx = -1
        for i, (k, v) in enumerate(chunk):
            if k == "P" and "答案与解析" in v:
                ans_idx = i
                break
                
        q_chunk = chunk[:ans_idx] if ans_idx != -1 else chunk
        a_chunk = chunk[ans_idx:] if ans_idx != -1 else []
        
        # Parse explanations and answers from text
        exp_map = {}
        ans_map = {}
        last_exp_num = None
        for k, v in a_chunk:
            if k == "P" and re.match(r"^\d+[\.、]\s*", v):
                m = re.match(r"^(\d+)[\.、]\s*(.*)", v)
                num = int(m.group(1))
                body = m.group(2)
                exp_map[num] = body
                last_exp_num = num
                
                # Check answer pattern in explanation
                ans_match = re.search(r"(?:故本题选|答案为|故选|应选|正确答案为?)\s*([A-E]+)", body)
                if ans_match:
                    ans_map[num] = ans_match.group(1).upper()
            elif k == "P" and "考查考点：" in v and last_exp_num:
                exp_map[last_exp_num] += "\n💡 " + v
                
        # Parse table answers fallback
        for k, v in a_chunk:
            if k == "TBL":
                for r in range(0, len(v), 2):
                    if r + 1 < len(v):
                        nums = [c.strip() for c in v[r]]
                        vals = [c.strip() for c in v[r+1]]
                        for n, val in zip(nums, vals):
                            if n.isdigit() and int(n) not in ans_map:
                                ans_map[int(n)] = val.upper()

        # Parse questions
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

        all_sections[p_id] = {
            "title": title,
            "subject": sub,
            "year": yr,
            "session": sess,
            "questions": qs,
            "answers": ans_map,
            "explanations": exp_map
        }
        print(f"Parsed {p_id}: {len(qs)} Qs, {len(ans_map)} Ans, {len(exp_map)} Exps")

    return all_sections

if __name__ == '__main__':
    parse_docx()
