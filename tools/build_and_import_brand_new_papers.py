#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tools/build_and_import_brand_new_papers.py

2026 银行从业初级资格考试 · 全新题库精准抽取、新规清洗与双系统注入引擎
- 从本地全量资料库全新讲义（法律法规教材精讲上/下、个人理财教材精讲、计算专项突破班）中全量精准抽取
- 100% 独立于现有题库的全新试题（保证 0 重复）
- 100% 融入 2024~2026 现行规范与避坑标注（金融监管总局 NFRA、民法典、2025年1月起个人活期入 M1、资管全面净值化）
- 自动生成 15 字秒杀口诀与避坑指南
- 自动保存为标准 JSON 套卷至 data/past_papers/ (供 quick_quiz.py 全真模考系统直读)
- 自动通过 AnkiConnect 注入本地 Anki 对应牌组
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from import_all_exam_papers import clean_pdf_lines, generate_mnemonic_and_trap, anki_invoke
from tools.generate_past_papers_json import reform_linter

DATA_DIR = os.path.join(BASE_DIR, "data", "past_papers")
MATERIALS_DIR = os.path.join(BASE_DIR, "本地全量资料库")

def load_existing_signatures():
    signatures = set()
    for pf in os.listdir(DATA_DIR):
        if pf.endswith(".json") and not pf.endswith("_new.json"):
            path = os.path.join(DATA_DIR, pf)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    for q in d.get("questions", []):
                        sig = re.sub(r"[\s\d\.\,\(\)（）\、\:\：\[\]【】\*\_\'\"\?？]", "", q["question"])[:18]
                        if sig:
                            signatures.add(sig)
            except Exception as e:
                print(f"⚠️ 读取 {pf} 出错: {e}")
    return signatures

def parse_clean_questions(pdf_path, subject, tag_prefix, existing_sigs):
    lines = clean_pdf_lines(pdf_path)
    ans_indices = [i for i, l in enumerate(lines) if re.match(r"^【答案】", l)]

    extracted = []
    for idx_num, a_idx in enumerate(ans_indices):
        ans_raw = lines[a_idx].replace("【答案】", "").strip()
        exp_start = a_idx + 1
        if not ans_raw and a_idx + 1 < len(lines):
            ans_raw = lines[a_idx + 1].strip()
            exp_start = a_idx + 2

        norm_ans = ans_raw.upper().replace(" ", "").replace("、", "")

        # 向上寻找 A 选项
        limit_prev = 0 if idx_num == 0 else ans_indices[idx_num - 1] + 1
        start_scan = max(limit_prev, a_idx - 35)

        opt_a_idx = None
        for p in range(a_idx - 1, start_scan - 1, -1):
            l = lines[p]
            if re.match(r"^A[．\.、\s]", l):
                opt_a_idx = p
                break
            if l in ["正确", "对", "A．正确", "A. 正确"]:
                opt_a_idx = p
                break

        if opt_a_idx is None:
            continue

        raw_opts = lines[opt_a_idx:a_idx]
        opts = {}
        curr_k = None
        for ol in raw_opts:
            m = re.match(r"^([A-E])[．\.、\s]\s*(.*)", ol)
            if m:
                curr_k = m.group(1)
                opts[curr_k] = m.group(2).strip()
            elif ol in ["正确", "对"]:
                opts["A"] = "正确"
            elif ol in ["错误", "错"]:
                opts["B"] = "错误"
            elif curr_k:
                opts[curr_k] += " " + ol.strip()

        # 向上寻找题干
        stem_start = opt_a_idx - 1
        for p in range(opt_a_idx - 1, max(limit_prev - 1, opt_a_idx - 25), -1):
            l = lines[p]
            if re.match(r"^\d{1,3}[、\.](?!\d)", l) or any(kw in l for kw in ["【单选", "【多选", "【判断", "【单选题", "【多选题", "【判断题", "习题演练"]):
                stem_start = p
                break
        stem = " ".join(lines[stem_start:opt_a_idx]).strip()

        # 清除前导杂质
        stem = re.sub(r"^(?:习题演练|【\s*(?:单选|多选|判断|单选题|多选题|判断题)\s*】|\d+[、\.])\s*", "", stem).strip()
        stem = re.sub(r"^(?:习题演练|【\s*(?:单选|多选|判断|单选题|多选题|判断题)\s*】|\d+[、\.])\s*", "", stem).strip()

        # 过滤过短或残缺选项
        if len(stem) < 8 or len(opts) < 2:
            continue

        # 去重检查
        sig = re.sub(r"[\s\d\.\,\(\)（）\、\:\：\[\]【】\*\_\'\"\?？]", "", stem)[:18]
        if sig in existing_sigs:
            continue
        existing_sigs.add(sig)

        # 提取解析
        next_lim = ans_indices[idx_num + 1] if idx_num + 1 < len(ans_indices) else len(lines)
        exp_lines = []
        for j in range(exp_start, min(next_lim, exp_start + 25)):
            l = lines[j]
            if any(kw in l for kw in ["习题演练", "【单选", "【多选", "【判断"]) or re.match(r"^\d{1,3}[、\.](?!\d)", l):
                break
            exp_lines.append(l)
        exp = " ".join(exp_lines).replace("【解析】", "").strip()
        if not exp:
            exp = "暂无官方文字解析。建议结合考纲核心教材与现行监管规范理解掌握。"

        # 判定题型与格式化答案
        if len(norm_ans) > 1 and all(c in "ABCDE" for c in norm_ans):
            q_type = "多选题"
        elif any(c in norm_ans for c in ["对", "错", "正确", "错误"]) or (len(opts) == 2 and "正确" in opts.get("A", "")):
            q_type = "判断题"
            if norm_ans in ["对", "正确", "T", "1", "√"]:
                norm_ans = "A"
            elif norm_ans in ["错", "错误", "F", "0", "×"]:
                norm_ans = "B"
            if not opts.get("A"):
                opts["A"] = "正确"
            if not opts.get("B"):
                opts["B"] = "错误"
        else:
            q_type = "单选题"
            if norm_ans not in opts:
                # 尝试从答案首字母修复
                for letter in ["A", "B", "C", "D", "E"]:
                    if letter in norm_ans:
                        norm_ans = letter
                        break

        qid = f"{tag_prefix}-{len(extracted)+1:03d}"
        mnemonic, trap = generate_mnemonic_and_trap(q_type, stem, opts, norm_ans, exp, qid)

        item = {
            "id": qid,
            "type": q_type,
            "question": stem,
            "options": opts,
            "answer": norm_ans,
            "explanation": exp,
            "mnemonic": mnemonic,
            "trap": trap
        }
        item = reform_linter(item)
        extracted.append(item)

    return extracted

def sync_to_anki(deck_name, questions, subject, paper_name):
    model_name = "银行从业·全真机考客观题"
    try:
        anki_invoke("createDeck", deck=deck_name)
    except Exception as e:
        print(f"⚠️ 创建牌组失败: {e}")
        return 0

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
            "tags": ["2026银行从业", subject, paper_name, q["type"], "全新题库"]
        })

    existing_cards = anki_invoke("findCards", query=f'deck:"{deck_name}"')
    if existing_cards:
        print(f"   ⚠️ 牌组 '{deck_name}' 已存在 {len(existing_cards)} 张卡片，清理旧版本以注入全量最新题库...")
        anki_invoke("deleteDecks", decks=[deck_name], cardsToo=True)
        anki_invoke("createDeck", deck=deck_name)

    print(f"   🚀 正在批量注入 {len(notes)} 张全新卡片至 Anki...")
    added = anki_invoke("addNotes", notes=notes)
    success_cnt = sum(1 for x in added if x is not None)
    print(f"   ✅ 成功注入: {success_cnt} / {len(notes)} 张卡片！")
    return success_cnt

def main():
    print("=" * 70)
    print("🚀 开始抽取与构建 2026 全新真题密训套卷 (法律法规 & 个人理财)")
    print("=" * 70)

    sigs = load_existing_signatures()
    print(f"📌 现有题库已录入 {len(sigs)} 条特征签名，全程实施 100% 严格去重。")

    # 1. 抽取法律法规全新题目
    print("\n📦 [1/4] 正在抽取《银行业法律法规与综合能力》(上册讲义)...")
    path_law1 = os.path.join(MATERIALS_DIR, "[旧版参考-机构待核验]初级银从-法律法规/01.教材精讲班/2026-初级《法律法规》教材精讲班(上)-孙婧【重要等级：★★☆☆☆全书讲义】.pdf")
    law_part1 = parse_clean_questions(path_law1, "法律法规", "LAW-NEW", sigs)
    print(f"   -> 提取出有效新题 {len(law_part1)} 道")

    print("\n📦 [2/4] 正在抽取《银行业法律法规与综合能力》(下册讲义)...")
    path_law2 = os.path.join(MATERIALS_DIR, "[旧版参考-机构待核验]初级银从-法律法规/01.教材精讲班/2026-初级《法律法规》教材精讲班(下)-孙婧【重要等级：★★☆☆☆全书讲义】.pdf")
    law_part2 = parse_clean_questions(path_law2, "法律法规", "LAW-NEW", sigs)
    print(f"   -> 提取出有效新题 {len(law_part2)} 道")

    all_law_questions = law_part1 + law_part2
    # 重新规范化 ID
    for idx, q in enumerate(all_law_questions, 1):
        q["id"] = f"LAW-NEW-{idx:03d}"

    print(f"\n🏛️ 《银行业法律法规与综合能力》全新题库总计: {len(all_law_questions)} 道")

    # 2. 抽取个人理财全新题目
    print("\n📦 [3/4] 正在抽取《个人理财》(教材精讲讲义)...")
    path_fin1 = os.path.join(MATERIALS_DIR, "[参考资料]初级银从-个人理财/01.教材精讲班/2026-初级《个人理财》教材精讲班-徐雨光【重要等级：★★☆☆☆全书讲义】.pdf")
    fin_part1 = parse_clean_questions(path_fin1, "个人理财", "FIN-NEW", sigs)
    print(f"   -> 提取出有效新题 {len(fin_part1)} 道")

    print("\n📦 [4/4] 正在抽取《个人理财》(计算专项突破讲义)...")
    path_fin2 = os.path.join(MATERIALS_DIR, "[参考资料]初级银从-个人理财/02.计算题专项班/2026-初级《个人理财》计算专项突破班-徐雨光【重要等级：★★★★★计算专项】.pdf")
    fin_part2 = parse_clean_questions(path_fin2, "个人理财", "FIN-NEW", sigs)
    print(f"   -> 提取出有效新题 {len(fin_part2)} 道")

    all_fin_questions = fin_part1 + fin_part2
    for idx, q in enumerate(all_fin_questions, 1):
        q["id"] = f"FIN-NEW-{idx:03d}"

    print(f"\n💰 《个人理财》全新题库总计: {len(all_fin_questions)} 道")

    # 3. 输出为标准机考 JSON 套卷
    os.makedirs(DATA_DIR, exist_ok=True)

    law_paper = {
        "paper_id": "2026_06_law_new",
        "title": "2026年最新考纲初级《银行业法律法规与综合能力》全真通关密训卷 (全新题库)",
        "subject": "银行业法律法规与综合能力",
        "year": 2026,
        "session": "06月",
        "source": "2026新考纲教材精讲与考点精粹（全量新题）",
        "total_questions": len(all_law_questions),
        "questions": all_law_questions
    }
    path_law_json = os.path.join(DATA_DIR, "2026_06_law_new.json")
    with open(path_law_json, "w", encoding="utf-8") as f:
        json.dump(law_paper, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已成功写入法律法规套卷 JSON: {path_law_json} ({len(all_law_questions)} 题)")

    fin_paper = {
        "paper_id": "2026_06_finance_new",
        "title": "2026年最新考纲初级《个人理财》全真通关密训卷 (全新题库·含计算突破)",
        "subject": "个人理财",
        "year": 2026,
        "session": "06月",
        "source": "2026新考纲教材精讲与计算专项突破（全量新题）",
        "total_questions": len(all_fin_questions),
        "questions": all_fin_questions
    }
    path_fin_json = os.path.join(DATA_DIR, "2026_06_finance_new.json")
    with open(path_fin_json, "w", encoding="utf-8") as f:
        json.dump(fin_paper, f, ensure_ascii=False, indent=2)
    print(f"💾 已成功写入个人理财套卷 JSON: {path_fin_json} ({len(all_fin_questions)} 题)")

    # 4. 同步注入 Anki
    print("\n🎴 正在同步注入至 Anki 本地客户端...")
    try:
        anki_invoke("version")
        deck_law = "01_🔥核心冲刺::01_银行从业::[全真密训]初级法律法规·2026全新通关卷"
        deck_fin = "01_🔥核心冲刺::01_银行从业::[全真密训]初级个人理财·2026全新通关卷"

        sync_to_anki(deck_law, all_law_questions, "法律法规", "全新通关卷")
        sync_to_anki(deck_fin, all_fin_questions, "个人理财", "全新通关卷")
        print("🎉 Anki 同步注入全量完成！")
    except Exception as e:
        print(f"⚠️ Anki 同步略过或出现异常: {e}")

    print("\n" + "=" * 70)
    print(f"✅ 全新套题导入全部完成！")
    print(f"   • 法律法规全新密训卷: {len(all_law_questions)} 道")
    print(f"   • 个人理财全新密训卷: {len(all_fin_questions)} 道")
    print("=" * 70)

if __name__ == "__main__":
    main()
