#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行从业初级备考 · 错题与知识盲区自动同步至 Anki 引擎
- 目标牌组: 等级考试::银行从业::[错题强化]盲区特训
- 卡牌模板: 银行从业·全真机考客观题
- 自动绑定 FSRS 记忆配置组并完成去重录入
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
DEFAULT_DECK = "等级考试::银行从业::[错题强化]盲区特训"
MODEL_NAME = "银行从业·全真机考客观题"
PRESET_NAME = "银行从业·科学记忆预设"

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

def ensure_deck_and_config(deck_name=DEFAULT_DECK):
    """确保目标牌组存在并绑定科学记忆预设"""
    decks = anki_invoke("deckNames")
    if deck_name not in decks:
        anki_invoke("createDeck", deck=deck_name)
        print(f"📦 已创建新错题强化牌组: {deck_name}")
    
    # 尝试绑定专属 FSRS 预设
    try:
        deck_config = anki_invoke("getDeckConfig", deck=deck_name)
        configs = anki_invoke("deckConfigNames")
        target_conf = next((c for c in configs if c.get("name") == PRESET_NAME), None)
        if target_conf and deck_config.get("id") != target_conf.get("id"):
            anki_invoke("setDeckConfigId", decks=[deck_name], configId=target_conf["id"])
            print(f"⚙️ 成功将牌组绑定至专属预设: {PRESET_NAME}")
    except Exception as e:
        # 非致命错误，忽略预设绑定告警
        pass

def add_mistake_note(q, deck_name=DEFAULT_DECK):
    """添加或更新单道错题卡片"""
    ensure_deck_and_config(deck_name)
    
    # 查重检测：按题干搜索是否已存在
    escaped_question = q["question"].replace('"', '\\"').replace(":", "\\:").strip()
    query = f'deck:"{deck_name}" "{escaped_question[:30]}"'
    existing_cards = anki_invoke("findCards", query=query)
    
    options = q.get("options", {})
    fields = {
        "ID": q.get("id", "MISTAKE-AUTO"),
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
    
    tags = ["2026银行从业", "错题强化", "盲区特训", q.get("type", "单选题")]
    if "subject" in q:
        tags.append(q["subject"])
    
    if existing_cards:
        # 已存在卡片，更新笔记字段
        note_id = anki_invoke("cardsToNotes", cards=[existing_cards[0]])[0]
        anki_invoke("updateNoteFields", note={"id": note_id, "fields": fields})
        print(f"🔄 卡片已存在，已更新 Note #{note_id} [{fields['ID']}]")
        return {"status": "updated", "note_id": note_id, "id": fields["ID"]}
    else:
        # 新增卡片
        note = {
            "deckName": deck_name,
            "modelName": MODEL_NAME,
            "fields": fields,
            "tags": tags
        }
        res_id = anki_invoke("addNote", note=note)
        print(f"✅ 成功注入错题卡片 Note #{res_id} [{fields['ID']}] 到 '{deck_name}'")
        return {"status": "created", "note_id": res_id, "id": fields["ID"]}

def add_mistakes_batch(questions, deck_name=DEFAULT_DECK):
    results = []
    for q in questions:
        res = add_mistake_note(q, deck_name)
        results.append(res)
    return results

def main():
    parser = argparse.ArgumentParser(description="银行从业错题自动注入 Anki 工具")
    parser.add_argument("--json", type=str, help="单个错题或错题列表的 JSON 字符串")
    parser.add_argument("--file", type=str, help="包含错题数据的 JSON 文件路径")
    parser.add_argument("--deck", type=str, default=DEFAULT_DECK, help="目标牌组名称")
    args = parser.parse_args()
    
    data = None
    if args.json:
        data = json.loads(args.json)
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print("💡 请提供 --json 或 --file 参数。")
        sys.exit(1)
        
    if isinstance(data, list):
        results = add_mistakes_batch(data, args.deck)
    else:
        results = [add_mistake_note(data, args.deck)]
        
    print(f"🎉 处理完成，共处理 {len(results)} 道错题。")

if __name__ == "__main__":
    main()
