#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行从业初级备考 · [专题突破]非TVM计算特训牌组自动同步引擎 (sync_non_tvm_deck.py)
-----------------------------------------------------------------------------
功能：
1. 自动在本地 Anki 中创建并绑定专属目标牌组：
   - 等级考试::银行从业::[专题突破]非TVM计算特训
2. 绑定《银行从业·科学记忆预设》(FSRS 算法)；
3. 从 data/deck_non_tvm_calculation.json 读取 10 道无法使用 TVM 计算的机考真题；
4. 增量去重录入，保障格式无损。
"""

import os
import sys
import json
import urllib.request
import urllib.error

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
TARGET_DECK = "等级考试::银行从业::[专题突破]非TVM计算特训"
MODEL_NAME = "银行从业·全真机考客观题"
PRESET_NAME = "银行从业·科学记忆预设"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "deck_non_tvm_calculation.json")

def anki_invoke(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if len(res) == 2 and "error" in res and res["error"] is not None:
                raise Exception(res["error"])
            return res.get("result")
    except urllib.error.URLError as e:
        raise ConnectionError(f"无法连接到 AnkiConnect ({ANKI_CONNECT_URL})，请确认本地 Anki 正在运行: {e}")

def ensure_deck_and_config(deck_name=TARGET_DECK):
    """确保目标牌组存在并绑定科学记忆预设"""
    decks = anki_invoke("deckNames")
    if deck_name not in decks:
        anki_invoke("createDeck", deck=deck_name)
        print(f"📦 已创建新专题突破牌组: {deck_name}")
    
    try:
        deck_config = anki_invoke("getDeckConfig", deck=deck_name)
        configs = anki_invoke("getDeckConfig", deck="Default")
        # 尝试绑定专属 FSRS 预设
        all_configs = anki_invoke("getDeckConfigs")
        target_conf = next((c for c in all_configs if c.get("name") == PRESET_NAME), None)
        if target_conf and deck_config.get("id") != target_conf.get("id"):
            anki_invoke("setDeckConfigId", decks=[deck_name], configId=target_conf["id"])
            print(f"⚙️ 成功将牌组绑定至专属预设: {PRESET_NAME}")
    except Exception:
        pass

def add_or_update_note(q, deck_name=TARGET_DECK):
    existing_cards = anki_invoke("findCards", query=f'deck:"{deck_name}" ID:{q["id"]}')
    options = q.get("options", {})
    fields = {
        "ID": q["id"],
        "题型": q.get("type", "单选题"),
        "题干": q["question"],
        "选项A": options.get("A", ""),
        "选项B": options.get("B", ""),
        "选项C": options.get("C", ""),
        "选项D": options.get("D", ""),
        "选项E": options.get("E", ""),
        "正确答案": q.get("answer", ""),
        "核心考点解析": q.get("explanation", ""),
        "速记口诀": q.get("mnemonic", ""),
        "避坑指南": q.get("trap", "")
    }
    tags = ["2026银行从业", "非TVM计算特训", "专题突破", q.get("type", "单选题"), q.get("subject", "个人理财")]

    if existing_cards:
        note_id = anki_invoke("cardsToNotes", cards=[existing_cards[0]])[0]
        anki_invoke("updateNoteFields", note={"id": note_id, "fields": fields})
        print(f"🔄 更新卡片 Note #{note_id} [{fields['ID']}]")
        return {"status": "updated", "id": fields["ID"]}
    else:
        note = {
            "deckName": deck_name,
            "modelName": MODEL_NAME,
            "fields": fields,
            "tags": tags
        }
        res_id = anki_invoke("addNote", note=note)
        print(f"✅ 成功注入卡片 Note #{res_id} [{fields['ID']}]")
        return {"status": "created", "id": fields["ID"]}

def main():
    if not os.path.exists(DATA_FILE):
        print(f"❌ 找不到数据文件: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"🚀 开始同步《非TVM计算特训》题集（共 {len(questions)} 道题目）...")
    try:
        ensure_deck_and_config(TARGET_DECK)
    except ConnectionError as e:
        print(f"💡 提示：{e}")
        print("📁 考题牌组数据已安全保存在本地: data/deck_non_tvm_calculation.json")
        print("👉 请在打开本地 Anki 桌面端后，运行以下命令即可一键无损同步：")
        print(f"   python3 {os.path.basename(__file__)}")
        return

    success_count = 0
    for q in questions:
        try:
            add_or_update_note(q, TARGET_DECK)
            success_count += 1
        except Exception as e:
            print(f"⚠️ 处理 {q.get('id')} 失败: {e}")

    print(f"🎉 处理完成，成功同步 {success_count}/{len(questions)} 道题目到牌组 '{TARGET_DECK}'！")

if __name__ == "__main__":
    main()
