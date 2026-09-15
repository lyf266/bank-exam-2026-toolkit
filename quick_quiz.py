#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业资格考试 · 本地高频考点极速自测工具 (quick_quiz.py)
特性：
- 零外部依赖（纯 Python 3 标准库）
- 100% 依据 2024-2026 机构改革与资管新规编撰
- 包含即时判定、解析及专属【15字助记口诀】
- 支持非交互自动化测试模式 (--test)
"""

import sys
import argparse
import random

QUESTIONS_LAW = [
    {
        "id": "LAW-01",
        "type": "单选题",
        "question": "根据 2023 年党和国家机构改革方案，下列哪一机构负责对银行业金融机构实施统一监督管理？",
        "options": {
            "A": "中国人民银行",
            "B": "国家金融监督管理总局",
            "C": "中国证券监督管理委员会",
            "D": "国务院金融稳定发展委员会"
        },
        "answer": "B",
        "explanation": "2023年机构改革后，撤销银保监会，组建国家金融监督管理总局（NFRA），统一负责除证券业之外的金融业监管。",
        "mnemonic": "银保监撤销，金监总局统管日常。"
    },
    {
        "id": "LAW-02",
        "type": "单选题",
        "question": "根据巴塞尔资本协议 Ⅲ 及我国银行业监管要求，商业银行的核心一级资本充足率最低要求为多少？",
        "options": {
            "A": "4%",
            "B": "5%",
            "C": "6%",
            "D": "8%"
        },
        "answer": "B",
        "explanation": "我国商业银行资本充足率三级底线为：核心一级资本充足率不得低于 5%；一级资本充足率不得低于 6%；总资本充足率不得低于 8%（储备资本另加 2.5%）。",
        "mnemonic": "核心一五、一级六、总资本八加两点五。"
    },
    {
        "id": "LAW-03",
        "type": "单选题",
        "question": "在商业银行的贷款五级分类中，借款人无法足额偿还本息，即使执行担保也肯定要造成较大损失的贷款属于哪一类？",
        "options": {
            "A": "关注贷款",
            "B": "次级贷款",
            "C": "可疑贷款",
            "D": "损失贷款"
        },
        "answer": "C",
        "explanation": "五级分类为：正常、关注、次级（部分损失）、可疑（较大损失）、损失（极少或无）。次级、可疑、损失三类合称不良贷款。",
        "mnemonic": "正关次疑损，后三为不良，疑即大损。"
    },
    {
        "id": "LAW-04",
        "type": "判断题",
        "question": "商业银行的同业拆借业务期限较短，拆借资金属于无担保的信用资金。",
        "options": {
            "A": "正确",
            "B": "错误"
        },
        "answer": "A",
        "explanation": "同业拆借是银行等金融机构之间调剂临时资金余缺的短期、纯信用资金融通，不设担保。",
        "mnemonic": "同业拆借时间短，纯拼信用不抵押。"
    },
    {
        "id": "LAW-05",
        "type": "单选题",
        "question": "根据我国《民法典》及银行业合规要求，下列哪项财产不得用于抵押？",
        "options": {
            "A": "债务人所有的房屋及其他地上定着物",
            "B": "依法可以转让的建设用地使用权",
            "C": "土地所有权",
            "D": "生产设备、原材料"
        },
        "answer": "C",
        "explanation": "我国土地所有权属于国家或集体所有，严禁抵押；能够抵押的仅为土地使用权。",
        "mnemonic": "所有权归公不可押，使用权可设抵押。"
    },
    {
        "id": "LAW-06",
        "type": "单选题",
        "question": "根据反洗钱法律法规，金融机构客户身份资料和交易记录自交易记账当年计起至少应当保存多少年？",
        "options": {
            "A": "3年",
            "B": "5年",
            "C": "10年",
            "D": "15年"
        },
        "answer": "B",
        "explanation": "金融机构反洗钱三项基本制度之一的资料保存制度规定，身份资料及交易记录至少保存 5 年。",
        "mnemonic": "反洗钱查底细，账本凭证至少五年。"
    }
]

QUESTIONS_FINANCE = [
    {
        "id": "FIN-01",
        "type": "单选题",
        "question": "根据资管新规及商业银行理财业务管理规定，下列关于银行理财产品的说法正确的是：",
        "options": {
            "A": "银行可以发行预期收益型的保本理财产品",
            "B": "商业银行理财产品必须实行净值化管理，严禁刚性兑付",
            "C": "银行对低风险客户可承诺理财最低收益率",
            "D": "理财产品资金可直接无限制投资于未上市企业股权"
        },
        "answer": "B",
        "explanation": "资管新规彻底终结了预期收益型和保本理财时代，商业银行理财产品必须净值化，不得承诺保本保息，打破刚兑。",
        "mnemonic": "资管新规破刚兑，净值波动自负盈亏。"
    },
    {
        "id": "FIN-02",
        "type": "单选题",
        "question": "已知某理财产品年化复利收益率为 10%，某客户初始投资 10,000 元，期限 2 年，则 2 年后的终值 (FV) 为多少元？",
        "options": {
            "A": "12,000 元",
            "B": "12,100 元",
            "C": "11,000 元",
            "D": "12,210 元"
        },
        "answer": "B",
        "explanation": "复利终值公式 FV = PV * (1 + r)^n = 10000 * (1 + 0.1)^2 = 10000 * 1.21 = 12,100 元。",
        "mnemonic": "复利滚雪球，乘方计算不含糊。"
    },
    {
        "id": "FIN-03",
        "type": "单选题",
        "question": "在个人生命周期理论中，处于“家庭形成期”（年轻夫妇、有学龄前子女）的客户，其理财主要特征通常是：",
        "options": {
            "A": "收入稳定增长，追求高资本增值，注重子女教育金与房屋贷款规划",
            "B": "收入达到巅峰，资产配置以绝对保本、退休年金为主",
            "C": "完全依靠养老金生活，风险承受能力极低",
            "D": "单身一人，无家庭负担，随意消费"
        },
        "answer": "A",
        "explanation": "家庭形成期伴随着买房负债与子女成长，收入爬坡，对保障和未来教育支出规划需求最迫切。",
        "mnemonic": "成长期肩挑房与娃，攻守兼备保未来。"
    },
    {
        "id": "FIN-04",
        "type": "判断题",
        "question": "根据金融消费者权益保护原则，商业银行在向客户销售理财产品时，可以将高风险等级的产品推荐给保守型（低风险承受能力）客户，只要客户签字确认免责即可。",
        "options": {
            "A": "正确",
            "B": "错误"
        },
        "answer": "B",
        "explanation": "商业银行必须严格遵守适当性匹配原则（KYC），严禁将高于客户风险承受能力的产品销售给该客户，签字免责条款无效。",
        "mnemonic": "适当性匹配是红线，低风客户禁买高风。"
    }
]

def run_quiz(questions, non_interactive=False):
    print("=" * 65)
    print(f"🎯 2026 银行从业极速自测模式启动 (共 {len(questions)} 题)")
    print("=" * 65)
    
    score = 0
    total = len(questions)
    
    for idx, q in enumerate(questions, 1):
        print(f"\n【第 {idx}/{total} 题】[{q['type']}] {q['question']}")
        for opt_k in sorted(q['options'].keys()):
            print(f"   {opt_k}. {q['options'][opt_k]}")
        
        if non_interactive:
            user_choice = q['answer']
            print(f"👉 [测试模式] 自动输入正确答案: {user_choice}")
        else:
            while True:
                try:
                    user_choice = input("\n👉 请输入你的选项 (A/B/C/D 或 q 退出): ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    print("\n测试已中断。")
                    return
                if user_choice == 'Q':
                    print("\n测试已提前结束。")
                    return
                if user_choice in q['options']:
                    break
                print("⚠️ 输入无效，请输入选项对应字母（如 A、B）。")
        
        if user_choice == q['answer']:
            print("✅ 【回答正确！】")
            score += 1
        else:
            print(f"❌ 【回答错误】 正确答案是: {q['answer']}")
        
        print(f"💡 考点解析：{q['explanation']}")
        print(f"🔑 助记口诀：{q['mnemonic']}")
        print("-" * 65)
        
    print("\n" + "=" * 65)
    print(f"🎉 测验完成！得分：{score} / {total} (正确率: {score/total*100:.1f}%)")
    if score == total:
        print("🌟 满分通关！这几个高频考点你已经形成肌肉记忆。")
    elif score / total >= 0.6:
        print("🟢 达到 60% 稳过线！继续保持午后 45 分钟刷题节奏。")
    else:
        print("🟠 未达及格线，建议复习错题解析中的【助记口诀】。")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="2026 银行从业高频自测 CLI")
    parser.add_argument("--test", action="store_true", help="自动化测试运行")
    parser.add_argument("--law", action="store_true", help="仅测《法律法规》")
    parser.add_argument("--finance", action="store_true", help="仅测《个人理财》")
    args = parser.parse_args()

    if args.law:
        pool = QUESTIONS_LAW
    elif args.finance:
        pool = QUESTIONS_FINANCE
    else:
        pool = QUESTIONS_LAW + QUESTIONS_FINANCE

    if args.test:
        run_quiz(pool, non_interactive=True)
        sys.exit(0)
    
    run_quiz(pool, non_interactive=False)

if __name__ == "__main__":
    main()
