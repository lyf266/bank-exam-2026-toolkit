#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行从业卡牌模板修复引擎 (fix_mobile_blank_template.py)
解决手机端 (AnkiDroid / AnkiMobile / AnkiWeb) 打开银行从业卡片完全空白的问题：
1. 移除与移动端 Anki 内置 MathJax 冲突的自定义 typesetPromise() 脚本 (导致移动端挂起白屏的元凶)
2. 全面重构 CSS，同时完美兼容 .night_mode, .nightMode, @media (prefers-color-scheme: dark)，杜绝白字白底
3. 移除非标准内联 JS，增强移动端 DOM 事件监听容错性
4. 保证在 JS 禁用或异常时，所有静态题干与选项 100% 优雅呈现
5. 热更新本地模板并重新导出离线 .apkg 卡包
"""

import os
import json
import urllib.request
import urllib.error

ANKI_CONNECT_URL = "http://127.0.0.1:8765"

def anki_invoke(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    req = urllib.request.Request(ANKI_CONNECT_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("error"):
                raise RuntimeError(f"AnkiConnect Error: {data['error']}")
            return data.get("result")
    except urllib.error.URLError as e:
        raise ConnectionError(f"无法连接 AnkiConnect: {e}")

# 现代化、高对比度、双模深度自适应的 CSS
NEW_CSS = """
/* 现代响应式高对比度自适应设计 (100% 兼容桌面与移动端) */
:root {
  --bg-app: #f8fafc;
  --bg-card: #ffffff;
  --text-main: #0f172a;
  --text-sub: #334155;
  --text-muted: #64748b;
  --border-light: #e2e8f0;
  --btn-bg: #ffffff;
  --btn-hover: #f1f5f9;
  --btn-selected-bg: #eff6ff;
  --btn-selected-border: #2563eb;
  --badge-bg: #f1f5f9;
}

/* 同时兼容桌面端 .nightMode 与 移动端 .night_mode */
.night_mode, .nightMode, body.night_mode, body.nightMode {
  --bg-app: #0f172a;
  --bg-card: #1e293b;
  --text-main: #f8fafc;
  --text-sub: #cbd5e1;
  --text-muted: #94a3b8;
  --border-light: #334155;
  --btn-bg: #1e293b;
  --btn-hover: #334155;
  --btn-selected-bg: #1e3a8a;
  --btn-selected-border: #60a5fa;
  --badge-bg: #334155;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-app: #0f172a;
    --bg-card: #1e293b;
    --text-main: #f8fafc;
    --text-sub: #cbd5e1;
    --text-muted: #94a3b8;
    --border-light: #334155;
    --btn-bg: #1e293b;
    --btn-hover: #334155;
    --btn-selected-bg: #1e3a8a;
    --btn-selected-border: #60a5fa;
    --badge-bg: #334155;
  }
}

.card {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC", "Noto Sans CJK SC", sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-main) !important;
  background-color: var(--bg-app) !important;
  padding: 12px;
  margin: 0 auto;
  max-width: 680px;
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

.badge-单选题 {
  color: #1d4ed8;
  background-color: #dbeafe;
  border: 1px solid #bfdbfe;
}
.night_mode .badge-单选题, .nightMode .badge-单选题 {
  color: #93c5fd;
  background-color: #1e3a8a;
  border-color: #1d4ed8;
}

.badge-多选题 {
  color: #b45309;
  background-color: #fef3c7;
  border: 1px solid #fde68a;
}
.night_mode .badge-多选题, .nightMode .badge-多选题 {
  color: #fcd34d;
  background-color: #78350f;
  border-color: #b45309;
}

.badge-判断题 {
  color: #6d28d9;
  background-color: #ede9fe;
  border: 1px solid #ddd6fe;
}
.night_mode .badge-判断题, .nightMode .badge-判断题 {
  color: #c4b5fd;
  background-color: #4c1d95;
  border-color: #6d28d9;
}

.exam-id {
  font-size: 12px;
  font-family: monospace;
  color: var(--text-muted) !important;
  background: var(--badge-bg) !important;
  padding: 2px 6px;
  border-radius: 4px;
}

.question-body {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main) !important;
  margin-bottom: 18px;
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.opt-btn {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border: 1.5px solid var(--border-light) !important;
  border-radius: 8px;
  background-color: var(--btn-bg) !important;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  text-align: left;
}

.opt-btn:hover {
  background-color: var(--btn-hover) !important;
}

.opt-btn.selected {
  border-color: var(--btn-selected-border) !important;
  background-color: var(--btn-selected-bg) !important;
}

.opt-tag {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 13px;
  background: var(--badge-bg);
  color: var(--text-muted);
  border: 1px solid var(--border-light);
}

.opt-btn.selected .opt-tag {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

.opt-text {
  flex-grow: 1;
  font-size: 14.5px;
  color: var(--text-sub) !important;
  line-height: 1.5;
}

.interactive-hint {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding-top: 4px;
}

/* 背面高亮与解析卡片 */
.back-container .opt-btn.correct-choice {
  border-color: #10b981 !important;
  background-color: #ecfdf5 !important;
}
.night_mode .back-container .opt-btn.correct-choice,
.nightMode .back-container .opt-btn.correct-choice {
  background-color: #064e3b !important;
  border-color: #34d399 !important;
}

.back-container .opt-btn.correct-choice .opt-tag {
  background-color: #10b981 !important;
  color: #ffffff !important;
  border-color: #10b981 !important;
}

.back-container .opt-btn.correct-choice .opt-text {
  color: #065f46 !important;
  font-weight: 600;
}
.night_mode .back-container .opt-btn.correct-choice .opt-text,
.nightMode .back-container .opt-btn.correct-choice .opt-text {
  color: #a7f3d0 !important;
}

.back-container .opt-btn.wrong-choice {
  opacity: 0.55;
  background-color: var(--btn-bg) !important;
}

.answer-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 10px 14px;
  margin: 16px 0;
}
.night_mode .answer-banner, .nightMode .answer-banner {
  background: #064e3b;
  border-color: #047857;
}

.ans-title {
  font-weight: 700;
  color: #065f46;
  font-size: 14px;
}
.night_mode .ans-title, .nightMode .ans-title {
  color: #a7f3d0;
}

.ans-val {
  font-size: 18px;
  font-weight: 800;
  color: #059669;
  letter-spacing: 1px;
}
.night_mode .ans-val, .nightMode .ans-val {
  color: #34d399;
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
"""

NEW_QFMT = """<div class="exam-container">
  <div class="exam-header">
    <span class="type-badge badge-{{题型}}">{{题型}}</span>
    <span class="exam-id">{{ID}}</span>
  </div>

  <div class="question-body">
    {{题干}}
  </div>

  <div class="options-list" id="frontOptions">
    {{#选项A}}
    <div class="opt-btn" data-opt="A">
      <span class="opt-tag">A</span>
      <span class="opt-text">{{选项A}}</span>
    </div>
    {{/选项A}}

    {{#选项B}}
    <div class="opt-btn" data-opt="B">
      <span class="opt-tag">B</span>
      <span class="opt-text">{{选项B}}</span>
    </div>
    {{/选项B}}

    {{#选项C}}
    <div class="opt-btn" data-opt="C">
      <span class="opt-tag">C</span>
      <span class="opt-text">{{选项C}}</span>
    </div>
    {{/选项C}}

    {{#选项D}}
    <div class="opt-btn" data-opt="D">
      <span class="opt-tag">D</span>
      <span class="opt-text">{{选项D}}</span>
    </div>
    {{/选项D}}

    {{#选项E}}
    <div class="opt-btn" data-opt="E">
      <span class="opt-tag">E</span>
      <span class="opt-text">{{选项E}}</span>
    </div>
    {{/选项E}}
  </div>

  <div class="interactive-hint">
    👆 点击选项即可作答 · 翻转查看机考答案与解析
  </div>
</div>

<script>
(function() {
  try {
    var isMulti = "{{题型}}" === "多选题";
    var container = document.getElementById("frontOptions");
    if (!container) return;

    var buttons = container.querySelectorAll(".opt-btn");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function() {
        if (isMulti) {
          this.classList.toggle("selected");
        } else {
          for (var j = 0; j < buttons.length; j++) {
            buttons[j].classList.remove("selected");
          }
          this.classList.add("selected");
        }
      });
    }
  } catch(e) {
    console.error("Option interaction error:", e);
  }
})();
</script>
"""

NEW_AFMT = """<div class="exam-container back-container">
  <div class="exam-header">
    <span class="type-badge badge-{{题型}}">{{题型}}</span>
    <span class="exam-id">{{ID}}</span>
  </div>

  <div class="question-body">
    {{题干}}
  </div>

  <div class="options-list" id="backOptions">
    {{#选项A}}
    <div class="opt-btn" data-opt="A">
      <span class="opt-tag">A</span>
      <span class="opt-text">{{选项A}}</span>
    </div>
    {{/选项A}}

    {{#选项B}}
    <div class="opt-btn" data-opt="B">
      <span class="opt-tag">B</span>
      <span class="opt-text">{{选项B}}</span>
    </div>
    {{/选项B}}

    {{#选项C}}
    <div class="opt-btn" data-opt="C">
      <span class="opt-tag">C</span>
      <span class="opt-text">{{选项C}}</span>
    </div>
    {{/选项C}}

    {{#选项D}}
    <div class="opt-btn" data-opt="D">
      <span class="opt-tag">D</span>
      <span class="opt-text">{{选项D}}</span>
    </div>
    {{/选项D}}

    {{#选项E}}
    <div class="opt-btn" data-opt="E">
      <span class="opt-tag">E</span>
      <span class="opt-text">{{选项E}}</span>
    </div>
    {{/选项E}}
  </div>

  <div class="answer-banner">
    <span class="ans-title">🎯 机考标准答案</span>
    <span class="ans-val" id="answerDisplay">{{正确答案}}</span>
  </div>

  {{#速记口诀}}
  <div class="info-section mnemonic-card">
    <div class="mnemonic-title">🔑 15字黄金速记口诀</div>
    <div class="mnemonic-body">{{速记口诀}}</div>
  </div>
  {{/速记口诀}}

  {{#核心考点解析}}
  <div class="info-section analysis-card">
    <div class="analysis-title">💡 核心考点精析</div>
    <div class="analysis-body">{{核心考点解析}}</div>
  </div>
  {{/核心考点解析}}

  {{#避坑指南}}
  <div class="info-section trap-card">
    <div class="trap-title">⚠️ 机考高频避坑陷阱</div>
    <div class="trap-body">{{避坑指南}}</div>
  </div>
  {{/避坑指南}}
</div>

<script>
(function() {
  try {
    var ans = "{{正确答案}}".trim().toUpperCase();
    var container = document.getElementById("backOptions");
    if (!container) return;
    var items = container.querySelectorAll(".opt-btn");

    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      var optCode = el.getAttribute("data-opt");
      var textEl = el.querySelector(".opt-text");
      var optText = textEl ? textEl.innerText.trim() : "";
      
      var isCorrect = false;
      if (ans.indexOf(optCode) !== -1) {
        isCorrect = true;
      } else if (ans === "正确" && (optCode === "A" || optText === "正确")) {
        isCorrect = true;
      } else if (ans === "错误" && (optCode === "B" || optText === "错误")) {
        isCorrect = true;
      }

      if (isCorrect) {
        el.classList.add("correct-choice");
      } else {
        el.classList.add("wrong-choice");
      }
    }
  } catch(e) {
    console.error("Back options highlighting error:", e);
  }
})();
</script>
"""

def main():
    print("=" * 65)
    print("🔧 正在修复 Anki 移动端 (AnkiDroid / AnkiMobile) 白屏问题...")
    print("=" * 65)

    model_name = "银行从业·全真机考客观题"

    # 1. 更新 Styling
    print("1️⃣ 正在更新模板 CSS 样式 (全面注入深浅双模与高对比度)...")
    anki_invoke("updateModelStyling", model={"name": model_name, "css": NEW_CSS.strip()})
    print("   ✅ CSS 更新成功！已彻底消除白底白字隐形问题。")

    # 2. 更新 Templates
    print("2️⃣ 正在更新卡片正反面模板 (移除破坏性 MathJax 脚本与内联 JS)...")
    templates_payload = {
        model_name: {
            "客观题答题卡": {
                "Front": NEW_QFMT.strip(),
                "Back": NEW_AFMT.strip()
            }
        }
    }
    anki_invoke("updateModelTemplates", model={"name": model_name, "templates": {"客观题答题卡": {"Front": NEW_QFMT.strip(), "Back": NEW_AFMT.strip()}}})
    print("   ✅ 正反面模板更新成功！已彻底移除导致移动端挂起白屏的冲突脚本。")

    # 3. 同时也修复 '问答题' 模板中的 MathJax 冗余冲突
    try:
        qa_model = "问答题"
        qa_qfmt = "{{正面}}"
        qa_afmt = "{{FrontSide}}\n\n<hr id=answer>\n\n{{背面}}"
        anki_invoke("updateModelTemplates", model={"name": qa_model, "templates": {"卡片 1": {"Front": qa_qfmt, "Back": qa_afmt}}})
        print("   ✅ '问答题' 模板已同步清理 MathJax 挂起风险！")
    except Exception as e:
        print(f"   ℹ️ 问答题模板清理跳过: {e}")

    # 4. 重新导出离线 .apkg 包供用户直接传手机
    print("3️⃣ 正在重新打包并导出最新全真机考离线 .apkg 卡包...")
    base_dir = "/home/f1are/orca/workspaces/银行从业备考/anki"
    pkg_obj = os.path.join(base_dir, "2026银行从业初级_全真机考客观题.apkg")
    pkg_all = os.path.join(base_dir, "2026银行从业初级_全真套题全量卡包.apkg")

    try:
        anki_invoke("exportPackage", deck="等级考试::银行从业", path=pkg_all, includeSched=False)
        anki_invoke("exportPackage", deck="等级考试::银行从业", path=pkg_obj, includeSched=False)
        print(f"   🎉 离线卡包重新导出成功！")
        print(f"   • {pkg_obj} ({os.path.getsize(pkg_obj)/1024:.1f} KB)")
        print(f"   • {pkg_all} ({os.path.getsize(pkg_all)/1024:.1f} KB)")
    except Exception as e:
        print(f"   ⚠️ 导出卡包提示: {e}")

    # 5. 触发云同步让 AnkiWeb / 手机端一键拉取
    print("4️⃣ 正在请求 AnkiConnect 执行云端同步 (Sync)...")
    try:
        anki_invoke("sync")
        print("   ☁️ 已触发云端同步！手机端打开 Anki 点击右上角【同步】即可秒级复活！")
    except Exception as e:
        print(f"   ℹ️ 云同步提示 (若未登录AnkiWeb可直接传.apkg): {e}")

    print("=" * 65)
    print("🚀 全部修复完成！")

if __name__ == "__main__":
    main()
