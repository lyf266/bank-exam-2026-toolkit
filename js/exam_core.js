/**
 * 2026 银行从业机考 · 考务与作答核心引擎 (exam_core.js)
 * 职责：
 * 1. 考前准考证信息核对与倒计时启动
 * 2. 120 分钟标准考场倒计时与交卷提醒
 * 3. 题号方阵状态管理（未做、已做、标记角标、当前题）
 * 4. 单选/多选/判断作答判定与键盘快捷键
 * 5. 全真模考与背题模式无损切换
 * 6. 官方准考证风格成绩报告与错题精析
 */

class ExamCore {
  constructor() {
    this.currentPaper = null;
    this.currentIndex = 0; // 0-indexed
    this.userAnswers = {}; // { qId: "A" 或 "ABCD" }
    this.flaggedQuestions = new Set();
    this.mode = "MOCK"; // 'MOCK' (全真模考) 或 'PRACTICE' (背题练习)
    this.status = "PRE_EXAM"; // 'PRE_EXAM', 'IN_EXAM', 'SUBMITTED'
    
    // 计时器 (标准 120 分钟)
    this.totalSeconds = 120 * 60;
    this.remainingSeconds = this.totalSeconds;
    this.timerInterval = null;
    this.startTime = null;

    // 考生档案
    this.candidate = {
      name: "张明远",
      ticket: "CBA202610180088",
      idCard: "11010119980512889X",
      seat: "第 038 号机位"
    };

    this.initDOM();
    this.initKeyboard();
  }

  initDOM() {
    // 考前核验模态框
    this.ticketModal = document.getElementById("ticketModal");
    this.reportModal = document.getElementById("reportModal");

    // 绑定开考按钮
    const startExamBtn = document.getElementById("startExamBtn");
    if (startExamBtn) {
      startExamBtn.addEventListener("click", () => {
        this.startExam();
      });
    }

    // 绑定交卷按钮 (PC 顶栏 + 移动端底栏)
    const submitBtn = document.getElementById("headerSubmitBtn");
    if (submitBtn) {
      submitBtn.addEventListener("click", () => {
        this.promptSubmit();
      });
    }
    const footerSubmitBtn = document.getElementById("footerSubmitBtn");
    if (footerSubmitBtn) {
      footerSubmitBtn.addEventListener("click", () => {
        this.promptSubmit();
      });
    }

    // 移动端题号抽屉控制 (Drawer Sheet)
    const sidebar = document.getElementById("examSidebar");
    const backdrop = document.getElementById("drawerBackdrop");
    const openDrawer = () => {
      if (sidebar) sidebar.classList.add("open");
      if (backdrop) backdrop.classList.add("active");
    };
    const closeDrawer = () => {
      if (sidebar) sidebar.classList.remove("open");
      if (backdrop) backdrop.classList.remove("active");
    };
    this.closeDrawer = closeDrawer;

    const toggleDrawerBtn = document.getElementById("btnToggleDrawer");
    if (toggleDrawerBtn) {
      toggleDrawerBtn.addEventListener("click", () => {
        if (sidebar && sidebar.classList.contains("open")) {
          closeDrawer();
        } else {
          openDrawer();
        }
      });
    }

    const mobileGridBtn = document.getElementById("btnMobileGrid");
    if (mobileGridBtn) {
      mobileGridBtn.addEventListener("click", () => {
        if (sidebar && sidebar.classList.contains("open")) {
          closeDrawer();
        } else {
          openDrawer();
        }
      });
    }

    const closeDrawerBtn = document.getElementById("btnCloseDrawer");
    if (closeDrawerBtn) {
      closeDrawerBtn.addEventListener("click", closeDrawer);
    }
    if (backdrop) {
      backdrop.addEventListener("click", closeDrawer);
    }

    // 模式切换按钮
    const modeBtn = document.getElementById("modeToggleBtn");
    if (modeBtn) {
      modeBtn.addEventListener("click", () => {
        this.toggleMode();
      });
    }

    // 上一题 / 下一题
    document.getElementById("btnPrevQ").addEventListener("click", () => {
      this.goToPrev();
    });
    document.getElementById("btnNextQ").addEventListener("click", () => {
      this.goToNext();
    });

    // 标记本题
    document.getElementById("btnFlagQ").addEventListener("click", () => {
      this.toggleFlagCurrent();
    });

    // 试卷选择器下拉
    const paperSelect = document.getElementById("paperSelect");
    if (paperSelect) {
      paperSelect.addEventListener("change", (e) => {
        const paperId = e.target.value;
        if (this.status === "IN_EXAM" && Object.keys(this.userAnswers).length > 0) {
          if (!confirm("⚠️ 当前正在作答中，切换试卷将清空当前进度，确定要切换吗？")) {
            if (this.currentPaper) {
              paperSelect.value = this.currentPaper.id;
            }
            return;
          }
        }
        if (PRESET_PAPERS[paperId]) {
          this.loadPaper(PRESET_PAPERS[paperId]);
        }
      });
    }

    // 全屏按钮 (F11 提示)
    const fsBtn = document.getElementById("fullscreenBtn");
    if (fsBtn) {
      fsBtn.addEventListener("click", () => {
        this.toggleFullScreen();
      });
    }
  }

  initKeyboard() {
    document.addEventListener("keydown", (e) => {
      // 避免输入框中触发快捷键
      if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        this.goToPrev();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        this.goToNext();
      } else if (e.key.toLowerCase() === "m") {
        e.preventDefault();
        this.toggleFlagCurrent();
      } else if (["a", "b", "c", "d", "e"].includes(e.key.toLowerCase())) {
        const letter = e.key.toUpperCase();
        this.handleOptionSelect(letter);
      }
    });
  }

  loadPaper(paper) {
    this.currentPaper = paper;
    this.currentIndex = 0;
    this.userAnswers = {};
    this.flaggedQuestions.clear();
    this.status = "PRE_EXAM";
    this.totalSeconds = (paper.durationMinutes || 120) * 60;
    this.remainingSeconds = this.totalSeconds;
    clearInterval(this.timerInterval);

    // 更新界面标题
    document.getElementById("examHeaderTitle").textContent = paper.title;
    document.getElementById("examHeaderSubtitle").textContent = `标准时长: ${paper.durationMinutes} 分钟 · 总满分: ${paper.totalScore} 分 · 考场专用无纸化系统`;
    
    // 更新试卷下拉框选中状态
    const paperSelect = document.getElementById("paperSelect");
    if (paperSelect && paper.id) {
      paperSelect.value = paper.id;
    }

    // 更新准考证信息
    document.getElementById("ticketSubject").textContent = paper.subject;
    document.getElementById("ticketDuration").textContent = `${paper.durationMinutes} 分钟`;

    // 渲染左侧导航方阵
    this.renderSidebar();
    // 渲染第一题
    this.renderCurrentQuestion();
    // 弹出考前核对窗口
    this.showTicketModal();
  }

  showTicketModal() {
    this.ticketModal.classList.add("active");
  }

  hideTicketModal() {
    this.ticketModal.classList.remove("active");
  }

  startExam() {
    this.hideTicketModal();
    this.status = "IN_EXAM";
    this.startTime = Date.now();
    this.startTimer();
  }

  startTimer() {
    clearInterval(this.timerInterval);
    this.updateTimerDisplay();

    this.timerInterval = setInterval(() => {
      this.remainingSeconds--;
      this.updateTimerDisplay();

      if (this.remainingSeconds <= 0) {
        clearInterval(this.timerInterval);
        alert("⏰ 考试时间到，系统已自动交卷！");
        this.calculateAndShowReport();
      }
    }, 1000);
  }

  updateTimerDisplay() {
    const hours = Math.floor(this.remainingSeconds / 3600);
    const minutes = Math.floor((this.remainingSeconds % 3600) / 60);
    const seconds = this.remainingSeconds % 60;
    const str = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    
    const el = document.getElementById("examTimer");
    el.textContent = str;

    // 剩余 15 分钟警示
    if (this.remainingSeconds < 15 * 60) {
      el.classList.add("warning");
    } else {
      el.classList.remove("warning");
    }
  }

  toggleMode() {
    this.mode = this.mode === "MOCK" ? "PRACTICE" : "MOCK";
    const badge = document.getElementById("modeToggleBtn");
    if (this.mode === "MOCK") {
      badge.textContent = "全真模考";
      badge.style.background = "#fa8c16";
    } else {
      badge.textContent = "背题模式";
      badge.style.background = "#52c41a";
    }
    this.renderCurrentQuestion();
  }

  toggleFullScreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  // 渲染左侧题型与题号矩阵
  renderSidebar() {
    const container = document.getElementById("sidebarContent");
    container.innerHTML = "";

    // 按 section 分组
    const sections = {};
    this.currentPaper.questions.forEach((q, idx) => {
      const sec = q.section || "试题列表";
      if (!sections[sec]) sections[sec] = [];
      sections[sec].push({ q, idx });
    });

    for (const [secName, qList] of Object.entries(sections)) {
      const groupEl = document.createElement("div");
      groupEl.className = "section-group";

      const headerEl = document.createElement("div");
      headerEl.className = "section-header";
      headerEl.innerHTML = `
        <span>${secName} (${qList.length}题)</span>
        <span class="section-score-tag">每题 ${qList[0].q.score} 分</span>
      `;
      groupEl.appendChild(headerEl);

      const gridEl = document.createElement("div");
      gridEl.className = "q-grid";

      qList.forEach(({ q, idx }) => {
        const box = document.createElement("div");
        box.className = "q-box";
        box.id = `qbox_${idx}`;
        box.textContent = idx + 1;
        box.addEventListener("click", () => {
          this.goToQuestion(idx);
          if (window.innerWidth <= 768 && this.closeDrawer) {
            this.closeDrawer();
          }
        });
        gridEl.appendChild(box);
      });

      groupEl.appendChild(gridEl);
      container.appendChild(groupEl);
    }

    this.updateSidebarStatuses();
  }

  updateSidebarStatuses() {
    this.currentPaper.questions.forEach((q, idx) => {
      const box = document.getElementById(`qbox_${idx}`);
      if (!box) return;

      const ans = this.userAnswers[q.id];
      const hasAnswered = ans !== undefined && ans !== "";
      const isFlagged = this.flaggedQuestions.has(q.id);
      const isActive = idx === this.currentIndex;

      box.classList.toggle("answered", hasAnswered);
      box.classList.toggle("flagged", isFlagged);
      box.classList.toggle("active", isActive);

      // 考后复盘状态
      if (this.status === "SUBMITTED") {
        const isCorrect = this.isAnswerCorrect(q, ans);
        box.classList.toggle("correct", isCorrect);
        box.classList.toggle("wrong", !isCorrect);
      }
    });
  }

  // 渲染当前题目
  renderCurrentQuestion() {
    const q = this.currentPaper.questions[this.currentIndex];
    if (!q) return;

    // 元数据
    document.getElementById("qTypeBadge").textContent = q.section || "选择题";
    
    // 2026新规考点徽标
    const reformedBadge = document.getElementById("reformedBadge");
    if (reformedBadge) {
      if (q.is_reformed) {
        reformedBadge.textContent = "🔥 2026新规考点";
        reformedBadge.style.display = "inline-block";
      } else {
        reformedBadge.style.display = "none";
      }
    }

    document.getElementById("qNumberIndicator").textContent = `第 ${this.currentIndex + 1} 题 / 共 ${this.currentPaper.questions.length} 题`;
    const mobInd = document.getElementById("mobileQIndicator");
    if (mobInd) {
      mobInd.textContent = `${this.currentIndex + 1} / ${this.currentPaper.questions.length}`;
    }
    document.getElementById("qScoreIndicator").textContent = `本题分值: ${q.score} 分`;

    // 题干 (支持 KaTeX 与公式美化)
    this.formatMathContent(document.getElementById("qStem"), q.question);

    // 选项列表
    const optContainer = document.getElementById("qOptionsList");
    optContainer.innerHTML = "";

    const userAns = this.userAnswers[q.id] || "";
    const isMultiple = q.type === "multiple";

    for (const [key, text] of Object.entries(q.options)) {
      const item = document.createElement("div");
      item.className = "option-item";

      const isSelected = isMultiple
        ? userAns.includes(key)
        : userAns === key;

      if (isSelected) item.classList.add("selected");

      const input = document.createElement("input");
      input.type = isMultiple ? "checkbox" : "radio";
      input.name = `opt_${q.id}`;
      input.value = key;
      input.checked = isSelected;
      input.className = isMultiple ? "option-checkbox" : "option-radio";

      item.appendChild(input);

      const label = document.createElement("span");
      label.className = "option-label";
      label.textContent = `${key}.`;
      item.appendChild(label);

      const textEl = document.createElement("span");
      textEl.className = "option-text";
      this.formatMathContent(textEl, text);
      item.appendChild(textEl);

      item.addEventListener("click", () => {
        this.handleOptionSelect(key);
      });

      optContainer.appendChild(item);
    }

    // 标记按钮状态
    const flagBtn = document.getElementById("btnFlagQ");
    const isFlagged = this.flaggedQuestions.has(q.id);
    flagBtn.classList.toggle("flagged", isFlagged);
    document.getElementById("flagBtnText").textContent = isFlagged ? "已标记此题" : "标记本题";

    // 导航按钮置灰控制
    document.getElementById("btnPrevQ").disabled = this.currentIndex === 0;
    document.getElementById("btnNextQ").disabled =
      this.currentIndex === this.currentPaper.questions.length - 1;

    // 解析与口诀卡片
    const expCard = document.getElementById("qExplanationCard");
    const showExp = this.mode === "PRACTICE" || this.status === "SUBMITTED";

    if (showExp) {
      expCard.classList.add("visible");
      document.getElementById("expCorrectAns").textContent = q.answer;
      this.formatMathContent(document.getElementById("expBody"), q.explanation || "暂无详细解析");
      
      const mneEl = document.getElementById("expMnemonic");
      if (mneEl) {
        mneEl.textContent = q.mnemonic
          ? `🔑 考点速记口诀：${q.mnemonic}`
          : "";
        mneEl.style.display = q.mnemonic ? "block" : "none";
      }

      const trapEl = document.getElementById("expTrap");
      if (trapEl) {
        if (q.trap) {
          this.formatMathContent(trapEl, q.trap);
          trapEl.style.display = "block";
        } else {
          trapEl.style.display = "none";
        }
      }
    } else {
      expCard.classList.remove("visible");
    }

    this.updateSidebarStatuses();
  }

  // 智能公式与格式化解析渲染引擎
  formatMathContent(element, rawText) {
    if (!element) return;
    if (!rawText) {
      element.innerHTML = "";
      return;
    }

    // 注入零宽隐形数字盲水印 (Steganographic Invisible Watermark)
    if (window.injectInvisibleWatermark) {
      rawText = window.injectInvisibleWatermark(rawText);
    }

    // 1. 如果支持 KaTeX 渲染
    if (window.katex) {
      const escaped = rawText
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

      const rendered = escaped.replace(/\$([^\$]+)\$/g, (match, expr) => {
        try {
          const unescapedExpr = expr
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&amp;/g, "&");
          return window.katex.renderToString(unescapedExpr, {
            throwOnError: false,
            displayMode: false
          });
        } catch (e) {
          return match;
        }
      });
      element.innerHTML = rendered;
    } else {
      // 2. 无 KaTeX 时的平滑转义，确保公式人类可读
      let clean = rawText
        .replace(/\$([^\$]+)\$/g, "$1")
        .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1) / ($2)")
        .replace(/\\times/g, " × ")
        .replace(/\\approx/g, " ≈ ")
        .replace(/\\sum_\{[^}]+\}\^\{[^}]+\}/g, "∑")
        .replace(/\\%/g, "%")
        .replace(/\\_/g, "_");
      element.textContent = clean;
    }
  }

  handleOptionSelect(key) {
    const q = this.currentPaper.questions[this.currentIndex];
    if (!q) return;

    if (q.type === "multiple") {
      let current = this.userAnswers[q.id] || "";
      if (current.includes(key)) {
        current = current.replace(key, "");
      } else {
        current += key;
      }
      // 字母排序
      this.userAnswers[q.id] = current.split("").sort().join("");
    } else {
      this.userAnswers[q.id] = key;
    }

    this.renderCurrentQuestion();
  }

  toggleFlagCurrent() {
    const q = this.currentPaper.questions[this.currentIndex];
    if (!q) return;

    if (this.flaggedQuestions.has(q.id)) {
      this.flaggedQuestions.delete(q.id);
    } else {
      this.flaggedQuestions.add(q.id);
    }
    this.renderCurrentQuestion();
  }

  goToQuestion(index) {
    if (index >= 0 && index < this.currentPaper.questions.length) {
      this.currentIndex = index;
      this.renderCurrentQuestion();
    }
  }

  goToPrev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.renderCurrentQuestion();
    }
  }

  goToNext() {
    if (this.currentIndex < this.currentPaper.questions.length - 1) {
      this.currentIndex++;
      this.renderCurrentQuestion();
    }
  }

  isAnswerCorrect(q, userAns) {
    if (!userAns) return false;
    const cleanUser = userAns.trim().toUpperCase();
    const cleanCorrect = q.answer.trim().toUpperCase();
    return cleanUser === cleanCorrect;
  }

  // 交卷逻辑与未作答防漏提醒
  promptSubmit() {
    let unansweredCount = 0;
    this.currentPaper.questions.forEach((q) => {
      const ans = this.userAnswers[q.id];
      if (!ans) unansweredCount++;
    });

    let msg = "您确定现在要提交试卷吗？";
    if (unansweredCount > 0) {
      msg = `⚠️ 注意：您还有 ${unansweredCount} 道试题未作答！\n确定要提前交卷吗？`;
    }

    if (confirm(msg)) {
      this.calculateAndShowReport();
    }
  }

  calculateAndShowReport() {
    clearInterval(this.timerInterval);
    this.status = "SUBMITTED";

    let totalEarned = 0;
    let correctCount = 0;
    let wrongCount = 0;
    let unattemptedCount = 0;

    this.currentPaper.questions.forEach((q) => {
      const userAns = this.userAnswers[q.id];
      if (!userAns) {
        unattemptedCount++;
      } else if (this.isAnswerCorrect(q, userAns)) {
        totalEarned += q.score;
        correctCount++;
      } else {
        wrongCount++;
      }
    });

    const totalPossible = this.currentPaper.totalScore || 100;
    const passThreshold = totalPossible * 0.6;
    const isPass = totalEarned >= passThreshold;
    const accuracy = ((correctCount / this.currentPaper.questions.length) * 100).toFixed(1);
    const timeSpentSeconds = Math.max(1, Math.floor((Date.now() - (this.startTime || Date.now())) / 1000));
    const timeSpentMin = Math.ceil(timeSpentSeconds / 60);

    // 渲染模态框成绩单
    const stampEl = document.getElementById("reportStamp");
    stampEl.textContent = isPass ? "成绩合格" : "未及格";
    stampEl.className = `report-stamp ${isPass ? "" : "fail"}`;

    document.getElementById("reportScore").textContent = `${totalEarned.toFixed(1)} / ${totalPossible}`;
    document.getElementById("statCorrect").textContent = correctCount;
    document.getElementById("statWrong").textContent = wrongCount;
    document.getElementById("statUnattempted").textContent = unattemptedCount;
    document.getElementById("statTimeSpent").textContent = `${timeSpentMin} 分钟`;

    this.reportModal.classList.add("active");
    this.renderCurrentQuestion();
    this.updateSidebarStatuses();
  }

  hideReportModal() {
    this.reportModal.classList.remove("active");
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = ExamCore;
}
