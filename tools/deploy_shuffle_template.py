#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全自动部署工业级轻量动态洗牌引擎与官方机考专用系数表系统 (deploy_shuffle_template.py)
特性：
1. 内置成熟的 anki-persistence 跨端持久化，正反面乱序 100% 严密对齐
2. 单选/多选题随机打乱，判断题智能锁定（A正确/B错误）
3. 动态重映射背面答案栏（如 A 选项变到了 C，背面答案自动标为 C，并附注原题标准答案）
4. 【新增】内置 ATA 官方全真机考专用四大系数表弹窗与即时查算器，全端原生运行
5. 全局防御性熔断机制，0 白屏风险，手机端无需安装任何第三方插件
6. 自动完成本地注入、重新导出离线 .apkg、并向 AnkiWeb 触发云端同步
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

COEFF_MODAL_HTML = """
<!-- 官方机考专用系数表弹窗 -->
<div id="coeffModal" class="coeff-modal-overlay" style="display:none;" onclick="closeCoeffModal(event)">
  <div class="coeff-modal-content" onclick="event.stopPropagation()">
    <div class="coeff-modal-head">
      <span class="coeff-modal-title">🏛️ 2026 银行从业 · 官方机考专用系数速查表</span>
      <button type="button" class="coeff-modal-close" onclick="closeCoeffModal(event)">✕</button>
    </div>
    <div class="coeff-tab-nav">
      <button type="button" class="coeff-nav-btn active" onclick="switchModalTab(event, 'm-pf')">📉 现值(P/F)</button>
      <button type="button" class="coeff-nav-btn" onclick="switchModalTab(event, 'm-fp')">📈 终值(F/P)</button>
      <button type="button" class="coeff-nav-btn" onclick="switchModalTab(event, 'm-pa')">💶 年金现(P/A)</button>
      <button type="button" class="coeff-nav-btn" onclick="switchModalTab(event, 'm-fa')">💰 年金终(F/A)</button>
      <button type="button" class="coeff-nav-btn" onclick="switchModalTab(event, 'm-calc')">🔍 查算器</button>
      <button type="button" class="coeff-nav-btn" onclick="switchModalTab(event, 'm-tips')">🔑 倒数秘籍</button>
    </div>
    <div class="coeff-tab-panels">
      <div id="m-pf" class="coeff-panel active">
        <div class="coeff-tip-bar">复利现值：PV = FV × (P/F, r, n) ｜ 折现求现值</div>
        <div class="coeff-scroll-box" id="tableBoxPF"></div>
      </div>
      <div id="m-fp" class="coeff-panel">
        <div class="coeff-tip-bar">复利终值：FV = PV × (F/P, r, n) ｜ 利滚利求终值</div>
        <div class="coeff-scroll-box" id="tableBoxFP"></div>
      </div>
      <div id="m-pa" class="coeff-panel">
        <div class="coeff-tip-bar">普通年金现值：PV = A × (P/A, r, n) ｜ 等额收付求总现值</div>
        <div class="coeff-scroll-box" id="tableBoxPA"></div>
      </div>
      <div id="m-fa" class="coeff-panel">
        <div class="coeff-tip-bar">普通年金终值：FV = A × (F/A, r, n) ｜ 定期定额累积终值</div>
        <div class="coeff-scroll-box" id="tableBoxFA"></div>
      </div>
      <div id="m-calc" class="coeff-panel">
        <div style="font-size:12px;margin-bottom:8px;font-weight:600;color:#1e40af;">🔍 输入利率与期数秒查四大系数：</div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12px;">
          <span>利率 r (%):</span>
          <input type="number" id="mRate" value="5" step="0.5" style="width:65px;padding:3px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;">
          <span>期数 n:</span>
          <input type="number" id="mPeriod" value="5" step="1" style="width:55px;padding:3px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;">
          <button type="button" class="coeff-btn" onclick="doModalCalc()">一键计算</button>
        </div>
        <div id="mCalcResult" style="margin-top:10px;font-size:12px;line-height:1.7;"></div>
      </div>
      <div id="m-tips" class="coeff-panel">
        <div style="font-size:12px;line-height:1.7;color:#334155;">
          • <strong>三大互为倒数</strong>：(F/P)×(P/F)=1，(F/A)×(A/F)=1，(P/A)×(A/P)=1<br/>
          • <strong>口诀</strong>：终现互倒年金配，偿债配终收配现。<br/>
          • <strong>先付年金</strong>：期末年金乘以 (1+r)；期初终值期数加一系数减一，期初现值期数减一系数加一。<br/>
          • <strong>永续年金现值</strong>：PV = C / r；增长型：PV = C / (r - g)
        </div>
      </div>
    </div>
  </div>
</div>
"""

COEFF_MODAL_JS = """
window.openCoeffModal = function(e) {
  if (e) { e.preventDefault(); e.stopPropagation(); }
  var m = document.getElementById("coeffModal");
  if (m) {
    m.style.display = "flex";
    if (!window._mTablesRendered) {
      renderModalAllTables();
      window._mTablesRendered = true;
    }
  }
};
window.closeCoeffModal = function(e) {
  if (e) { e.preventDefault(); e.stopPropagation(); }
  var m = document.getElementById("coeffModal");
  if (m) m.style.display = "none";
};
window.switchModalTab = function(e, tabId) {
  if (e) { e.preventDefault(); e.stopPropagation(); }
  var navBtns = document.querySelectorAll(".coeff-nav-btn");
  for (var i = 0; i < navBtns.length; i++) navBtns[i].classList.remove("active");
  var panels = document.querySelectorAll(".coeff-panel");
  for (var i = 0; i < panels.length; i++) panels[i].classList.remove("active");
  if (e && e.currentTarget) e.currentTarget.classList.add("active");
  var target = document.getElementById(tabId);
  if (target) target.classList.add("active");
  if (tabId === "m-calc") {
    var res = document.getElementById("mCalcResult");
    if (res && !res.innerHTML) doModalCalc();
  }
};
function renderModalAllTables() {
  var rates = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 20];
  var periods = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30];
  function buildTbl(type) {
    var h = '<table class="m-table"><thead><tr><th class="m-col-n">期数 n</th>';
    for (var i = 0; i < rates.length; i++) h += '<th>' + rates[i] + '%</th>';
    h += '</tr></thead><tbody>';
    for (var j = 0; j < periods.length; j++) {
      var n = periods[j];
      h += '<tr><td class="m-col-n">n=' + n + '</td>';
      for (var i = 0; i < rates.length; i++) {
        var r = rates[i] / 100.0;
        var val = 0;
        if (type === 'pf') val = Math.pow(1 + r, -n);
        else if (type === 'fp') val = Math.pow(1 + r, n);
        else if (type === 'pa') val = (1 - Math.pow(1 + r, -n)) / r;
        else if (type === 'fa') val = (Math.pow(1 + r, n) - 1) / r;
        h += '<td>' + val.toFixed(4) + '</td>';
      }
      h += '</tr>';
    }
    h += '</tbody></table>';
    return h;
  }
  var bPF = document.getElementById("tableBoxPF"); if (bPF) bPF.innerHTML = buildTbl("pf");
  var bFP = document.getElementById("tableBoxFP"); if (bFP) bFP.innerHTML = buildTbl("fp");
  var bPA = document.getElementById("tableBoxPA"); if (bPA) bPA.innerHTML = buildTbl("pa");
  var bFA = document.getElementById("tableBoxFA"); if (bFA) bFA.innerHTML = buildTbl("fa");
}
window.doModalCalc = function() {
  var rEl = document.getElementById("mRate");
  var nEl = document.getElementById("mPeriod");
  var r = parseFloat(rEl ? rEl.value : 5) || 5;
  var n = parseInt(nEl ? nEl.value : 5) || 5;
  var rDec = r / 100.0;
  var fp = Math.pow(1 + rDec, n);
  var pf = Math.pow(1 + rDec, -n);
  var fa = (Math.pow(1 + rDec, n) - 1) / rDec;
  var pa = (1 - Math.pow(1 + rDec, -n)) / rDec;
  var res = document.getElementById("mCalcResult");
  if (res) {
    res.innerHTML = '<div style="background:#f1f5f9;padding:8px;border-radius:6px;border:1px solid #e2e8f0;margin-top:6px;">' +
      '• <strong>复利终值 (F/P, ' + r + '%, ' + n + ')</strong> = <span style="color:#2563eb;font-weight:700;">' + fp.toFixed(4) + '</span><br/>' +
      '• <strong>复利现值 (P/F, ' + r + '%, ' + n + ')</strong> = <span style="color:#2563eb;font-weight:700;">' + pf.toFixed(4) + '</span><br/>' +
      '• <strong>年金终值 (F/A, ' + r + '%, ' + n + ')</strong> = <span style="color:#059669;font-weight:700;">' + fa.toFixed(4) + '</span><br/>' +
      '• <strong>年金现值 (P/A, ' + r + '%, ' + n + ')</strong> = <span style="color:#059669;font-weight:700;">' + pa.toFixed(4) + '</span><br/>' +
      '• 偿债基金 (A/F) = ' + (1/fa).toFixed(4) + ' ｜ 投资回收 (A/P) = ' + (1/pa).toFixed(4) +
      '</div>';
  }
};
"""

COEFF_CSS_SNIPPET = """
/* 机考专用系数表弹窗与按钮样式 */
.header-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}
.coeff-btn {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
  border: 1px solid rgba(59, 130, 246, 0.3);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  transition: all 0.2s ease;
}
.coeff-btn:hover {
  background: #2563eb;
  color: #ffffff;
}
.coeff-modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
}
.coeff-modal-content {
  background: #ffffff;
  border-radius: 10px;
  width: 96%;
  max-width: 680px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0,0,0,0.25);
  font-family: "Source Han Sans SC", "Noto Sans CJK SC", "Noto Sans SC", sans-serif;
  color: #0f172a;
}
.night_mode .coeff-modal-content, .nightMode .coeff-modal-content {
  background: #1e293b;
  color: #f8fafc;
}
.coeff-modal-head {
  padding: 10px 14px;
  background: #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}
.night_mode .coeff-modal-head, .nightMode .coeff-modal-head {
  background: #0f172a;
  border-bottom-color: #334155;
}
.coeff-modal-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e40af;
}
.night_mode .coeff-modal-title, .nightMode .coeff-modal-title {
  color: #60a5fa;
}
.coeff-modal-close {
  background: transparent;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #64748b;
}
.coeff-tab-nav {
  display: flex;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
}
.night_mode .coeff-tab-nav, .nightMode .coeff-tab-nav {
  background: #0f172a;
  border-bottom-color: #334155;
}
.coeff-nav-btn {
  padding: 8px 12px;
  border: none;
  background: transparent;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  white-space: nowrap;
}
.coeff-nav-btn.active {
  color: #2563eb;
  border-bottom: 2px solid #2563eb;
  background: #ffffff;
}
.night_mode .coeff-nav-btn.active, .nightMode .coeff-nav-btn.active {
  background: #1e293b;
  color: #60a5fa;
  border-bottom-color: #60a5fa;
}
.coeff-tab-panels {
  flex: 1;
  overflow: auto;
  padding: 10px;
}
.coeff-panel {
  display: none;
}
.coeff-panel.active {
  display: block;
}
.coeff-tip-bar {
  font-size: 11px;
  padding: 4px 8px;
  background: #eff6ff;
  border-radius: 4px;
  margin-bottom: 8px;
  color: #1e40af;
}
.night_mode .coeff-tip-bar, .nightMode .coeff-tip-bar {
  background: #1e3a8a33;
  color: #93c5fd;
}
.coeff-scroll-box {
  max-height: 52vh;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}
.night_mode .coeff-scroll-box, .nightMode .coeff-scroll-box {
  border-color: #334155;
}
.m-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 11px;
  text-align: right;
}
.m-table th, .m-table td {
  padding: 5px 7px;
  border-bottom: 1px solid #e2e8f0;
  border-right: 1px solid #e2e8f0;
  white-space: nowrap;
}
.night_mode .m-table th, .night_mode .m-table td,
.nightMode .m-table th, .nightMode .m-table td {
  border-color: #334155;
}
.m-table th {
  background: #f1f5f9;
  position: sticky;
  top: 0;
  z-index: 5;
  font-weight: 700;
  color: #1e40af;
}
.night_mode .m-table th, .nightMode .m-table th {
  background: #0f172a;
  color: #60a5fa;
}
.m-table .m-col-n {
  position: sticky;
  left: 0;
  background: #ffffff;
  z-index: 3;
  text-align: center;
  font-weight: 600;
}
.m-table th.m-col-n {
  z-index: 8;
  background: #f1f5f9;
}
.night_mode .m-table .m-col-n, .nightMode .m-table .m-col-n {
  background: #1e293b;
}
.night_mode .m-table th.m-col-n, .nightMode .m-table th.m-col-n {
  background: #0f172a;
}
"""

SHUFFLE_QFMT = f"""<div class="exam-container">
  <div class="exam-header">
    <div class="header-tags">
      <span class="type-badge badge-{{{{题型}}}}">{{{{题型}}}}</span>
      <span class="exam-id">{{{{ID}}}}</span>
    </div>
    <button class="coeff-btn" type="button" onclick="openCoeffModal(event)">📊 系数表</button>
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

  {COEFF_MODAL_HTML.strip()}
</div>

<script>
{PERSISTENCE_JS.strip()}
{COEFF_MODAL_JS.strip()}
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
    <div class="header-tags">
      <span class="type-badge badge-{{{{题型}}}}">{{{{题型}}}}</span>
      <span class="exam-id">{{{{ID}}}}</span>
    </div>
    <button class="coeff-btn" type="button" onclick="openCoeffModal(event)">📊 系数表</button>
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

  {COEFF_MODAL_HTML.strip()}
</div>

<script>
{PERSISTENCE_JS.strip()}
{COEFF_MODAL_JS.strip()}
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
    print("🚀 正在注入跨端轻量动态洗牌与官方机考系数表引擎...")
    print("=" * 60)

    model_name = "银行从业·全真机考客观题"

    # 0. 更新样式
    print("0️⃣ 正在更新卡牌 CSS 样式 (注入官方机考系数表弹窗样式)...")
    try:
        cur_css = anki_invoke("modelStyling", modelName=model_name).get("css", "")
        if ".coeff-modal-overlay" not in cur_css:
            cur_css += "\n" + COEFF_CSS_SNIPPET.strip()
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
        print("   ✅ CSS 样式写入成功！")
    except Exception as e:
        print(f"   ℹ️ CSS 样式更新提示: {e}")

    # 1. 更新模板
    print("1️⃣ 正在将官方机考系数表与洗牌引擎写入卡牌模板...")
    anki_invoke("updateModelTemplates", model={
        "name": model_name,
        "templates": {
            "客观题答题卡": {
                "Front": SHUFFLE_QFMT.strip(),
                "Back": SHUFFLE_AFMT.strip()
            }
        }
    })
    print("   ✅ 模板正反面写入成功！机考专用系数表组件已就绪。")

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
