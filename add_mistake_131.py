#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

card = {
    "id": "MISTAKE-131",
    "type": "多选题",
    "subject": "个人理财",
    "question": "下列关于年金系数的表述，正确的有（　　）。",
    "options": {
        "A": "期初普通年金现值系数一定大于期末普通年金现值系数",
        "B": "普通年金现值系数和复利终值系数互为倒数",
        "C": "复利终值系数和复利现值系数互为倒数",
        "D": "普通年金终值系数和普通年金现值系数互为倒数",
        "E": "普通年金终值系数和复利终值系数互为倒数"
    },
    "answer": "AC",
    "explanation": """<div style="background: rgba(37, 99, 235, 0.08); border-left: 4px solid #2563eb; padding: 10px 14px; margin-bottom: 12px; border-radius: 4px; line-height: 1.6;">
<div style="font-weight: 700; color: #1d4ed8; font-size: 14px; margin-bottom: 4px;">🎯 【你的疑问：为什么互为倒数？（大白话直观透视）】</div>
<div style="color: #334155; font-size: 13px; margin-bottom: 4px;">
<b>1. 生活直觉（去程放大，回程缩小）</b>：<br>
• 从<b>现在走向未来</b>（求终值）：把钱乘以膨胀倍数 <b>(1+r)^t</b>（放大）；<br>
• 从<b>未来折回现在</b>（求现值）：把钱除以膨胀倍数，即乘以 <b>1/(1+r)^t</b>（缩小）。<br>
• 就像今天去程翻了 2 倍（×2），回程要变回原样就必须乘 1/2！<b>乘数和还原数相乘等于 1，定义就是互为倒数！</b>
</div>
<div style="color: #334155; font-size: 13px;">
<b>2. 数学公式相乘等于 1</b>：<br>
复利终值系数 × 复利现值系数 = (1+r)^t × [1/(1+r)^t] = <b>1</b> ➔ 必然互为倒数！
</div>
</div>
<div style="line-height: 1.7; color: #334155;">
<b>【机考必背：金融学“三大黄金倒数家族”】</b><br>
1. <b>单笔复利对</b>：复利终值系数 ⟷ 复利现值系数；<br>
2. <b>年金现值对</b>：普通年金现值系数 ⟷ <b>投资回收系数（资本回收系数）</b>（用于房贷已知总额算每月月供）；<br>
3. <b>年金终值对</b>：普通年金终值系数 ⟷ <b>偿债基金系数</b>（用于已知未来要攒多少钱算每年存多少）。<br><br>
<b>【选项逐项剖析】</b><br>
• <b>A 项正确</b>：期初年金（先付年金）每笔钱比期末年金多滚 1 期利息，期初系数 = 期末系数 × (1+r) > 期末系数（r > 0）。<br>
• <b>B/D/E 项错误</b>：年金终值系数与年金现值系数差了 (1+r)^t 倍，绝不互为倒数；原题部分印刷选 AE 属答案排版乌龙，其自身解析亦确认仅复利终现值互为倒数，标准答案必选 <b>AC</b>！
</div>""",
    "mnemonic": "去乘来除积为一，终现互倒年金配",
    "trap": "⚠️ 避坑提醒：原题部分题库印刷答案标为 AE，但解析明确说明仅复利终现值互为倒数！年金终值系数的倒数是【偿债基金系数】，年金现值系数的倒数是【投资回收系数】，标准机考答案必须选 AC！"
}

with open("data/pending_anki_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

existing = [c for c in cards if c.get("id") == "MISTAKE-131"]
if not existing:
    cards.append(card)
    with open("data/pending_anki_cards.json", "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print("Added MISTAKE-131 to pending_anki_cards.json")
else:
    print("MISTAKE-131 already in pending_anki_cards.json")
