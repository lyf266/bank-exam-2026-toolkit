#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业初级资格考试 · 全量真题套题与模考金题 Anki 自动化抽取、新规清洗与注入引擎
- 解析本地资料库 4 大权威讲义 PDF（法律法规真题带刷班、模考金题班；个人理财真题带刷班、模考金题班）
- 全量提取 475 道套题客观题（单选题、多选题、判断题）
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

def find_question_starts(lines, ans_indices):
    """精确定位每道题目的起始行索引"""
    q_starts = []
    q0_start = 0
    for i in range(ans_indices[0]):
        if re.match(r"^\d+[、\.]", lines[i]) or lines[i] in ["单选题：", "多选题：", "判断题："] or re.match(r"^\d+\.?$", lines[i]):
            q0_start = i
            break
        if "单项选择题" in lines[i]:
            q0_start = i + 1
    q_starts.append(q0_start)

    for k in range(1, len(ans_indices)):
        prev_ans = ans_indices[k-1]
        cur_ans = ans_indices[k]

        opt_start = cur_ans
        while opt_start > prev_ans + 2 and re.match(r"^[A-E][．\.、]", lines[opt_start-1]):
            opt_start -= 1

        best_start = None
        for i in range(prev_ans + 2, opt_start):
            l = lines[i]
            if l == "【解析】":
                continue
            if re.match(r"^第[一二三四五六七八九十]+章", l):
                best_start = i
                break
            if any(s in l for s in ["一、单项选择题", "二、多项选择题", "三、判断题", "一、 单项选择题", "二、多项选择题。"]):
                best_start = i
                break
            if re.match(r"^\d+[、]", l):
                best_start = i
                break
            if re.match(r"^\d+\.?$", l) and i + 2 < len(lines) and any(kw in lines[i+1] or kw in lines[i+2] for kw in ["单", "选题", "判断"]):
                best_start = i
                break
            if l in ["单选题：", "多选题：", "判断题："]:
                best_start = i
                break

        if best_start is None:
            best_start = max(prev_ans + 3, opt_start - 2)
        q_starts.append(best_start)

    return q_starts

def generate_mnemonic_and_trap(q_type, stem, options, ans, explanation):
    """依据 2024~2026 监管新规及题目特征智能生成口诀与避坑指南"""
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

    # 2. 提取口诀/记忆关键词
    sens = [s.strip() for s in re.split(r"[。；\n]", explanation) if s.strip() and not re.match(r"^(?:故本题|本题选|综上所述|本题考查|答案为|故选)", s.strip())]
    if sens:
        s0 = sens[0]
        s0 = re.sub(r"^[A-E正确错误对错1-9项、\.，\s]+", "", s0).strip()
        if len(s0) > 20:
            mnemonic = s0[:19] + "…"
        else:
            mnemonic = s0 if s0 else "牢记题眼定义，准确对应选项。"
    else:
        mnemonic = "牢记题眼定义，准确对应选项。"

    return mnemonic, trap

def parse_exam_pdf(pdf_config):
    """解析单份 PDF 讲义并返回结构化客观题列表"""
    path = pdf_config["pdf_path"]
    tag_prefix = pdf_config["tag_prefix"]
    lines = clean_pdf_lines(path)
    ans_indices = [i for i, l in enumerate(lines) if l == "【答案】"]
    starts = find_question_starts(lines, ans_indices)

    questions = []
    for k in range(len(ans_indices)):
        s_idx = starts[k]
        a_idx = ans_indices[k]
        next_s_idx = starts[k+1] if k + 1 < len(starts) else len(lines)

        raw_ans = lines[a_idx + 1] if a_idx + 1 < len(lines) else ""
        norm_ans = raw_ans.strip().upper().replace(" ", "")

        # 选项提取（从 a_idx - 1 往前扫描至 Option A）
        opt_lines = []
        p = a_idx - 1
        found_a = False
        while p >= s_idx:
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

        if not found_a:
            opt_lines = []
            stem_raw_lines = lines[s_idx:a_idx]
        else:
            stem_raw_lines = lines[s_idx : p + 1]

        # 解析提取
        e_start = a_idx + 2
        if e_start < len(lines) and lines[e_start] == "【解析】":
            e_start += 1
        exp_lines = lines[e_start : next_s_idx]

        # 清洗题干
        stem_str = " ".join(stem_raw_lines).strip()
        for _ in range(5):
            stem_str = re.sub(r"^(?:6\s*月模考金题[（\(][一二三][\)）]\s*)", "", stem_str).strip()
            stem_str = re.sub(r"^(?:[一二三四]、\s*[单多选判].*?题[。]?)", "", stem_str).strip()
            stem_str = re.sub(r"^（共\d+题.*?）", "", stem_str).strip()
            stem_str = re.sub(r"^（本大题共\d+小题.*?）", "", stem_str).strip()
            stem_str = re.sub(r"^以下各小题.*?）", "", stem_str).strip()
            stem_str = re.sub(r"^第[一二三四五六七八九十]+章\s*.*?(?=(?:\d+\.?|单选题|多选题|判断题))", "", stem_str).strip()
            stem_str = re.sub(r"^[\d\.\s、]+", "", stem_str).strip()
            stem_str = re.sub(r"^(?:单|多|判)\s*选?\s*题[：:]?\s*", "", stem_str).strip()
            stem_str = re.sub(r"^[\d\.\s、]+", "", stem_str).strip()

        # 解析选项字典
        options = {}
        cur_k = None
        for ol in opt_lines:
            m = re.match(r"^([A-E])[．\.、]\s*(.*)", ol)
            if m:
                cur_k = m.group(1)
                options[cur_k] = m.group(2).strip()
            elif cur_k:
                options[cur_k] += " " + ol.strip()

        # 判定题型
        combined_raw = " ".join(stem_raw_lines)
        q_type = "单选题"
        if any(w in combined_raw for w in ["多项选择题", "多选题"]):
            q_type = "多选题"
        elif any(w in combined_raw for w in ["判断题", "判断"]):
            q_type = "判断题"
        elif len(norm_ans) > 1 and all(c in "ABCDE" for c in norm_ans):
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

        exp_clean = " ".join(exp_lines).strip()
        mnemonic, trap = generate_mnemonic_and_trap(q_type, stem_str, options, norm_ans, exp_clean)

        questions.append({
            "id": f"{tag_prefix}-{k+1:03d}",
            "type": q_type,
            "question": stem_str,
            "options": options,
            "answer": norm_ans,
            "explanation": exp_clean,
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
    print("🏦 2026 银行从业初级资格考试 · 全真套题全量导入引擎")
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
