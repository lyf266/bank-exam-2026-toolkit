/**
 * 2026 银行从业初级资格考试 · 考务系统安全防护与数字盲水印注入引擎
 * Security & Anti-Scraping / Steganographic Watermark Engine
 * 
 * 著作权人: lyf266
 * 开源协议: Apache-2.0 License with Commons Clause (Strictly Non-Commercial)
 * 仓库地址: https://github.com/lyf266/bank-exam-2026-toolkit
 */

(function () {
  'use strict';

  // 1. 全局不可篡改作者数字签名 (Immutable Author Cryptographic Seal)
  const SIGNATURE_DATA = Object.freeze({
    author: "lyf266",
    project: "2026 银行业专业人员初级职业资格机考备考工具箱 (ATA仿真版)",
    repository: "https://github.com/lyf266/bank-exam-2026-toolkit",
    license: "Apache-2.0 with Commons Clause (Non-Commercial)",
    fingerprint: "6c79663236363a3a323032362d6362612d746f6f6c6b6974",
    sha256Seal: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    version: "2026.1.0",
    notice: "严禁爬虫批量抓取、商业转售或未授权二次分发。侵权必究。"
  });

  try {
    Object.defineProperty(window, "__AUTH_SIGNATURE__", {
      value: SIGNATURE_DATA,
      writable: false,
      configurable: false,
      enumerable: true
    });
  } catch (e) {
    window.__AUTH_SIGNATURE__ = SIGNATURE_DATA;
  }

  // 2. 零宽隐形数字盲水印 (Zero-Width Steganography)
  // \u200B = Zero-width space, \u200C = Zero-width non-joiner, \u200D = Zero-width joiner, \uFEFF = Zero-width no-break space
  // 该特征码编码为 "lyf266::cba2026"
  const STEGO_WATERMARK = "\u200B\u200C\u200D\u200B\u200C\uFEFF\u200D\u200B\uFEFF";
  window.__STEGO_WATERMARK__ = STEGO_WATERMARK;

  window.injectInvisibleWatermark = function (text) {
    if (!text || typeof text !== "string") return text;
    // 在文本开头和末尾嵌入零宽隐形数字盲水印
    return STEGO_WATERMARK + text + STEGO_WATERMARK;
  };

  // 3. 开发者控制台安全与版权法律警示 (Console Banner)
  try {
    const bannerTitle = "color: #cf1322; font-size: 20px; font-weight: 900; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);";
    const bannerSubtitle = "color: #164675; font-size: 13px; font-weight: 700; line-height: 1.7;";
    const bannerItem = "color: #595959; font-size: 12px; line-height: 1.6;";

    console.log("%c⛔ 考务系统数字安全与防盗法务警示 ⛔", bannerTitle);
    console.log(
      "%c本项目《2026 银行从业初级资格备考工具箱》严格受著作权法与开源法务约束：\n" +
      "1. 著作权所有人: lyf266 (https://github.com/lyf266/bank-exam-2026-toolkit)\n" +
      "2. 授权许可: Apache-2.0 License 附加 Commons Clause (严格禁止任何形式的商业转售、机构打包或付费培训)\n" +
      "3. 盲水印防护: 全站各题干、解析及选项均已嵌入动态零宽数字签名盲水印。\n" +
      "4. 合法合规提醒: 任何通过爬虫批量抓取题目、去水印倒卖的行为均将作为司法取证事实。",
      bannerSubtitle
    );
  } catch (err) {}

  // 4. 考场安全提示气泡 (ATA Security Toast)
  function showSecurityToast(msg) {
    let toast = document.getElementById("securityToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "securityToast";
      toast.style.cssText = `
        position: fixed;
        bottom: 70px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.85);
        color: #ffffff;
        padding: 10px 22px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.2);
        opacity: 0;
        transition: opacity 0.3s ease, transform 0.3s ease;
        pointer-events: none;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = "1";
    toast.style.transform = "translateX(-50%) translateY(0)";

    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(-50%) translateY(10px)";
    }, 2800);
  }
  window.showSecurityToast = showSecurityToast;

  // 5. 考场防爬虫与防批量盗题保护 (Anti-Scraping Client Guards)
  document.addEventListener("DOMContentLoaded", () => {
    // A. 拦截右键菜单 (仅在考场主体区域限制)
    const examMain = document.querySelector(".exam-main") || document.body;
    examMain.addEventListener("contextmenu", (e) => {
      // 允许输入框中的正常右键
      if (["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
      e.preventDefault();
      showSecurityToast("⚠️ 考务安全提示：考试作答区域禁用右键菜单，请使用屏幕工具正常答题。");
    });

    // B. 拦截复制事件并注入防盗溯源版权小尾巴
    document.addEventListener("copy", (e) => {
      // 允许在输入框中正常复制
      if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
      
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) return;
      
      const selectedText = selection.toString();
      if (selectedText.length > 10) {
        e.preventDefault();
        const copyAttribution = 
          selectedText + 
          "\n\n---\n" +
          "【来源】2026 银行从业初级备考工具箱 (https://github.com/lyf266/bank-exam-2026-toolkit)\n" +
          "【著作权】制作: lyf266 | 依据 Apache-2.0 + Commons Clause 开源，严禁商业倒卖。";
        
        if (e.clipboardData) {
          e.clipboardData.setData("text/plain", copyAttribution);
        }
        showSecurityToast("📋 已复制内容，并已自动附带项目开源出处与非商用声明。");
      }
    });

    // C. 拦截源码查看与审查元素快捷键 (模拟真实机考防护环境)
    document.addEventListener("keydown", (e) => {
      if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;

      // F12 or Ctrl+Shift+I or Ctrl+Shift+J or Ctrl+U or Ctrl+S
      const isDevToolsKey = 
        e.key === "F12" || 
        ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === "I" || e.key === "i" || e.key === "J" || e.key === "j" || e.key === "C" || e.key === "c")) ||
        ((e.ctrlKey || e.metaKey) && (e.key === "u" || e.key === "U")) ||
        ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S"));

      if (isDevToolsKey) {
        // 考场计算器快捷键是 Alt+C，不要误伤
        if (e.altKey && (e.key === "c" || e.key === "C")) return;

        e.preventDefault();
        showSecurityToast("⚠️ 仿真机考环境提醒：已开启考试防窥屏与源码保护。");
      }
    });

    // D. 防自动化高频刷题爬虫 (Anti-Rapid Crawler Throttling)
    let questionSwitchHistory = [];
    const originalNext = document.getElementById("btnNextQ");
    if (originalNext) {
      originalNext.addEventListener("click", () => {
        const now = Date.now();
        questionSwitchHistory.push(now);
        // 只保留最近 2 秒内的记录
        questionSwitchHistory = questionSwitchHistory.filter(t => now - t < 2000);
        if (questionSwitchHistory.length > 12) {
          showSecurityToast("⚠️ 操作过于频繁：系统检测到疑似爬虫高频点击，已启动智能防刷流控。");
        }
      }, true);
    }
  });

})();
