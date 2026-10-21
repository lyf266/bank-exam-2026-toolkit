#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

card = {
    "id": "MISTAKE-132",
    "type": "判断题",
    "subject": "个人理财",
    "question": "信托产品出现兑付困难时，信托公司可以按照产品净值垫资兑付。（　　）",
    "options": {
        "A": "正确",
        "B": "错误"
    },
    "answer": "B",
    "explanation": """<div style="background: rgba(37, 99, 235, 0.08); border-left: 4px solid #2563eb; padding: 10px 14px; margin-bottom: 12px; border-radius: 4px; line-height: 1.6;">
<div style="font-weight: 700; color: #1d4ed8; font-size: 14px; margin-bottom: 4px;">🎯 【你的疑问：这道题如果换成信托呢？】</div>
<div style="color: #334155; font-size: 13px; margin-bottom: 4px;">
<b>重点解答：换成信托，结论依然是【绝对错误】（严禁以任何形式垫资兑付）！</b><br>
很多考生受过去“信托刚兑”潜规则的影响，误以为信托公司有责任或权力兜底垫资，这是极其致命的认知盲区！
</div>
</div>
<div style="line-height: 1.7; color: #334155;">
<b>【三大法理与现行监管铁律】</b><br>
1. <b>信托属于《资管新规》法定统辖范畴</b>：<br>
   • 《资管新规》第 2 条明确将<b>“信托公司的资金信托”</b>全额纳入资产管理产品；<br>
   • 第 19 条明令禁止：<b>资产管理产品兑付困难时，受托人（信托公司）不得自行筹集资金或委托其他机构垫资兑付</b>！违者被直接定性为“刚性兑付违规”，面临停业与高额处罚。<br>
2. <b>司法审判红线（打破刚兑彻底法制化）</b>：<br>
   • 根据《信托法》与最高法《九民纪要》，信托财产独立于信托公司，<b>“卖者尽责、买者自负”</b>；<br>
   • 任何保底兜底协议、垫资兑付承诺在法律上一律<b>认定无效</b>！<br>
3. <b>关键易混概念：【垫资兑付（违规刚兑）】 vs 【过错赔偿（法定责任）】</b>：<br>
   • <b>垫资兑付（严厉禁止）</b>：信托项目因正常市场风险/商业风险亏损，信托公司拿自己的钱替客户填坑（破坏市场纪律，制造系统性风险）；<br>
   • <b>过错赔偿（合法合规）</b>：信托公司因违背尽职尽责义务（如虚假尽调、挪用资金、违规放贷等），依法承担民事赔偿责任。这是<b>侵权/违约赔偿</b>，绝非“垫资兑付”！
</div>""",
    "mnemonic": "卖者尽责买者负，信托垫资刚兑禁",
    "trap": "⚠️ 避坑提醒：看到“垫资兑付”四个字，无论是银行理财、信托产品、公募还是私募资管，一律判定为【错误】！资管新规下没有任何金融机构可以合法垫资刚兑！"
}

with open("data/pending_anki_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

existing = [c for c in cards if c.get("id") == "MISTAKE-132"]
if not existing:
    cards.append(card)
    with open("data/pending_anki_cards.json", "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print("Added MISTAKE-132 to pending_anki_cards.json")
else:
    print("MISTAKE-132 already in pending_anki_cards.json")
