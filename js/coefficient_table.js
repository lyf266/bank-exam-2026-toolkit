/**
 * 2026 银行从业机考 · 官方机考专用系数表组件 (coefficient_table.js)
 * 100% 仿真 ATA 全真考场附表：
 * 1. 附表一：复利现值系数表 (P/F, r, n)
 * 2. 附表二：复利终值系数表 (F/P, r, n)
 * 3. 附表三：普通年金现值系数表 (P/A, r, n)
 * 4. 附表四：普通年金终值系数表 (F/A, r, n)
 * 5. 核心换算与三大互为倒数秘籍 (偿债基金、投资回收、先付年金加一减一口诀)
 * 6. 支持自由拖拽 (桌面端)、最大化全屏、移动端底部半屏抽屉 (Bottom Sheet)
 * 7. 顶部极速查算条：输入利率与期数，秒级定位高亮匹配单元格并折算本金
 */

class ExamCoefficientTable {
  constructor() {
    this.win = document.getElementById("coeffWindow");
    this.header = document.getElementById("coeffHeader");
    this.maxBtn = document.getElementById("coeffMaxBtn");
    this.closeBtn = document.getElementById("coeffCloseBtn");

    this.rateInput = document.getElementById("coeffQuickRate");
    this.periodInput = document.getElementById("coeffQuickPeriod");
    this.amountInput = document.getElementById("coeffQuickAmount");

    this.activeTab = "pf"; // 'pf', 'fp', 'pa', 'fa', 'tips'
    this.isMaximized = false;
    this.renderedTabs = new Set();

    // 官方机考标准利率与期数梯度
    this.RATES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 20];
    this.PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 25, 30];

    this.initDrag();
    this.initEvents();
  }

  // 四大系数数学精确求解
  static calc(type, rPct, n) {
    const r = rPct / 100.0;
    if (type === "pf") return Math.pow(1 + r, -n);
    if (type === "fp") return Math.pow(1 + r, n);
    if (type === "fa") {
      if (Math.abs(r) < 1e-9) return n;
      return (Math.pow(1 + r, n) - 1) / r;
    }
    if (type === "pa") {
      if (Math.abs(r) < 1e-9) return n;
      return (1 - Math.pow(1 + r, -n)) / r;
    }
    return 0;
  }

  // 桌面端浮动窗口可拖拽与防出界
  initDrag() {
    if (!this.header || !this.win) return;
    let isDragging = false;
    let startX = 0, startY = 0;
    let origLeft = 0, origTop = 0;

    this.header.addEventListener("mousedown", (e) => {
      if (window.innerWidth <= 768 || this.isMaximized) return;
      if (e.target.closest(".coeff-ctrl-btn")) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = this.win.getBoundingClientRect();
      origLeft = rect.left;
      origTop = rect.top;
      this.header.style.cursor = "grabbing";
      e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      let newLeft = origLeft + (e.clientX - startX);
      let newTop = origTop + (e.clientY - startY);

      const maxLeft = window.innerWidth - this.win.offsetWidth - 10;
      const maxTop = window.innerHeight - this.win.offsetHeight - 10;
      newLeft = Math.max(10, Math.min(newLeft, maxLeft));
      newTop = Math.max(50, Math.min(newTop, maxTop));

      this.win.style.left = `${newLeft}px`;
      this.win.style.top = `${newTop}px`;
      this.win.style.right = "auto";
    });

    document.addEventListener("mouseup", () => {
      if (isDragging) {
        isDragging = false;
        this.header.style.cursor = "move";
      }
    });
  }

  initEvents() {
    // 快捷键监听
    document.addEventListener("keydown", (e) => {
      // Alt + T: 呼出/隐藏系数表
      if (e.altKey && e.code === "KeyT") {
        e.preventDefault();
        this.toggle();
        return;
      }
      // Esc: 若系数表打开则关闭
      if (e.key === "Escape" && this.win && this.win.classList.contains("active")) {
        e.preventDefault();
        this.hide();
        return;
      }
    });

    // 最大化 / 还原
    if (this.maxBtn) {
      this.maxBtn.addEventListener("click", () => this.toggleMaximize());
    }

    // 关闭按钮
    if (this.closeBtn) {
      this.closeBtn.addEventListener("click", () => this.hide());
    }

    // 选项卡切换
    if (this.win) {
      this.win.querySelectorAll(".coeff-tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const tab = btn.dataset.tab;
          this.switchTab(tab);
        });
      });
    }

    // 顶部快速定位输入框联动
    const onQuickInput = () => this.updateQuickLookup();
    if (this.rateInput) this.rateInput.addEventListener("input", onQuickInput);
    if (this.periodInput) this.periodInput.addEventListener("input", onQuickInput);
    if (this.amountInput) this.amountInput.addEventListener("input", onQuickInput);
  }

  // 选项卡切换与惰性渲染
  switchTab(tabKey) {
    this.activeTab = tabKey;
    if (!this.win) return;

    this.win.querySelectorAll(".coeff-tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabKey);
    });

    this.win.querySelectorAll(".coeff-tab-pane").forEach((pane) => {
      pane.classList.toggle("active", pane.id === `pane-${tabKey}`);
    });

    if (["pf", "fp", "pa", "fa"].includes(tabKey)) {
      this.renderTable(tabKey);
    }

    // 若有 KaTeX 支持，自动渲染公式
    if (typeof renderMathInElement === "function") {
      const activePane = document.getElementById(`pane-${tabKey}`);
      if (activePane) {
        try {
          renderMathInElement(activePane, {
            delimiters: [
              { left: "$$", right: "$$", display: true },
              { left: "\\[", right: "\\]", display: true },
              { left: "$", right: "$", display: false },
              { left: "\\(", right: "\\)", display: false }
            ],
            throwOnError: false
          });
        } catch (e) {}
      }
    }
  }

  // 渲染表格 (惰性生成，带冻结首行首列)
  renderTable(type) {
    if (this.renderedTabs.has(type)) return;
    const wrapId = `tableWrap${type.toUpperCase()}`;
    const wrap = document.getElementById(wrapId);
    if (!wrap) return;

    let html = `<table class="coeff-data-table">
      <thead>
        <tr>
          <th class="col-period-sticky">期数 (n)</th>`;
    for (const r of this.RATES) {
      html += `<th>${r}%</th>`;
    }
    html += `</tr></thead><tbody>`;

    for (const n of this.PERIODS) {
      html += `<tr data-n="${n}"><td class="col-period-sticky">n = ${n}</td>`;
      for (const r of this.RATES) {
        const val = ExamCoefficientTable.calc(type, r, n).toFixed(4);
        html += `<td data-r="${r}" data-n="${n}">${val}</td>`;
      }
      html += `</tr>`;
    }
    html += `</tbody></table>`;
    wrap.innerHTML = html;
    this.renderedTabs.add(type);

    // 重新应用高亮
    this.updateHighlight();
  }

  // 顶部快速检索更新
  updateQuickLookup() {
    const r = parseFloat(this.rateInput ? this.rateInput.value : 5) || 5;
    const n = parseInt(this.periodInput ? this.periodInput.value : 5) || 5;
    const amt = parseFloat(this.amountInput ? this.amountInput.value : 0) || 0;

    const pf = ExamCoefficientTable.calc("pf", r, n);
    const fp = ExamCoefficientTable.calc("fp", r, n);
    const pa = ExamCoefficientTable.calc("pa", r, n);
    const fa = ExamCoefficientTable.calc("fa", r, n);

    const bPF = document.getElementById("coeffBadgePF");
    const bFP = document.getElementById("coeffBadgeFP");
    const bPA = document.getElementById("coeffBadgePA");
    const bFA = document.getElementById("coeffBadgeFA");

    if (bPF) bPF.innerHTML = pf.toFixed(4) + (amt > 0 ? ` <small>(≈${(amt * pf).toFixed(0)}元)</small>` : "");
    if (bFP) bFP.innerHTML = fp.toFixed(4) + (amt > 0 ? ` <small>(≈${(amt * fp).toFixed(0)}元)</small>` : "");
    if (bPA) bPA.innerHTML = pa.toFixed(4) + (amt > 0 ? ` <small>(≈${(amt * pa).toFixed(0)}元)</small>` : "");
    if (bFA) bFA.innerHTML = fa.toFixed(4) + (amt > 0 ? ` <small>(≈${(amt * fa).toFixed(0)}元)</small>` : "");

    this.updateHighlight(r, n);
  }

  // 单元格黄色聚焦高亮
  updateHighlight(r, n) {
    if (!this.win) return;
    if (r === undefined) r = parseFloat(this.rateInput ? this.rateInput.value : 5) || 5;
    if (n === undefined) n = parseInt(this.periodInput ? this.periodInput.value : 5) || 5;

    // 清除既有高亮
    this.win.querySelectorAll(".highlight-cell").forEach((el) => el.classList.remove("highlight-cell"));
    this.win.querySelectorAll(".highlight-row").forEach((el) => el.classList.remove("highlight-row"));

    // 添加新高亮
    this.win.querySelectorAll(`tr[data-n="${n}"]`).forEach((tr) => tr.classList.add("highlight-row"));
    this.win.querySelectorAll(`td[data-r="${r}"][data-n="${n}"]`).forEach((td) => td.classList.add("highlight-cell"));
  }

  toggleMaximize() {
    this.isMaximized = !this.isMaximized;
    if (this.isMaximized) {
      this.win.classList.add("maximized");
      if (this.maxBtn) {
        this.maxBtn.textContent = "❐";
        this.maxBtn.title = "还原窗口";
      }
    } else {
      this.win.classList.remove("maximized");
      if (this.maxBtn) {
        this.maxBtn.textContent = "⛶";
        this.maxBtn.title = "最大化全屏";
      }
    }
  }

  show() {
    if (!this.win) return;
    this.win.classList.add("active");
    this.renderTable(this.activeTab);
    this.updateQuickLookup();
  }

  hide() {
    if (!this.win) return;
    this.win.classList.remove("active");
  }

  toggle() {
    if (!this.win) return;
    if (this.win.classList.contains("active")) {
      this.hide();
    } else {
      this.show();
    }
  }
}
