/**
 * 2026 银行从业机考 · 考场标准双模式计算器 (calculator.js)
 * 特性：
 * 1. 浮动窗口可自由拖拽、防出界、置顶不遮挡选项
 * 2. 模式一：考场标准科学计算器 (加减乘除、次幂、开方、e^x、ln、log、括号、正负号)
 * 3. 模式二：银行业专用 TVM 货币时间价值金融计算器 (N, I/Y, PV, PMT, FV, BGN/END, CPT)
 */

class ExamCalculator {
  constructor() {
    this.win = document.getElementById("calcWindow");
    this.header = document.getElementById("calcHeader");
    this.display = document.getElementById("calcDisplay");
    this.expressionDisplay = document.getElementById("calcExpression");
    
    // 状态
    this.currentExpr = "";
    this.currentVal = "0";
    this.newNumber = true;
    this.activeTab = "sci"; // 'sci' 或 'tvm'
    
    // TVM 状态
    this.tvmMode = "END"; // 'END' (期末, 默认) 或 'BGN' (期初)
    this.tvmData = { N: null, IY: null, PV: null, PMT: null, FV: null };

    this.initDrag();
    this.initEvents();
  }

  // 1. 窗口拖拽与边界碰撞检测 (仅桌面端启用)
  initDrag() {
    if (!this.header || !this.win) return;
    let isDragging = false;
    let startX = 0, startY = 0;
    let origLeft = 0, origTop = 0;

    this.header.addEventListener("mousedown", (e) => {
      if (window.innerWidth <= 768) return;
      if (e.target.closest(".calc-ctrl-btn")) return;
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

      // 限制不拖出屏幕视口
      const maxLeft = window.innerWidth - this.win.offsetWidth - 10;
      const maxTop = window.innerHeight - this.win.offsetHeight - 10;
      newLeft = Math.max(10, Math.min(newLeft, maxLeft));
      newTop = Math.max(60, Math.min(newTop, maxTop));

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
    // 切换标签
    document.querySelectorAll(".calc-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });

    // 科学计算器按键绑定
    document.querySelectorAll(".calc-key").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        const val = btn.dataset.val;
        this.handleSciKey(action, val);
      });
    });

    // TVM 模式切换 (BGN / END)
    const tvmToggle = document.getElementById("tvmToggleBtn");
    if (tvmToggle) {
      tvmToggle.addEventListener("click", () => {
        this.tvmMode = this.tvmMode === "END" ? "BGN" : "END";
        tvmToggle.textContent = this.tvmMode;
        document.getElementById("tvmModeText").textContent = 
          this.tvmMode === "END" ? "期末年金 (Ordinary/END)" : "期初年金 (Annuity Due/BGN)";
      });
    }

    // TVM CPT (求解未知变量)
    document.querySelectorAll(".tvm-cpt-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.target;
        this.solveTVM(target);
      });
    });

    // TVM 清除 (CLR TVM)
    const tvmClr = document.getElementById("tvmClrBtn");
    if (tvmClr) {
      tvmClr.addEventListener("click", () => {
        ["N", "IY", "PV", "PMT", "FV"].forEach((key) => {
          const input = document.getElementById(`tvm_${key}`);
          if (input) input.value = "";
        });
        document.getElementById("tvmStatusMsg").textContent = "TVM 寄存器已重置清空";
      });
    }

    // 快捷键 Alt+C 呼出/隐藏计算器
    if (typeof document !== "undefined" && document.addEventListener) {
      document.addEventListener("keydown", (e) => {
        if (e.altKey && e.code === "KeyC") {
          e.preventDefault();
          this.toggle();
        }
      });
    }
  }

  show() {
    if (window.innerWidth <= 768 && this.win) {
      this.win.style.left = "";
      this.win.style.top = "";
      this.win.style.right = "";
    }
    this.win.classList.add("active");
  }

  hide() {
    this.win.classList.remove("active");
  }

  toggle() {
    if (this.win.classList.contains("active")) {
      this.hide();
    } else {
      this.show();
    }
  }

  switchTab(tab) {
    this.activeTab = tab;
    document.querySelectorAll(".calc-tab-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.tab === tab);
    });

    const sciGrid = document.getElementById("calcSciGrid");
    const tvmPanel = document.getElementById("calcTvmPanel");
    const screen = document.querySelector(".calc-screen");

    if (tab === "sci") {
      sciGrid.style.display = "grid";
      tvmPanel.classList.remove("active");
      screen.style.display = "block";
    } else {
      sciGrid.style.display = "none";
      tvmPanel.classList.add("active");
      screen.style.display = "none";
    }
  }

  // 2. 科学计算按键处理
  handleSciKey(action, val) {
    if (action === "digit") {
      if (this.newNumber) {
        this.currentVal = val;
        this.newNumber = false;
      } else {
        this.currentVal = this.currentVal === "0" ? val : this.currentVal + val;
      }
      this.updateDisplay();
    } else if (action === "dot") {
      if (this.newNumber) {
        this.currentVal = "0.";
        this.newNumber = false;
      } else if (!this.currentVal.includes(".")) {
        this.currentVal += ".";
      }
      this.updateDisplay();
    } else if (action === "op") {
      this.currentExpr += ` ${this.currentVal} ${val}`;
      this.newNumber = true;
      this.updateDisplay();
    } else if (action === "equal") {
      try {
        const fullExpr = `${this.currentExpr} ${this.currentVal}`.trim();
        const res = this.safeEval(fullExpr);
        this.expressionDisplay.textContent = fullExpr + " =";
        this.currentVal = String(Number(res.toFixed(8)));
        this.currentExpr = "";
        this.newNumber = true;
        this.updateDisplay();
      } catch (err) {
        this.currentVal = "Error";
        this.newNumber = true;
        this.updateDisplay();
      }
    } else if (action === "clear") {
      this.currentVal = "0";
      this.currentExpr = "";
      this.newNumber = true;
      this.expressionDisplay.textContent = "";
      this.updateDisplay();
    } else if (action === "ce") {
      this.currentVal = "0";
      this.newNumber = true;
      this.updateDisplay();
    } else if (action === "backspace") {
      if (this.currentVal.length > 1) {
        this.currentVal = this.currentVal.slice(0, -1);
      } else {
        this.currentVal = "0";
        this.newNumber = true;
      }
      this.updateDisplay();
    } else if (action === "neg") {
      if (this.currentVal !== "0") {
        this.currentVal = this.currentVal.startsWith("-")
          ? this.currentVal.substring(1)
          : "-" + this.currentVal;
        this.updateDisplay();
      }
    } else if (action === "fn") {
      this.executeScientificFn(val);
    }
  }

  executeScientificFn(fnName) {
    let num = parseFloat(this.currentVal);
    if (isNaN(num)) return;

    let res = 0;
    switch (fnName) {
      case "sqr": // x^2
        res = Math.pow(num, 2);
        break;
      case "sqrt": // √x
        if (num < 0) { this.currentVal = "Error"; this.updateDisplay(); return; }
        res = Math.sqrt(num);
        break;
      case "pow": // x^y
        this.currentExpr += ` ${this.currentVal} **`;
        this.newNumber = true;
        this.updateDisplay();
        return;
      case "yroot": // y√x -> x ** (1/y)
        this.currentExpr += ` ${this.currentVal} yroot`;
        this.newNumber = true;
        this.updateDisplay();
        return;
      case "exp": // e^x
        res = Math.exp(num);
        break;
      case "ln": // ln(x)
        if (num <= 0) { this.currentVal = "Error"; this.updateDisplay(); return; }
        res = Math.log(num);
        break;
      case "log": // log10(x)
        if (num <= 0) { this.currentVal = "Error"; this.updateDisplay(); return; }
        res = Math.log10(num);
        break;
      case "recip": // 1/x
        if (num === 0) { this.currentVal = "Error"; this.updateDisplay(); return; }
        res = 1 / num;
        break;
      case "e":
        res = Math.E;
        break;
      case "pi":
        res = Math.PI;
        break;
      default:
        return;
    }

    this.currentVal = String(Number(res.toFixed(8)));
    this.newNumber = true;
    this.updateDisplay();
  }

  safeEval(exprStr) {
    // 替换 yroot 语法
    if (exprStr.includes("yroot")) {
      const parts = exprStr.split("yroot");
      const base = parseFloat(parts[0].trim());
      const root = parseFloat(parts[1].trim());
      return Math.pow(base, 1 / root);
    }
    // 仅保留合法的算术字符
    const sanitized = exprStr.replace(/[^0-9+\-*/().\s]/g, (match) => {
      return match === "*" ? "*" : "";
    });
    // 使用 Function 安全计算算术表达式
    return new Function(`return (${sanitized});`)();
  }

  updateDisplay() {
    this.display.textContent = this.currentVal;
    this.expressionDisplay.textContent = this.currentExpr;
  }

  // 3. TVM 货币时间价值解算引擎
  solveTVM(target) {
    const getVal = (id) => {
      const val = document.getElementById(`tvm_${id}`).value.trim();
      return val === "" ? null : parseFloat(val);
    };

    const N = getVal("N");
    const IY = getVal("IY");
    const PV = getVal("PV");
    const PMT = getVal("PMT");
    const FV = getVal("FV");

    const isBgn = this.tvmMode === "BGN";
    const b = isBgn ? 1 : 0;
    const msgEl = document.getElementById("tvmStatusMsg");

    try {
      if (target === "FV") {
        if (N === null || IY === null || PV === null || PMT === null) {
          msgEl.textContent = "⚠️ 求解 FV 需要先填入 N, I/Y, PV, PMT";
          return;
        }
        const r = IY / 100;
        let fvRes = 0;
        if (r === 0) {
          fvRes = -(PV + PMT * N);
        } else {
          const S = ((Math.pow(1 + r, N) - 1) / r) * (1 + r * b);
          fvRes = -(PV * Math.pow(1 + r, N) + PMT * S);
        }
        document.getElementById("tvm_FV").value = fvRes.toFixed(4);
        msgEl.textContent = `✅ 终值 FV = ${fvRes.toFixed(4)} (${isBgn ? "期初" : "期末"})`;
      } else if (target === "PV") {
        if (N === null || IY === null || PMT === null || FV === null) {
          msgEl.textContent = "⚠️ 求解 PV 需要先填入 N, I/Y, PMT, FV";
          return;
        }
        const r = IY / 100;
        let pvRes = 0;
        if (r === 0) {
          pvRes = -(FV + PMT * N);
        } else {
          const A = ((1 - Math.pow(1 + r, -N)) / r) * (1 + r * b);
          pvRes = -(FV / Math.pow(1 + r, N) + PMT * A);
        }
        document.getElementById("tvm_PV").value = pvRes.toFixed(4);
        msgEl.textContent = `✅ 现值 PV = ${pvRes.toFixed(4)} (${isBgn ? "期初" : "期末"})`;
      } else if (target === "PMT") {
        if (N === null || IY === null || PV === null || FV === null) {
          msgEl.textContent = "⚠️ 求解 PMT 需要先填入 N, I/Y, PV, FV";
          return;
        }
        const r = IY / 100;
        let pmtRes = 0;
        if (r === 0) {
          pmtRes = -(PV + FV) / N;
        } else {
          const S = ((Math.pow(1 + r, N) - 1) / r) * (1 + r * b);
          pmtRes = -(PV * Math.pow(1 + r, N) + FV) / S;
        }
        document.getElementById("tvm_PMT").value = pmtRes.toFixed(4);
        msgEl.textContent = `✅ 每期年金 PMT = ${pmtRes.toFixed(4)}`;
      } else if (target === "N") {
        if (IY === null || PV === null || PMT === null || FV === null) {
          msgEl.textContent = "⚠️ 求解 N 需要先填入 I/Y, PV, PMT, FV";
          return;
        }
        const r = IY / 100;
        if (r === 0) {
          const nRes = -(PV + FV) / PMT;
          document.getElementById("tvm_N").value = nRes.toFixed(2);
          msgEl.textContent = `✅ 期数 N = ${nRes.toFixed(2)}`;
          return;
        }
        if (PMT === 0) {
          const ratio = -FV / PV;
          if (ratio <= 0) throw new Error("现金流方向需一正一负");
          const nRes = Math.log(ratio) / Math.log(1 + r);
          document.getElementById("tvm_N").value = nRes.toFixed(2);
          msgEl.textContent = `✅ 期数 N = ${nRes.toFixed(2)}`;
        } else {
          const k = PMT * ((1 + r * b) / r);
          const numerator = k - FV;
          const denominator = PV + k;
          if (numerator / denominator <= 0) throw new Error("年金与现值终值不匹配");
          const nRes = Math.log(numerator / denominator) / Math.log(1 + r);
          document.getElementById("tvm_N").value = nRes.toFixed(2);
          msgEl.textContent = `✅ 期数 N = ${nRes.toFixed(2)}`;
        }
      } else if (target === "IY") {
        if (N === null || PV === null || PMT === null || FV === null) {
          msgEl.textContent = "⚠️ 求解 I/Y 需要先填入 N, PV, PMT, FV";
          return;
        }
        // 牛顿迭代法求解利率 r
        let r = 0.05; // 初始猜测 5%
        for (let i = 0; i < 50; i++) {
          const S = r === 0 ? N : ((Math.pow(1 + r, N) - 1) / r) * (1 + r * b);
          const f = PV * Math.pow(1 + r, N) + PMT * S + FV;
          // 导数微元近似
          const dr = 0.0001;
          const S_dr = ((Math.pow(1 + (r + dr), N) - 1) / (r + dr)) * (1 + (r + dr) * b);
          const f_dr = PV * Math.pow(1 + (r + dr), N) + PMT * S_dr + FV;
          const df = (f_dr - f) / dr;
          if (Math.abs(df) < 1e-12) break;
          const rNext = r - f / df;
          if (Math.abs(rNext - r) < 1e-7) {
            r = rNext;
            break;
          }
          r = rNext;
        }
        const iyRes = r * 100;
        document.getElementById("tvm_IY").value = iyRes.toFixed(4);
        msgEl.textContent = `✅ 每期利率 I/Y = ${iyRes.toFixed(4)}%`;
      }
    } catch (err) {
      msgEl.textContent = `❌ 计算失败: ${err.message || "输入数值无法收敛"}`;
    }
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = ExamCalculator;
}
