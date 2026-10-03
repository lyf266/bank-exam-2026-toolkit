/**
 * 2026 银行从业初级资格机考模拟系统 · 核心业务引擎
 */

class MockExamApp {
  constructor() {
    this.exams = [];
    this.currentExam = null;
    this.currentIndex = 0;
    this.userAnswers = {}; // { [id]: "A" | "AC" }
    this.markedQuestions = new Set();
    this.timeRemaining = 120 * 60; // 120分钟
    this.timerInterval = null;
    this.fontSizeLevel = 2; // 1: 14px, 2: 16px, 3: 18px

    this.initDOM();
    this.loadSampleExams();
  }

  initDOM() {
    // 基础导航
    document.getElementById('btn-prev')?.addEventListener('click', () => this.prevQuestion());
    document.getElementById('btn-next')?.addEventListener('click', () => this.nextQuestion());
    document.getElementById('btn-mark-toggle')?.addEventListener('click', () => this.toggleMark());
    document.getElementById('btn-submit-exam')?.addEventListener('click', () => this.confirmSubmit());

    // 字体缩放
    document.getElementById('btn-font-plus')?.addEventListener('click', () => this.changeFontSize(1));
    document.getElementById('btn-font-minus')?.addEventListener('click', () => this.changeFontSize(-1));

    // 计算器弹窗开关
    document.getElementById('btn-toggle-calc')?.addEventListener('click', () => {
      const modal = document.getElementById('calc-modal');
      if (modal) {
        modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
      }
    });
    document.getElementById('btn-close-calc')?.addEventListener('click', () => {
      document.getElementById('calc-modal').style.display = 'none';
    });

    // 导入题目模态框
    document.getElementById('btn-import-modal')?.addEventListener('click', () => {
      document.getElementById('import-modal').style.display = 'flex';
    });
    document.getElementById('btn-close-import')?.addEventListener('click', () => {
      document.getElementById('import-modal').style.display = 'none';
    });

    // 题库切换选择器
    document.getElementById('select-exam')?.addEventListener('change', (e) => {
      this.switchExam(e.target.value);
    });

    // 导入确认
    document.getElementById('btn-do-import')?.addEventListener('click', () => this.handleCustomImport());

    // 重新测试与关闭成绩弹窗
    document.getElementById('btn-close-result')?.addEventListener('click', () => {
      document.getElementById('result-modal').style.display = 'none';
    });
    document.getElementById('btn-restart-exam')?.addEventListener('click', () => {
      document.getElementById('result-modal').style.display = 'none';
      this.resetExamState();
    });
    document.getElementById('btn-export-wrongs')?.addEventListener('click', () => this.exportWrongQuestions());

    // 初始化计算器组件
    if (window.ExamCalculator) {
      this.calculator = new window.ExamCalculator();
    }
  }

  async loadSampleExams() {
    try {
      // 优先从 localStorage 加载用户自定义的题库
      const localCustom = localStorage.getItem('bank_mock_custom_exams');
      let customExams = [];
      if (localCustom) {
        try { customExams = JSON.parse(localCustom); } catch {}
      }

      // 获取内置题库
      const res = await fetch('questions_sample.json');
      const data = await res.json();
      this.exams = [...(data.exams || []), ...customExams];

      this.renderExamSelector();
      if (this.exams.length > 0) {
        this.switchExam(this.exams[0].id);
      }
    } catch (e) {
      console.error('加载样卷失败，启动基础模式', e);
    }
  }

  renderExamSelector() {
    const sel = document.getElementById('select-exam');
    if (!sel) return;
    sel.innerHTML = '';
    this.exams.forEach(ex => {
      const opt = document.createElement('option');
      opt.value = ex.id;
      opt.innerText = ex.name;
      sel.appendChild(opt);
    });
  }

  switchExam(examId) {
    const ex = this.exams.find(item => item.id === examId);
    if (!ex) return;
    this.currentExam = ex;
    document.getElementById('exam-subject-name').innerText = ex.name;
    this.resetExamState();
  }

  resetExamState() {
    this.currentIndex = 0;
    this.userAnswers = {};
    this.markedQuestions.clear();
    this.timeRemaining = (this.currentExam.duration_minutes || 120) * 60;
    this.startTimer();
    this.renderQuestion();
    this.renderAnswerSheet();
  }

  startTimer() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    const timerEl = document.getElementById('timer-countdown');

    const updateDisplay = () => {
      const m = Math.floor(this.timeRemaining / 60);
      const s = this.timeRemaining % 60;
      const fmt = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
      if (timerEl) {
        timerEl.innerText = fmt;
        const box = timerEl.closest('.timer-box');
        if (this.timeRemaining <= 300) {
          box?.classList.add('warning');
        } else {
          box?.classList.remove('warning');
        }
      }

      if (this.timeRemaining <= 0) {
        clearInterval(this.timerInterval);
        alert('考试时间到！系统已自动为您交卷并判分。');
        this.submitExam();
      }
      this.timeRemaining--;
    };

    updateDisplay();
    this.timerInterval = setInterval(updateDisplay, 1000);
  }

  renderQuestion() {
    const q = this.currentExam.questions[this.currentIndex];
    if (!q) return;

    // 题型标签与元信息
    const typeTag = document.getElementById('q-type-tag');
    typeTag.className = 'type-tag';
    if (q.type === '多选题') typeTag.classList.add('multi');
    else if (q.type === '判断题') typeTag.classList.add('judge');
    typeTag.innerText = q.type;

    document.getElementById('q-current-num').innerText = this.currentIndex + 1;
    document.getElementById('q-total-num').innerText = this.currentExam.questions.length;
    document.getElementById('q-score').innerText = q.score.toFixed(1);

    // 标记按钮状态
    const markBtn = document.getElementById('btn-mark-toggle');
    const isMarked = this.markedQuestions.has(q.id);
    if (isMarked) {
      markBtn.classList.add('marked');
      markBtn.innerHTML = '🚩 已标记待复查';
    } else {
      markBtn.classList.remove('marked');
      markBtn.innerHTML = '🏳️ 标记本题';
    }

    // 题干内容
    document.getElementById('q-content-text').innerText = q.question;

    // 选项列表
    const optContainer = document.getElementById('options-container');
    optContainer.innerHTML = '';

    const currentAnswer = this.userAnswers[q.id] || '';

    Object.entries(q.options).forEach(([key, val]) => {
      const optEl = document.createElement('div');
      optEl.className = 'option-item';
      const isSelected = (q.type === '多选题') ? currentAnswer.includes(key) : currentAnswer === key;
      if (isSelected) optEl.classList.add('selected');

      optEl.innerHTML = `
        <div class="option-prefix">${key}.</div>
        <div class="option-content">${val}</div>
      `;

      optEl.addEventListener('click', () => this.handleOptionSelect(q, key));
      optContainer.appendChild(optEl);
    });

    // 翻页按钮可用性
    document.getElementById('btn-prev').disabled = (this.currentIndex === 0);
    document.getElementById('btn-next').disabled = (this.currentIndex === this.currentExam.questions.length - 1);

    // 刷新答题卡高亮聚焦
    this.updateAnswerSheetFocus();
  }

  handleOptionSelect(q, selectedKey) {
    if (q.type === '多选题') {
      let cur = this.userAnswers[q.id] || '';
      if (cur.includes(selectedKey)) {
        cur = cur.replace(selectedKey, '');
      } else {
        cur = (cur + selectedKey).split('').sort().join('');
      }
      if (cur.length > 0) {
        this.userAnswers[q.id] = cur;
      } else {
        delete this.userAnswers[q.id];
      }
    } else {
      // 单选题与判断题直接替换
      this.userAnswers[q.id] = selectedKey;
    }

    this.renderQuestion();
    this.updateAnswerSheetButton(this.currentIndex);
  }

  prevQuestion() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.renderQuestion();
    }
  }

  nextQuestion() {
    if (this.currentIndex < this.currentExam.questions.length - 1) {
      this.currentIndex++;
      this.renderQuestion();
    }
  }

  toggleMark() {
    const q = this.currentExam.questions[this.currentIndex];
    if (this.markedQuestions.has(q.id)) {
      this.markedQuestions.delete(q.id);
    } else {
      this.markedQuestions.add(q.id);
    }
    this.renderQuestion();
    this.updateAnswerSheetButton(this.currentIndex);
  }

  renderAnswerSheet() {
    const container = document.getElementById('sheet-groups-container');
    if (!container) return;
    container.innerHTML = '';

    // 按题型自动分组
    const groups = {};
    this.currentExam.questions.forEach((q, idx) => {
      if (!groups[q.type]) groups[q.type] = [];
      groups[q.type].push({ q, idx });
    });

    Object.entries(groups).forEach(([type, items]) => {
      const gBox = document.createElement('div');
      gBox.className = 'sheet-group';

      const gTitle = document.createElement('div');
      gTitle.className = 'sheet-group-title';
      gTitle.innerText = `${type}（第 ${items[0].idx + 1} ~ ${items[items.length - 1].idx + 1} 题）`;
      gBox.appendChild(gTitle);

      const matrix = document.createElement('div');
      matrix.className = 'grid-matrix';

      items.forEach(({ q, idx }) => {
        const btn = document.createElement('button');
        btn.className = 'grid-btn';
        btn.id = `sheet-btn-${idx}`;
        btn.innerText = idx + 1;
        btn.addEventListener('click', () => {
          this.currentIndex = idx;
          this.renderQuestion();
        });
        matrix.appendChild(btn);
      });

      gBox.appendChild(matrix);
      container.appendChild(gBox);
    });

    for (let i = 0; i < this.currentExam.questions.length; i++) {
      this.updateAnswerSheetButton(i);
    }
    this.updateAnswerSheetFocus();
  }

  updateAnswerSheetButton(idx) {
    const btn = document.getElementById(`sheet-btn-${idx}`);
    if (!btn) return;

    const q = this.currentExam.questions[idx];
    const isAnswered = !!this.userAnswers[q.id];
    const isMarked = this.markedQuestions.has(q.id);

    btn.className = 'grid-btn';
    if (idx === this.currentIndex) btn.classList.add('current');
    if (isAnswered) btn.classList.add('answered');
    if (isMarked) btn.classList.add('marked');
  }

  updateAnswerSheetFocus() {
    document.querySelectorAll('.grid-btn.current').forEach(b => b.classList.remove('current'));
    const curBtn = document.getElementById(`sheet-btn-${this.currentIndex}`);
    if (curBtn) curBtn.classList.add('current');
  }

  changeFontSize(delta) {
    this.fontSizeLevel = Math.max(1, Math.min(3, this.fontSizeLevel + delta));
    const sizes = { 1: '14px', 2: '16px', 3: '18px' };
    document.getElementById('q-content-text').style.fontSize = sizes[this.fontSizeLevel];
  }

  confirmSubmit() {
    const total = this.currentExam.questions.length;
    const answeredCount = Object.keys(this.userAnswers).length;
    const unAnsweredCount = total - answeredCount;

    let msg = `本卷共 ${total} 道题，您已作答 ${answeredCount} 道`;
    if (unAnsweredCount > 0) {
      msg += `，尚有 ${unAnsweredCount} 道题未作答！`;
    } else {
      msg += `，已全部作答完毕！`;
    }
    msg += '\n\n确定现在交卷并进行官方标准成绩判分吗？';

    if (confirm(msg)) {
      this.submitExam();
    }
  }

  submitExam() {
    if (this.timerInterval) clearInterval(this.timerInterval);

    let totalScore = 0;
    let maxScore = 0;
    const wrongList = [];

    this.currentExam.questions.forEach((q, idx) => {
      maxScore += q.score;
      const userAns = this.userAnswers[q.id] || '未作答';
      const correctAns = q.answer;

      let isCorrect = false;
      if (q.type === '多选题') {
        // 多选、少选、错选均不得分 (严格字符串比对)
        isCorrect = (userAns === correctAns);
      } else {
        isCorrect = (userAns === correctAns);
      }

      if (isCorrect) {
        totalScore += q.score;
      } else {
        wrongList.push({
          num: idx + 1,
          q,
          userAns,
          correctAns
        });
      }
    });

    this.showResultModal(totalScore, maxScore, wrongList);
  }

  showResultModal(score, maxScore, wrongList) {
    const modal = document.getElementById('result-modal');
    const scoreVal = document.getElementById('res-score-val');
    const statusText = document.getElementById('res-status-text');
    const rateText = document.getElementById('res-rate-text');
    const wrongContainer = document.getElementById('res-wrongs-list');

    const roundedScore = parseFloat(score.toFixed(1));
    scoreVal.innerText = roundedScore;
    rateText.innerText = `满分 ${maxScore.toFixed(1)} 分 (做对 ${this.currentExam.questions.length - wrongList.length} / ${this.currentExam.questions.length} 题)`;

    if (roundedScore >= 60.0 || (roundedScore / maxScore >= 0.6)) {
      statusText.innerText = '🎉 恭喜通过！成绩合格，达成稳过基本盘！';
      statusText.style.color = '#15803D';
    } else {
      statusText.innerText = '⚠️ 未达 60 分及格线！请重点复盘以下错题与口诀。';
      statusText.style.color = '#DC2626';
    }

    // 渲染错题复盘列表
    wrongContainer.innerHTML = '';
    if (wrongList.length === 0) {
      wrongContainer.innerHTML = '<div style="color:#15803D; font-weight:700;">🌟 满分！全部答对，无任何错题！</div>';
    } else {
      wrongList.forEach(item => {
        const row = document.createElement('div');
        row.style.cssText = 'background:#FEF2F2; border:1px solid #FCA5A5; border-radius:6px; padding:12px; margin-bottom:12px; font-size:13px;';
        row.innerHTML = `
          <div style="font-weight:700; color:#991B1B; margin-bottom:4px;">
            第 ${item.num} 题 [${item.q.type}]（你的作答：${item.userAns} ❌ ｜ 正确答案：${item.correctAns} ✅）
          </div>
          <div style="margin-bottom:6px; color:#1E293B;">${item.q.question}</div>
          <div style="color:#475569; font-size:12px; margin-bottom:4px;">💡 <b>考点解析</b>：${item.q.explanation}</div>
          <div style="color:#B45309; font-size:12px; font-weight:700;">🔑 <b>记忆口诀</b>：${item.q.mnemonic || '无'}</div>
        `;
        wrongContainer.appendChild(row);
      });
    }

    this.latestWrongList = wrongList;
    modal.style.display = 'flex';
  }

  exportWrongQuestions() {
    if (!this.latestWrongList || this.latestWrongList.length === 0) {
      alert('本次测验无错题！');
      return;
    }
    let md = `# 📝 错题提纯导出 (${new Date().toLocaleDateString()})\n\n`;
    this.latestWrongList.forEach(item => {
      md += `### 第 ${item.num} 题 [${item.q.type}]\n`;
      md += `* **题干**：${item.q.question}\n`;
      md += `* **你的作答**：${item.userAns}（错误）\n`;
      md += `* **正确答案**：${item.correctAns}\n`;
      md += `* **考点解析**：${item.q.explanation}\n`;
      md += `* **秒杀口诀**：${item.q.mnemonic}\n\n---\n\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `错题复盘本_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // === 题库导入引擎（支持直接粘贴解析）===
  handleCustomImport() {
    const rawText = document.getElementById('import-textarea').value.trim();
    const fileInput = document.getElementById('import-file-input');

    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const parsed = JSON.parse(e.target.result);
          this.saveImportedExam(parsed);
        } catch {
          alert('JSON 文件格式解析失败，请检查语法！');
        }
      };
      reader.readAsText(file);
      return;
    }

    if (!rawText) {
      alert('请粘贴题目纯文本，或者上传 JSON 题库文件！');
      return;
    }

    // 纯文本解析引擎
    try {
      const exam = this.parseTextToExam(rawText);
      if (exam.questions.length === 0) {
        alert('未能识别到有效题目，请参考示例格式粘贴！');
        return;
      }
      this.saveImportedExam(exam);
    } catch (e) {
      alert('文本解析出错: ' + e.message);
    }
  }

  parseTextToExam(text) {
    const lines = text.split('\n');
    const questions = [];
    let curQ = null;

    for (let rawLine of lines) {
      const line = rawLine.trim();
      if (!line) continue;

      // 匹配题干行: 1. [单选题] 题干...
      const qMatch = line.match(/^(\d+[\.\、\s]*)?(\[?(单选|多选|判断)题?\]?)?\s*(.+)$/);
      if (line.includes('A.') || line.includes('A、') || line.startsWith('答案') || line.startsWith('解析') || line.startsWith('口诀')) {
        // 属于选项或元信息
      } else if (qMatch && (line.includes('？') || line.includes('?') || line.includes('（') || line.includes('(') || qMatch[3])) {
        if (curQ && curQ.question && curQ.answer) {
          questions.push(curQ);
        }
        const typeStr = qMatch[3] ? (qMatch[3] + '题') : '单选题';
        curQ = {
          id: `CUSTOM-${questions.length + 1}`,
          type: typeStr.replace('题题', '题'),
          score: typeStr.includes('单选') ? 0.5 : 1.0,
          question: qMatch[4],
          options: {},
          answer: '',
          explanation: '',
          mnemonic: ''
        };
        continue;
      }

      if (!curQ) continue;

      // 匹配选项 A. 或 A、
      const optMatch = line.match(/^([A-E])[\.\、\:\s]\s*(.+)$/);
      if (optMatch) {
        curQ.options[optMatch[1]] = optMatch[2];
        continue;
      }

      // 匹配答案
      if (line.startsWith('答案') || line.startsWith('参考答案')) {
        const ansMatch = line.match(/([A-E]+)/);
        if (ansMatch) curQ.answer = ansMatch[1];
        continue;
      }

      // 匹配解析
      if (line.startsWith('解析') || line.startsWith('考点解析')) {
        curQ.explanation = line.replace(/^(解析|考点解析)[\:\：\s]*/, '');
        continue;
      }

      // 匹配口诀
      if (line.startsWith('口诀') || line.startsWith('记忆口诀')) {
        curQ.mnemonic = line.replace(/^(口诀|记忆口诀)[\:\：\s]*/, '');
        continue;
      }
    }

    if (curQ && curQ.question && curQ.answer) {
      questions.push(curQ);
    }

    return {
      id: `custom_${Date.now()}`,
      name: `自定义导入题库 (${new Date().toLocaleDateString()})`,
      duration_minutes: 120,
      questions
    };
  }

  saveImportedExam(exam) {
    this.exams.push(exam);
    // 写入 localStorage
    const localCustom = localStorage.getItem('bank_mock_custom_exams');
    let customExams = [];
    if (localCustom) {
      try { customExams = JSON.parse(localCustom); } catch {}
    }
    customExams.push(exam);
    localStorage.setItem('bank_mock_custom_exams', JSON.stringify(customExams));

    alert(`成功导入题库《${exam.name}》，共 ${exam.questions.length} 道题目！已自动切换。`);
    document.getElementById('import-modal').style.display = 'none';
    this.renderExamSelector();
    this.switchExam(exam.id);
  }
}

// 页面加载完毕初始化
window.addEventListener('DOMContentLoaded', () => {
  window.mockApp = new MockExamApp();
});
