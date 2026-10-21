#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行从业初级备考 · 反过拟合题集与对比挖空全自动同步引擎 (sync_anti_overfit_deck.py)
-----------------------------------------------------------------------------
功能：
1. 自动注册并维护高美感《银行从业·反过拟合对比挖空模板》（思源黑体、双端暗黑自适应、横向网格表格）；
2. 自动构建专属多层级目标牌组：
   - 01_🔥核心冲刺::01_银行从业::[反过拟合]一题多变与挖空对比::01_高频混淆考点挖空对比表
   - 01_🔥核心冲刺::01_银行从业::[反过拟合]一题多变与挖空对比::02_一题多变反过拟合特训
3. 绑定 FSRS 科学记忆预设《银行从业·科学记忆预设》；
4. 解析《错题本_反过拟合题集.md》，精准提取 14 幅横向对比挖空矩阵与 56 道一题多变真题；
5. 幂等性检测与增量更新，杜绝重复与数据污染。
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error

ANKI_CONNECT_URL = "http://127.0.0.1:8765"

PARENT_DECK = "01_🔥核心冲刺::01_银行从业::[反过拟合]一题多变与挖空对比"
CLOZE_DECK = f"{PARENT_DECK}::01_高频混淆考点挖空对比表"
OBJECTIVE_DECK = f"{PARENT_DECK}::02_一题多变反过拟合特训"

CLOZE_MODEL_NAME = "银行从业·反过拟合对比挖空模板"
OBJECTIVE_MODEL_NAME = "银行从业·全真机考客观题"
PRESET_NAME = "银行从业·科学记忆预设"

SOURCE_MD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "错题本_反过拟合题集.md")

CLOZE_CSS = """@import url("_editor_button_styles.css");

:root {
  --bg-app: #f8fafc;
  --bg-card: #ffffff;
  --text-main: #0f172a;
  --text-sub: #334155;
  --text-muted: #64748b;
  --border-light: #e2e8f0;
  --badge-bg: #f1f5f9;
  --table-header-bg: #f1f5f9;
  --table-border: #cbd5e1;
  --table-alt-bg: #f8fafc;
  --cloze-color: #2563eb;
  --cloze-bg: #eff6ff;
  --cloze-border: #93c5fa;
}

.night_mode, .nightMode, body.night_mode, body.nightMode {
  --bg-app: #0f172a;
  --bg-card: #1e293b;
  --text-main: #f8fafc;
  --text-sub: #cbd5e1;
  --text-muted: #94a3b8;
  --border-light: #334155;
  --badge-bg: #334155;
  --table-header-bg: #0f172a;
  --table-border: #475569;
  --table-alt-bg: #1e293b;
  --cloze-color: #60a5fa;
  --cloze-bg: #1e3a8a;
  --cloze-border: #3b82f6;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-app: #0f172a;
    --bg-card: #1e293b;
    --text-main: #f8fafc;
    --text-sub: #cbd5e1;
    --text-muted: #94a3b8;
    --border-light: #334155;
    --badge-bg: #334155;
    --table-header-bg: #0f172a;
    --table-border: #475569;
    --table-alt-bg: #1e293b;
    --cloze-color: #60a5fa;
    --cloze-bg: #1e3a8a;
    --cloze-border: #3b82f6;
  }
}

.card {
  font-family: "Source Han Sans SC", "Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-main) !important;
  background-color: var(--bg-app) !important;
  padding: 12px;
  margin: 0 auto;
  max-width: 760px;
  -webkit-font-smoothing: antialiased;
}

.exam-container {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: 12px;
  padding: 18px 20px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.type-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

.badge-cloze {
  color: #0284c7;
  background-color: #e0f2fe;
  border: 1px solid #bae6fd;
}
.night_mode .badge-cloze, .nightMode .badge-cloze {
  color: #7dd3fc;
  background-color: #0c4a6e;
  border-color: #0284c7;
}

.exam-id {
  font-size: 12px;
  font-family: monospace;
  color: var(--text-muted) !important;
  background: var(--badge-bg) !important;
  padding: 2px 6px;
  border-radius: 4px;
}

.cloze-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 14px;
  line-height: 1.5;
  border-bottom: 1.5px solid var(--border-light);
  padding-bottom: 8px;
}

.cloze-table-container {
  overflow-x: auto;
  margin: 14px 0;
}

.cloze-table-container table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  line-height: 1.5;
}

.cloze-table-container th {
  background-color: var(--table-header-bg);
  border: 1px solid var(--table-border);
  padding: 8px 10px;
  font-weight: 700;
  color: var(--text-main);
}

.cloze-table-container td {
  border: 1px solid var(--table-border);
  padding: 8px 10px;
  color: var(--text-sub);
}

.cloze {
  font-weight: 700;
  color: var(--cloze-color) !important;
  background-color: var(--cloze-bg) !important;
  border: 1px dashed var(--cloze-border);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin: 1px 2px;
}

.interactive-hint {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding-top: 10px;
  border-top: 1px dashed var(--border-light);
}

.info-section {
  border-radius: 8px;
  padding: 12px 14px;
  margin-top: 12px;
  font-size: 14px;
}

.mnemonic-card {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-left: 4px solid #f59e0b;
}
.night_mode .mnemonic-card, .nightMode .mnemonic-card {
  background: #451a03;
  border-color: #78350f;
  border-left-color: #f59e0b;
}

.mnemonic-title {
  font-weight: 700;
  color: #b45309;
  margin-bottom: 4px;
  font-size: 13px;
}
.night_mode .mnemonic-title, .nightMode .mnemonic-title {
  color: #fcd34d;
}

.mnemonic-body {
  font-size: 15px;
  font-weight: 700;
  color: #92400e;
}
.night_mode .mnemonic-body, .nightMode .mnemonic-body {
  color: #fef3c7;
}

.analysis-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.night_mode .analysis-card, .nightMode .analysis-card {
  background: #1e293b;
  border-color: #334155;
}

.analysis-title {
  font-weight: 700;
  color: #334155;
  margin-bottom: 6px;
  font-size: 13px;
}
.night_mode .analysis-title, .nightMode .analysis-title {
  color: #cbd5e1;
}

.analysis-body {
  color: #475569;
  line-height: 1.6;
}
.night_mode .analysis-body, .nightMode .analysis-body {
  color: #94a3b8;
}

.trap-card {
  background: #fff1f2;
  border: 1px solid #fecdd3;
  border-left: 4px solid #f43f5e;
}
.night_mode .trap-card, .nightMode .trap-card {
  background: #4c0519;
  border-color: #881337;
  border-left-color: #fb7185;
}

.trap-title {
  font-weight: 700;
  color: #e11d48;
  margin-bottom: 4px;
  font-size: 13px;
}
.night_mode .trap-title, .nightMode .trap-title {
  color: #fda4af;
}

.trap-body {
  color: #9f1239;
  line-height: 1.5;
}
.night_mode .trap-body, .nightMode .trap-body {
  color: #ffe4e6;
}

.card-author-watermark {
  margin-top: 14px;
  padding-top: 8px;
  border-top: 1px dashed rgba(140, 140, 140, 0.3);
  font-size: 11px;
  color: #8c8c8c;
  text-align: center;
  font-weight: 500;
  letter-spacing: 0.5px;
}
"""

CLOZE_QFMT = """<div class="exam-container cloze-card-wrap">
  <div class="exam-header">
    <span class="type-badge badge-cloze">{{考点分类}}</span>
    <span class="exam-id">{{ID}}</span>
  </div>

  <div class="cloze-title">
    💡 <b>反过拟合 · 核心概念切片对比</b>：{{考点标题}}
  </div>

  <div class="cloze-table-container">
    {{cloze:挖空内容}}
  </div>

  <div class="interactive-hint">
    ⌨️ <i>遮挡主动提取：依据横向因果与监管红线，在脑海中补齐关键数值与法定特征</i>
  </div>
</div>"""

CLOZE_AFMT = """<div class="exam-container cloze-card-wrap back-container">
  <div class="exam-header">
    <span class="type-badge badge-cloze">{{考点分类}}</span>
    <span class="exam-id">{{ID}}</span>
  </div>

  <div class="cloze-title">
    💡 <b>反过拟合 · 核心概念切片对比</b>：{{考点标题}}
  </div>

  <div class="cloze-table-container">
    {{cloze:挖空内容}}
  </div>

  {{#速记口诀}}
  <div class="info-section mnemonic-card">
    <div class="mnemonic-title">⚡ 15字秒杀口诀</div>
    <div class="mnemonic-body">{{速记口诀}}</div>
  </div>
  {{/速记口诀}}

  {{#核心考点解析}}
  <div class="info-section analysis-card">
    <div class="analysis-title">📖 底层法理与监管精析</div>
    <div class="analysis-body">{{核心考点解析}}</div>
  </div>
  {{/核心考点解析}}

  {{#避坑指南}}
  <div class="info-section trap-card">
    <div class="trap-title">⚠️ 出题人设坑与反过拟合指南</div>
    <div class="trap-body">{{避坑指南}}</div>
  </div>
  {{/避坑指南}}

  <div class="card-author-watermark">
    2026 银行从业初级 · 反过拟合对比挖空特训
  </div>
</div>"""

def anki_invoke(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    req = urllib.request.Request(ANKI_CONNECT_URL, payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if len(res) == 2 and "error" in res and res["error"] is not None:
                raise RuntimeError(res["error"])
            return res.get("result")
    except urllib.error.URLError as e:
        raise ConnectionError(f"无法连接到 AnkiConnect ({ANKI_CONNECT_URL}): {e}")

def ensure_cloze_model():
    """注册或更新反过拟合专用对比挖空模型"""
    models = anki_invoke("modelNames")
    in_order_fields = ["ID", "考点分类", "考点标题", "挖空内容", "核心考点解析", "速记口诀", "避坑指南"]
    
    if CLOZE_MODEL_NAME not in models:
        anki_invoke(
            "createModel",
            modelName=CLOZE_MODEL_NAME,
            inOrderFields=in_order_fields,
            isCloze=True,
            css=CLOZE_CSS,
            cardTemplates=[{"Name": "对比挖空卡", "Front": CLOZE_QFMT, "Back": CLOZE_AFMT}]
        )
        print(f"✨ 成功注册高颜值新模板: {CLOZE_MODEL_NAME}")
    else:
        # 更新 CSS 与模板确保最新样式生效
        anki_invoke("updateModelStyling", model={"name": CLOZE_MODEL_NAME, "css": CLOZE_CSS})
        anki_invoke("updateModelTemplates", model={"name": CLOZE_MODEL_NAME, "templates": {"对比挖空卡": {"Front": CLOZE_QFMT, "Back": CLOZE_AFMT}}})
        print(f"🔄 已核验并刷新模板样式与结构: {CLOZE_MODEL_NAME}")

def ensure_decks_and_fsrs():
    """确保多层级牌组就绪并绑定 FSRS 记忆预设"""
    decks = anki_invoke("deckNames")
    target_decks = [PARENT_DECK, CLOZE_DECK, OBJECTIVE_DECK]
    
    for d in target_decks:
        if d not in decks:
            anki_invoke("createDeck", deck=d)
            print(f"📦 已创建专属牌组: {d}")
            
    # 尝试绑定专属 FSRS 预设
    try:
        configs = anki_invoke("deckConfigNames")
        target_conf = next((c for c in configs if c.get("name") == PRESET_NAME), None)
        if target_conf:
            for d in [CLOZE_DECK, OBJECTIVE_DECK]:
                anki_invoke("setDeckConfigId", decks=[d], configId=target_conf["id"])
            print(f"⚙️ 成功将牌组绑定至专属预设: {PRESET_NAME}")
    except Exception as e:
        print(f"⚠️ 预设绑定提示（非致命）: {e}")

def parse_anti_overfit_markdown(filepath):
    """解析 Markdown 文件，返回 Cloze 笔记列表与一题多变客观题笔记列表"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 按专题切割
    topic_sections = re.split(r'\n## 专题 (ANTI-\d+)[：:]\s*(.+?)\n', content)
    
    cloze_notes = []
    objective_notes = []

    # topic_sections[0] 是前言，从 1 开始每 3 项是一组 (id, title, body)
    for i in range(1, len(topic_sections), 3):
        t_id = topic_sections[i].strip()
        t_title = topic_sections[i+1].strip()
        t_body = topic_sections[i+2]
        
        # 1. 提取 Cloze 对比表
        table_match = re.search(r'### 2\. 横向切片挖空对比表\s*```html\s*(<table[\s\S]+?</table>)\s*```', t_body)
        cloze_table_html = table_match.group(1).strip() if table_match else ""
        
        # 提取该考点的综合解析与口诀（从变体中提取通用口诀或主题口诀）
        first_mnemonic_match = re.search(r'\* \*\*秒杀口诀\*\*[：:]\s*(.+)', t_body)
        mnemonic = first_mnemonic_match.group(1).strip() if first_mnemonic_match else ""
        
        first_exp_match = re.search(r'\* \*\*题眼排除\*\*[：:]\s*(.+)', t_body)
        explanation = first_exp_match.group(1).strip() if first_exp_match else ""
        
        trap_match = re.search(r'\* \*\*过拟合陷阱\*\*[：:]\s*(.+)', t_body)
        trap = trap_match.group(1).strip() if trap_match else ""

        if cloze_table_html:
            cloze_notes.append({
                "id": f"CLOZE-{t_id}",
                "category": f"反过拟合 · {t_title.split('与')[0].split('（')[0].strip()}",
                "title": t_title,
                "content": cloze_table_html,
                "explanation": explanation,
                "mnemonic": mnemonic,
                "trap": trap,
                "subject": "法律法规" if ("法" in t_title or "监管" in t_title or "巴塞尔" in t_title or "收支" in t_title) else "个人理财"
            })

        # 2. 提取一题多变题目
        var_blocks = re.findall(r'#### \[(变体 \d+ · .+?)\] (ANTI-VAR-\d+)\s*\n([\s\S]+?)(?=\n#### \[|\n## 专题 |\n## 🏆 |\Z)', t_body)
        for var_tag, var_id, var_text in var_blocks:
            lines = [l.strip() for l in var_text.strip().split('\n') if l.strip()]
            q_lines = []
            options = {}
            ans = ""
            exp = ""
            mne = ""
            
            for line in lines:
                if re.match(r'^[A-E]\.\s*', line):
                    opt_letter = line[0]
                    opt_val = line[2:].strip()
                    options[opt_letter] = opt_val
                elif line.startswith('* **正确答案**') or line.startswith('**正确答案**'):
                    ans_match = re.search(r'\*\*([A-E]+)\*\*', line)
                    if ans_match:
                        ans = ans_match.group(1)
                    else:
                        ans = line.split('：')[-1].replace('*', '').strip()
                elif line.startswith('* **题眼排除**') or line.startswith('**题眼排除**'):
                    exp = line.split('：')[-1].strip()
                elif line.startswith('* **秒杀口诀**') or line.startswith('**秒杀口诀**'):
                    mne = line.split('：')[-1].strip()
                else:
                    if not options and not ans:
                        q_lines.append(line)
            
            q_text = " ".join(q_lines).strip()
            q_type = "多选题" if len(ans) > 1 else "单选题"
            
            objective_notes.append({
                "id": var_id,
                "type": q_type,
                "question": f"【{var_tag}】{q_text}",
                "options": options,
                "answer": ans,
                "explanation": exp,
                "mnemonic": mne,
                "trap": f"命题陷阱：针对【{t_title}】进行考点置换与干扰项扶正训练",
                "subject": "法律法规" if ("法" in t_title or "监管" in t_title or "巴塞尔" in t_title or "收支" in t_title) else "个人理财"
            })

    return cloze_notes, objective_notes

def sync_cloze_notes(cloze_notes):
    """同步对比挖空卡片到 Anki"""
    print(f"\n🚀 开始同步【对比挖空矩阵卡片】(共 {len(cloze_notes)} 组专题)...")
    added_count = 0
    updated_count = 0
    
    for cn in cloze_notes:
        existing_cards = anki_invoke("findCards", query=f'deck:"{CLOZE_DECK}" ID:{cn["id"]}')
        
        fields = {
            "ID": cn["id"],
            "考点分类": cn["category"],
            "考点标题": cn["title"],
            "挖空内容": cn["content"],
            "核心考点解析": cn["explanation"],
            "速记口诀": cn["mnemonic"],
            "避坑指南": cn["trap"]
        }
        
        tags = ["2026银行从业", "反过拟合", "横向切片对比", "Cloze挖空", cn["subject"]]
        
        if existing_cards:
            note_id = anki_invoke("cardsToNotes", cards=[existing_cards[0]])[0]
            anki_invoke("updateNoteFields", note={"id": note_id, "fields": fields})
            updated_count += 1
            print(f"  🔄 [已更新] {cn['id']} - {cn['title']}")
        else:
            note = {
                "deckName": CLOZE_DECK,
                "modelName": CLOZE_MODEL_NAME,
                "fields": fields,
                "tags": tags,
                "options": {"allowDuplicate": False}
            }
            nid = anki_invoke("addNote", note=note)
            added_count += 1
            print(f"  ✨ [新录入] {cn['id']} - {cn['title']} (Note #{nid})")
            
    print(f"✅ 对比挖空卡片同步完毕：新增 {added_count} 组，更新 {updated_count} 组。")
    return added_count, updated_count

def sync_objective_notes(objective_notes):
    """同步一题多变客观题卡片到 Anki"""
    print(f"\n🎯 开始同步【一题多变机考客观题】(共 {len(objective_notes)} 道变体题)...")
    added_count = 0
    updated_count = 0
    
    for q in objective_notes:
        existing_cards = anki_invoke("findCards", query=f'deck:"{OBJECTIVE_DECK}" ID:{q["id"]}')
        
        options = q["options"]
        fields = {
            "ID": q["id"],
            "题型": q["type"],
            "题干": q["question"],
            "选项A": options.get("A", ""),
            "选项B": options.get("B", ""),
            "选项C": options.get("C", ""),
            "选项D": options.get("D", ""),
            "选项E": options.get("E", ""),
            "正确答案": q["answer"],
            "核心考点解析": q["explanation"],
            "速记口诀": q["mnemonic"],
            "避坑指南": q["trap"]
        }
        
        tags = ["2026银行从业", "反过拟合", "一题多变", q["type"], q["subject"]]
        
        if existing_cards:
            note_id = anki_invoke("cardsToNotes", cards=[existing_cards[0]])[0]
            anki_invoke("updateNoteFields", note={"id": note_id, "fields": fields})
            updated_count += 1
            print(f"  🔄 [已更新] {q['id']} - {q['type']} ({q['question'][:24]}...)")
        else:
            note = {
                "deckName": OBJECTIVE_DECK,
                "modelName": OBJECTIVE_MODEL_NAME,
                "fields": fields,
                "tags": tags,
                "options": {"allowDuplicate": False}
            }
            nid = anki_invoke("addNote", note=note)
            added_count += 1
            print(f"  ✨ [新录入] {q['id']} - {q['type']} ({q['question'][:24]}...) (Note #{nid})")
            
    print(f"✅ 一题多变客观题同步完毕：新增 {added_count} 道，更新 {updated_count} 道。")
    return added_count, updated_count

def main():
    print("=====================================================================")
    print(" 🛡️  银行从业初级备考 · 反过拟合题集与对比挖空全自动同步引擎  🛡️")
    print("=====================================================================")
    
    if not os.path.exists(SOURCE_MD_PATH):
        print(f"❌ 错误：未找到题集文件 {SOURCE_MD_PATH}")
        sys.exit(1)
        
    ensure_cloze_model()
    ensure_decks_and_fsrs()
    
    cloze_notes, objective_notes = parse_anti_overfit_markdown(SOURCE_MD_PATH)
    print(f"📖 题集解析成功：已提取 {len(cloze_notes)} 组挖空对比表，{len(objective_notes)} 道一题多变机考题。")
    
    c_add, c_up = sync_cloze_notes(cloze_notes)
    o_add, o_up = sync_objective_notes(objective_notes)
    
    # 汇总检查
    cloze_card_count = len(anki_invoke("findCards", query=f'deck:"{CLOZE_DECK}"'))
    obj_card_count = len(anki_invoke("findCards", query=f'deck:"{OBJECTIVE_DECK}"'))
    
    print("\n=====================================================================")
    print(" 📊 【同步成果统计】")
    print(f"  - 牌组 1 [{CLOZE_DECK}]: 共 {cloze_card_count} 张 Cloze 挖空派生闪卡")
    print(f"  - 牌组 2 [{OBJECTIVE_DECK}]: 共 {obj_card_count} 张一题多变机考客观题卡")
    print(f"  - 总卡牌规模: {cloze_card_count + obj_card_count} 张高保真对抗卡")
    print("=====================================================================")

if __name__ == "__main__":
    main()
