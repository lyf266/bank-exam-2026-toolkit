/**
 * 银行业专业人员职业资格机考模拟系统 · 考场内置金融/科学计算器
 * 支持：
 * 1. 标准四则运算、小括号、乘方 x^y、平方根、百分比
 * 2. 真实考场专用 TVM 面板 (N, I/Y, PV, PMT, FV, CPT 计算)
 * 3. 悬浮窗口自由拖拽与极速唤出
 */

class ExamCalculator {
  constructor() {
    this.display = document.getElementById('calc-display');
    this.expression = '';
    this.tvm = {
      N: null,
      IY: null,
      PV: null,
      PMT: null,
      FV: null
    };
    this.initEvents();
    this.initDrag();
  }

  initEvents() {
    // 基础键位绑定
    document.querySelectorAll('.calc-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const val = btn.dataset.val;
        const action = btn.dataset.action;

        if (action === 'clear') {
          this.clear();
        } else if (action === 'backspace') {
          this.backspace();
        } else if (action === 'eval') {
          this.evaluate();
        } else if (action === 'sqrt') {
          this.sqrt();
        } else if (val) {
          this.append(val);
        }
      });
    });

    // TVM 键位绑定
    document.querySelectorAll('.tvm-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const param = btn.dataset.param;
        const mode = document.querySelector('input[name="tvm-mode"]:checked').value; // 'set' or 'cpt'
        
        if (mode === 'set') {
          this.setTvmParam(param);
        } else {
          this.computeTvm(param);
        }
      });
    });

    document.getElementById('btn-reset-tvm')?.addEventListener('click', () => {
      this.resetTvm();
    });
  }

  append(char) {
    if (this.expression === '0' && !isNaN(char)) {
      this.expression = char;
    } else {
      this.expression += char;
    }
    this.updateDisplay();
  }

  clear() {
    this.expression = '';
    this.updateDisplay('0');
  }

  backspace() {
    this.expression = this.expression.slice(0, -1);
    this.updateDisplay(this.expression || '0');
  }

  sqrt() {
    try {
      const val = eval(this.sanitizeExpr(this.expression));
      if (val < 0) {
        this.updateDisplay('错误: 负数开方');
        return;
      }
      const res = Math.sqrt(val);
      this.expression = res.toString();
      this.updateDisplay(res);
    } catch {
      this.updateDisplay('错误');
    }
  }

  sanitizeExpr(expr) {
    return expr.replace(/×/g, '*').replace(/÷/g, '/').replace(/\^/g, '**');
  }

  evaluate() {
    if (!this.expression) return;
    try {
      const sanitized = this.sanitizeExpr(this.expression);
      const result = eval(sanitized);
      const formatted = Number.isInteger(result) ? result : parseFloat(result.toFixed(6));
      this.expression = formatted.toString();
      this.updateDisplay(formatted);
      return formatted;
    } catch (e) {
      this.updateDisplay('语法错误');
    }
  }

  updateDisplay(val) {
    if (this.display) {
      this.display.value = val !== undefined ? val : this.expression;
    }
  }

  // === TVM 核心计算逻辑 ===
  setTvmParam(param) {
    const curVal = parseFloat(this.display.value);
    if (isNaN(curVal)) {
      alert('请先在计算器主屏幕中输入数值，再存入 ' + param);
      return;
    }
    this.tvm[param] = curVal;
    this.updateTvmLabels();
  }

  resetTvm() {
    this.tvm = { N: null, IY: null, PV: null, PMT: null, FV: null };
    this.updateTvmLabels();
  }

  updateTvmLabels() {
    for (const [k, v] of Object.entries(this.tvm)) {
      const el = document.getElementById(`tvm-val-${k}`);
      if (el) {
        el.innerText = v !== null ? v : '--';
      }
    }
  }

  computeTvm(target) {
    const { N, IY, PV, PMT, FV } = this.tvm;
    const r = (IY !== null) ? IY / 100 : null;

    try {
      let result = null;

      if (target === 'FV') {
        // FV = - (PV*(1+r)^N + PMT*((1+r)^N - 1)/r)
        if (N === null || r === null) throw new Error('缺少 N 或 I/Y');
        const pv = PV || 0;
        const pmt = PMT || 0;
        const factor = Math.pow(1 + r, N);
        const fvAnnuity = (r === 0) ? (pmt * N) : (pmt * (factor - 1) / r);
        result = - (pv * factor + fvAnnuity);
        // 如果用户按正负号未严格区分，显示其绝对值供参考
      } else if (target === 'PV') {
        if (N === null || r === null) throw new Error('缺少 N 或 I/Y');
        const fv = FV || 0;
        const pmt = PMT || 0;
        const factor = Math.pow(1 + r, -N);
        const pvAnnuity = (r === 0) ? (pmt * N) : (pmt * (1 - factor) / r);
        result = - (fv * factor + pvAnnuity);
      } else if (target === 'PMT') {
        if (N === null || r === null) throw new Error('缺少 N 或 I/Y');
        const pv = PV || 0;
        const fv = FV || 0;
        if (r === 0) {
          result = -(pv + fv) / N;
        } else {
          const factor = Math.pow(1 + r, N);
          const annuityFactor = (factor - 1) / r;
          result = - (pv * factor + fv) / annuityFactor;
        }
      } else if (target === 'N') {
        if (r === null) throw new Error('缺少 I/Y');
        const pv = PV || 0;
        const fv = FV || 0;
        if (r === 0) throw new Error('利率不可为 0');
        // 单笔现值终值 N = ln(FV / -PV) / ln(1+r)
        result = Math.log(Math.abs(fv / pv)) / Math.log(1 + r);
      }

      if (result !== null) {
        const rounded = Math.abs(parseFloat(result.toFixed(4)));
        this.display.value = rounded;
        this.expression = rounded.toString();
        // 自动将结果更新进 tvm
        this.tvm[target] = rounded;
        this.updateTvmLabels();
      }
    } catch (err) {
      alert('TVM 计算错误: ' + err.message);
    }
  }

  // === 悬浮窗口拖拽支持 ===
  initDrag() {
    const modal = document.getElementById('calc-modal');
    const header = document.getElementById('calc-header');
    if (!modal || !header) return;

    let isDragging = false;
    let startX, startY, initX, initY;

    header.addEventListener('mousedown', (e) => {
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      initX = modal.offsetLeft;
      initY = modal.offsetTop;
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      modal.style.left = `${initX + dx}px`;
      modal.style.top = `${initY + dy}px`;
      modal.style.right = 'auto';
      modal.style.bottom = 'auto';
    });

    document.addEventListener('mouseup', () => {
      isDragging = false;
      document.body.style.userSelect = 'auto';
    });
  }
}

window.ExamCalculator = ExamCalculator;
