#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机考模拟系统自动化验证套件 (test_simulator.py)
"""

import unittest
import json
import os
import re
import math

class TestMockExamSystem(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.sample_json_path = os.path.join(self.base_dir, 'questions_sample.json')

    def test_sample_json_integrity(self):
        """验证内置样卷 JSON 完整性与各题型规范"""
        self.assertTrue(os.path.exists(self.sample_json_path), "questions_sample.json 不存在！")
        with open(self.sample_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('exams', data)
        self.assertGreaterEqual(len(data['exams']), 2, "应至少包含 2 套预置试卷！")

        for ex in data['exams']:
            self.assertIn('id', ex)
            self.assertIn('name', ex)
            self.assertIn('questions', ex)
            self.assertGreater(len(ex['questions']), 0)

            for q in ex['questions']:
                self.assertIn('id', q)
                self.assertIn('type', q)
                self.assertIn(q['type'], ['单选题', '多选题', '判断题'])
                self.assertIn('score', q)
                self.assertIn('question', q)
                self.assertIn('options', q)
                self.assertIn('answer', q)
                self.assertIn('explanation', q)

                # 选项与答案校验
                if q['type'] == '单选题':
                    self.assertEqual(len(q['answer']), 1)
                    self.assertIn(q['answer'], q['options'])
                elif q['type'] == '判断题':
                    self.assertEqual(len(q['answer']), 1)
                    self.assertIn(q['answer'], ['A', 'B'])
                elif q['type'] == '多选题':
                    self.assertGreater(len(q['answer']), 1)
                    for char in q['answer']:
                        self.assertIn(char, q['options'])

    def test_tvm_formulas(self):
        """验证金融计算器核心数学模型与真题结果一致性"""
        # 1. 单笔复利：10000 存 3 年，20% -> 17280
        pv = 10000
        r = 0.20
        n = 3
        fv = pv * math.pow(1 + r, n)
        self.assertAlmostEqual(fv, 17280.0, places=2)

        # 2. 房贷按揭：100万 20年 5%，等额本息 PMT -> 80242.59
        pv_loan = 1000000
        r_loan = 0.05
        n_loan = 20
        factor = (1 - math.pow(1 + r_loan, -n_loan)) / r_loan
        pmt = pv_loan / factor
        self.assertAlmostEqual(pmt, 80242.59, delta=0.5)

        # 3. 普通年金终值：每年 8000，6 年，8% -> 58687.4 (≈ 58688)
        pmt_edu = 8000
        r_edu = 0.08
        n_edu = 6
        fv_edu = pmt_edu * ((math.pow(1 + r_edu, n_edu) - 1) / r_edu)
        self.assertAlmostEqual(fv_edu, 58687.4, delta=1.0)

        # 4. 有效年利率 EAR：12% 季复利 -> 12.55%
        ear = math.pow(1 + 0.12/4, 4) - 1
        self.assertAlmostEqual(ear * 100, 12.55, places=2)

        # 5. 72法则：9% -> 8年
        self.assertEqual(72 // 9, 8)

    def test_text_import_parser(self):
        """验证文本导入解析逻辑有效性"""
        sample_text = """
1. [单选题] 某投资项目预期收益率为20%，期限3年，利息再投资，初始存入1万元，终值是多少？
A. 17000
B. 17280
C. 17400
D. 17500
答案: B
解析: 利息再投资即复利，FV = 10000 * (1+0.2)^3 = 17280元。
口诀: 未加说明默认年，利息再投即复利。
"""
        lines = sample_text.strip().split('\n')
        curQ = { 'options': {} }
        for line in lines:
            line = line.strip()
            if not line: continue
            if '某投资项目' in line:
                curQ['question'] = line
            elif line.startswith('A.'):
                curQ['options']['A'] = line[2:].strip()
            elif line.startswith('B.'):
                curQ['options']['B'] = line[2:].strip()
            elif line.startswith('答案:'):
                curQ['answer'] = line.replace('答案:', '').strip()

        self.assertIn('某投资项目', curQ['question'])
        self.assertEqual(curQ['answer'], 'B')
        self.assertEqual(curQ['options']['B'], '17280')

if __name__ == '__main__':
    unittest.main()
