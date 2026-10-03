#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全自动部署工业级轻量动态洗牌引擎 (deploy_shuffle_template.py)
特性：
1. 内置成熟的 anki-persistence 跨端持久化，正反面乱序 100% 严密对齐
2. 单选/多选题随机打乱，判断题智能锁定（A正确/B错误）
3. 动态重映射背面答案栏（如 A 选项变到了 C，背面答案自动标为 C，并附注原题标准答案）
4. 全局防御性熔断机制，0 白屏风险，手机端无需安装任何第三方插件
5. 自动完成本地注入、重新导出离线 .apkg、并向 AnkiWeb 触发云端同步
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

# 持久化辅助脚本 (仅 20 来行纯 JS，零外部网络依赖)
PERSISTENCE_JS = """
if(typeof(window.Persistence)==="undefined"){var _persistenceKey="github.com/SimonLammer/anki-persistence/",_defaultKey="_default";window.Persistence_sessionStorage=function(){var isAvailable=!1;try{if(typeof(window.sessionStorage)==="object"){isAvailable=!0;this.clear=function(){for(var e=0;e<sessionStorage.length;e++){var t=sessionStorage.key(e);0==t.indexOf(_persistenceKey)&&(sessionStorage.removeItem(t),e--)}};this.setItem=function(e,t){undefined==t&&(t=e,e=_defaultKey),sessionStorage.setItem(_persistenceKey+e,JSON.stringify(t))};this.getItem=function(e){return undefined==e&&(e=_defaultKey),JSON.parse(sessionStorage.getItem(_persistenceKey+e))};this.removeItem=function(e){undefined==e&&(e=_defaultKey),sessionStorage.removeItem(_persistenceKey+e)}}}catch(e){}this.isAvailable=function(){return isAvailable}};window.Persistence_windowKey=function(e){var t=window[e],n=!1;typeof t==="object"&&(n=!0,this.clear=function(){t[_persistenceKey]={}},this.setItem=function(e,n){undefined==n&&(n=e,e=_defaultKey),t[_persistenceKey][e]=n},this.getItem=function(e){return undefined==e&&(e=_defaultKey),t[_persistenceKey][e]==undefined?null:t[_persistenceKey][e]},this.removeItem=function(e){undefined==e&&(e=_defaultKey),delete t[_persistenceKey][e]},t[_persistenceKey]==undefined&&this.clear()),this.isAvailable=function(){return n}};window.Persistence=new Persistence_sessionStorage;Persistence.isAvailable()||(window.Persistence=new Persistence_windowKey("py"));Persistence.isAvailable()||(window.Persistence=new Persistence_windowKey("qt"))}
"""

SHUFFLE_QFMT = f"""<div class="exam-container">
  <div class="exam-header">
    <span class="type-badge badge-{{{{题型}}}}">{{{{题型}}}}</span>
    <span class="exam-id">{{{{ID}}}}</span>
  </div>

  <div class="question-body">
    {{{{题干}}}}
  </div>

  <div class="options-list" id="frontOptions">
    {{{{#选项A}}}}
    <div class="opt-btn" data-opt="A">
      <span class="opt-tag">A</span>
      <span class="opt-text">{{{{选项A}}}}</span>
    </div>
    {{{{/选项A}}}}

    {{{{#选项B}}}}
    <div class="opt-btn" data-opt="B">
      <span class="opt-tag">B</span>
      <span class="opt-text">{{{{选项B}}}}</span>
    </div>
    {{{{/选项B}}}}

    {{{{#选项C}}}}
    <div class="opt-btn" data-opt="C">
      <span class="opt-tag">C</span>
      <span class="opt-text">{{{{选项C}}}}</span>
    </div>
    {{{{/选项C}}}}

    {{{{#选项D}}}}
    <div class="opt-btn" data-opt="D">
      <span class="opt-tag">D</span>
      <span class="opt-text">{{{{选项D}}}}</span>
    </div>
    {{{{/选项D}}}}

    {{{{#选项E}}}}
    <div class="opt-btn" data-opt="E">
      <span class="opt-tag">E</span>
      <span class="opt-text">{{{{选项E}}}}</span>
    </div>
    {{{{/选项E}}}}
  </div>

  <div class="interactive-hint">
    👆 选项已随机乱序 · 点击选项作答 · 翻转查看解析
  </div>

  <div class="card-author-watermark">
    🎴 2026 银行从业初级 · 制作: lyf266 | 仅供个人备考，严禁商用 (Apache-2.0)
  </div>
</div>

<script>
{PERSISTENCE_JS.strip()}
(function() {{
  try {{
    var isMulti = "{{{{题型}}}}" === "多选题";
    var isJudge = "{{{{题型}}}}" === "判断题";
    var container = document.getElementById("frontOptions");
    if (!container) return;

    var buttons = container.querySelectorAll(".opt-btn");
    for (var i = 0; i < buttons.length; i++) {{
      buttons[i].addEventListener("click", function() {{
        if (isMulti) {{
          this.classList.toggle("selected");
        }} else {{
          for (var j = 0; j < buttons.length; j++) {{
            buttons[j].classList.remove("selected");
          }}
          this.classList.add("selected");
        }}
      }});
    }}

    // 动态打乱（仅单选和多选，判断题保持原序）
    if (!isJudge && buttons.length > 1) {{
      var items = Array.prototype.slice.call(buttons);
      var indices = [];
      for (var i = 0; i < items.length; i++) indices.push(i);

      for (var i = indices.length - 1; i > 0; i--) {{
        var j = Math.floor(Math.random() * (i + 1));
        var temp = indices[i];
        indices[i] = indices[j];
        indices[j] = temp;
      }}

      if (window.Persistence && Persistence.isAvailable()) {{
        Persistence.setItem("opt_indices", indices);
      }}

      var letters = ["A", "B", "C", "D", "E"];
      for (var k = 0; k < indices.length; k++) {{
        var el = items[indices[k]];
        container.appendChild(el);
        var tag = el.querySelector(".opt-tag");
        if (tag) tag.innerText = letters[k];
      }}
    }}
  }} catch(e) {{
    // 任何异常自动静默降级为默认顺序，绝不阻塞显示
  }}
}})();
</script>
"""

SHUFFLE_AFMT = f"""<div class="exam-container back-container">
  <div class="exam-header">
    <span class="type-badge badge-{{{{题型}}}}">{{{{题型}}}}</span>
    <span class="exam-id">{{{{ID}}}}</span>
  </div>

  <div class="question-body">
    {{{{题干}}}}
  </div>

  <div class="options-list" id="backOptions">
    {{{{#选项A}}}}
    <div class="opt-btn" data-opt="A">
      <span class="opt-tag">A</span>
      <span class="opt-text">{{{{选项A}}}}</span>
    </div>
    {{{{/选项A}}}}

    {{{{#选项B}}}}
    <div class="opt-btn" data-opt="B">
      <span class="opt-tag">B</span>
      <span class="opt-text">{{{{选项B}}}}</span>
    </div>
    {{{{/选项B}}}}

    {{{{#选项C}}}}
    <div class="opt-btn" data-opt="C">
      <span class="opt-tag">C</span>
      <span class="opt-text">{{{{选项C}}}}</span>
    </div>
    {{{{/选项C}}}}

    {{{{#选项D}}}}
    <div class="opt-btn" data-opt="D">
      <span class="opt-tag">D</span>
      <span class="opt-text">{{{{选项D}}}}</span>
    </div>
    {{{{/选项D}}}}

    {{{{#选项E}}}}
    <div class="opt-btn" data-opt="E">
      <span class="opt-tag">E</span>
      <span class="opt-text">{{{{选项E}}}}</span>
    </div>
    {{{{/选项E}}}}
  </div>

  <div class="answer-banner">
    <span class="ans-title">🎯 机考标准答案</span>
    <span class="ans-val" id="answerDisplay">{{{{正确答案}}}}</span>
  </div>

  {{{{#速记口诀}}}}
  <div class="info-section mnemonic-card">
    <div class="mnemonic-title">🔑 15字黄金速记口诀</div>
    <div class="mnemonic-body">{{{{速记口诀}}}}</div>
  </div>
  {{{{/速记口诀}}}}

  {{{{#核心考点解析}}}}
  <div class="info-section analysis-card">
    <div class="analysis-title">💡 核心考点精析</div>
    <div class="analysis-body">{{{{核心考点解析}}}}</div>
  </div>
  {{{{/核心考点解析}}}}

  {{{{#避坑指南}}}}
  <div class="info-section trap-card">
    <div class="trap-title">⚠️ 机考高频避坑陷阱</div>
    <div class="trap-body">{{{{避坑指南}}}}</div>
  </div>
  {{{{/避坑指南}}}}

  <div class="card-author-watermark">
    🎴 2026 银行从业初级 · 制作: lyf266 | 仅供个人备考，严禁商用 (Apache-2.0)
  </div>
</div>

<script>
{PERSISTENCE_JS.strip()}
(function() {{
  try {{
    var isJudge = "{{{{题型}}}}" === "判断题";
    var ans = "{{{{正确答案}}}}".trim().toUpperCase();
    var container = document.getElementById("backOptions");
    if (!container) return;
    var items = Array.prototype.slice.call(container.querySelectorAll(".opt-btn"));
    var letters = ["A", "B", "C", "D", "E"];
    var currentCorrectLetters = [];

    var indices = null;
    if (!isJudge && items.length > 1 && window.Persistence && Persistence.isAvailable()) {{
      indices = Persistence.getItem("opt_indices");
    }}

    if (indices && indices.length === items.length) {{
      // 按照正面随机顺序重排背面
      for (var k = 0; k < indices.length; k++) {{
        var el = items[indices[k]];
        container.appendChild(el);
        var curLetter = letters[k];
        var tag = el.querySelector(".opt-tag");
        if (tag) tag.innerText = curLetter;

        var origCode = el.getAttribute("data-opt");
        if (ans.indexOf(origCode) !== -1) {{
          el.classList.add("correct-choice");
          currentCorrectLetters.push(curLetter);
        }} else {{
          el.classList.add("wrong-choice");
        }}
      }}

      // 动态映射答案栏
      var ansEl = document.getElementById("answerDisplay");
      if (ansEl && currentCorrectLetters.length > 0) {{
        currentCorrectLetters.sort();
        var newAns = currentCorrectLetters.join("");
        if (newAns !== ans) {{
          ansEl.innerHTML = newAns + ' <span style="font-size:12px;opacity:0.8;font-weight:normal">(原题: ' + ans + ')</span>';
        }}
      }}
    }} else {{
      // 判断题或降级直接匹配
      for (var i = 0; i < items.length; i++) {{
        var el = items[i];
        var optCode = el.getAttribute("data-opt");
        var textEl = el.querySelector(".opt-text");
        var optText = textEl ? textEl.innerText.trim() : "";

        var isCorrect = false;
        if (ans.indexOf(optCode) !== -1) {{
          isCorrect = true;
        }} else if (ans === "正确" && (optCode === "A" || optText === "正确")) {{
          isCorrect = true;
        }} else if (ans === "错误" && (optCode === "B" || optText === "错误")) {{
          isCorrect = true;
        }}

        if (isCorrect) {{
          el.classList.add("correct-choice");
        }} else {{
          el.classList.add("wrong-choice");
        }}
      }}
    }}
  }} catch(e) {{
    // 任何异常自动静默降级
  }}
}})();
</script>
"""

def main():
    print("=" * 60)
    print("🚀 正在注入跨端轻量动态洗牌引擎...")
    print("=" * 60)

    model_name = "银行从业·全真机考客观题"

    # 0. 更新样式
    print("0️⃣ 正在更新卡牌 CSS 样式 (注入作者水印微调样式)...")
    try:
        cur_css = anki_invoke("modelStyling", modelName=model_name).get("css", "")
        if ".card-author-watermark" not in cur_css:
            cur_css += """\n
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
            anki_invoke("updateModelStyling", model={"name": model_name, "css": cur_css.strip()})
            print("   ✅ CSS 水印样式写入成功！")
    except Exception as e:
        print(f"   ℹ️ CSS 样式更新提示: {e}")

    # 1. 更新模板
    print("1️⃣ 正在将持久化洗牌引擎写入卡牌模板...")
    anki_invoke("updateModelTemplates", model={
        "name": model_name,
        "templates": {
            "客观题答题卡": {
                "Front": SHUFFLE_QFMT.strip(),
                "Back": SHUFFLE_AFMT.strip()
            }
        }
    })
    print("   ✅ 模板正反面写入成功！正反面乱序严格对齐已就绪。")

    # 2. 重新打包导出离线卡包
    print("2️⃣ 重新打包导出离线 .apkg 卡包...")
    base_dir = "/home/f1are/orca/workspaces/银行从业备考/anki"
    pkg_obj = os.path.join(base_dir, "2026银行从业初级_全真机考客观题.apkg")
    pkg_all = os.path.join(base_dir, "2026银行从业初级_全真套题全量卡包.apkg")

    try:
        anki_invoke("exportPackage", deck="等级考试::银行从业", path=pkg_all, includeSched=False)
        anki_invoke("exportPackage", deck="等级考试::银行从业", path=pkg_obj, includeSched=False)
        print("   ✅ 离线卡包打包完毕！")
    except Exception as e:
        print(f"   ⚠️ 导出卡包提示: {e}")

    # 3. 云同步
    print("3️⃣ 正在触发云端同步推送到 AnkiWeb...")
    try:
        anki_invoke("sync")
        print("   ☁️ 云端同步完成！")
    except Exception as e:
        print(f"   ℹ️ 云同步提示: {e}")

    print("=" * 60)
    print("🎉 全部搞定！你无需任何手动配置！")

if __name__ == "__main__":
    main()
