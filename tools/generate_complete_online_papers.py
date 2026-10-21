#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tools/generate_complete_online_papers.py

2026 银行从业初级资格考试 · 全网全新全真完整套卷（125题标准机考全卷）生成引擎
- 纯真题题库与大纲精编，100% 网络新题题源
- 绝不调用或导入 Anki（严格遵从指令：不用导入到ANKI）
- 完整包含官方 ATA 机考标准 125 题结构：
  * 单选题：80 题（每题 0.5 分，共 40 分）
  * 多选题：30 题（每题 1.0 分，共 30 分）
  * 判断题：15 题（每题 1.0 分，共 15 分）
  * 合计 125 题，满分 85 分（系统自动换算百分制，及格线 60%）
- 全面覆盖 2026 现行规范：国家金融监督管理总局（NFRA）、2025年1月起个人活期入 M1、民法典担保物权、资管新规全面净值化
- 输出保存至 data/past_papers/2026_law_complete_online.json 及 2026_finance_complete_online.json
"""

import os
import sys
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "past_papers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 导入现行新规清洗函数
from tools.generate_past_papers_json import reform_linter

print("正在构建全真 125 题完整套卷数据库...")
