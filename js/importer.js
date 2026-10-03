/**
 * 2026 银行从业机考 · 智能试题导入引擎 (importer.js)
 * 特性：
 * 1. 智能自然文本解析器：支持任意来源文本复制粘贴（大模型生成、文档、网页），容错强
 * 2. 自动分类单选/多选/判断题型、提取题干、选项、答案、解析与助记口诀
 * 3. 支持 JSON 试题文件拖拽导入与一键导出备份
 */

class QuestionImporter {
  constructor() {
    this.modal = document.getElementById("importModal");
    this.textarea = document.getElementById("importTextarea");
    this.previewBadge = document.getElementById("importPreviewBadge");
    this.activeImportTab = "text";
    this.parsedQuestions = [];

    this.initEvents();
  }

  initEvents() {
    // 导入模态框内的标签切换
    document.querySelectorAll(".import-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        this.activeImportTab = btn.dataset.tab;
        document.querySelectorAll(".import-tab-btn").forEach((b) => {
          b.classList.toggle("active", b === btn);
        });
        document.getElementById("importTextPanel").style.display =
          this.activeImportTab === "text" ? "block" : "none";
        document.getElementById("importJsonPanel").style.display =
          this.activeImportTab === "json" ? "block" : "none";
      });
    });

    // 实时监听文本输入并即时智能解析
    if (this.textarea) {
      this.textarea.addEventListener("input", () => {
        this.parseTextContent();
      });
    }

    // 载入示例试题模板
    const loadSampleBtn = document.getElementById("loadSampleTextBtn");
    if (loadSampleBtn) {
      loadSampleBtn.addEventListener("click", () => {
        this.loadSampleTemplate();
      });
    }

    // 确认导入试题
    const confirmBtn = document.getElementById("confirmImportBtn");
    if (confirmBtn) {
      confirmBtn.addEventListener("click", () => {
        this.applyImport();
      });
    }

    // 拖拽与文件上传 JSON
    const fileInput = document.getElementById("jsonFileInput");
    if (fileInput) {
      fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) this.readJsonFile(file);
      });
    }

    // 导出当前考卷为 JSON
    const exportBtn = document.getElementById("exportJsonBtn");
    if (exportBtn) {
      exportBtn.addEventListener("click", () => {
        this.exportCurrentPaper();
      });
    }
  }

  show() {
    this.modal.classList.add("active");
  }

  hide() {
    this.modal.classList.remove("active");
  }

  loadSampleTemplate() {
    const sample = `1. 根据资管新规，下列关于商业银行理财产品的说法正确的是：
A. 商业银行可以发行保本保收益的预期收益型理财产品
B. 商业银行理财产品必须实行净值化管理，严禁刚性兑付
C. 银行可向保守型客户推荐高风险权益类产品
D. 理财产品可以承诺最低收益率
【答案】B
【解析】资管新规彻底终结了预期收益型和保本时代，全面实行净值化转型。
【口诀】资管新规破刚兑，净值波动自负盈亏。

2. 根据我国商业银行资本管理要求，下列属于核心一级资本的有哪些？
A. 实收资本或普通股
B. 资本公积
C. 盈余公积
D. 未分配利润
E. 优先股
【答案】ABCD
【解析】核心一级资本包括普通股、资本公积、盈余公积和未分配利润等。优先股属于其他一级资本。
【口诀】普通股三公积加未分配，优先股算其他。

3. 商业银行在向关系人发放贷款时，可以向关系人发放信用贷款。
A. 正确
B. 错误
【答案】B
【解析】《商业银行法》明确禁止向关系人发放信用贷款。
【口诀】关系人严禁信用贷，担保贷款同待遇。`;

    this.textarea.value = sample;
    this.parseTextContent();
  }

  parseTextContent() {
    const raw = this.textarea.value.trim();
    if (!raw) {
      this.parsedQuestions = [];
      this.previewBadge.style.display = "none";
      return;
    }

    // 拆分题目块
    // 匹配题号开头，如 "1.", "1、", "第1题", "【1】"
    const lines = raw.split("\n");
    const blocks = [];
    let currentBlock = [];

    const isQuestionStart = (line) => {
      const trimmed = line.trim();
      return /^(?:\d+[\.、\s]|第\s*\d+\s*题|【\d+】)/.test(trimmed);
    };

    for (const line of lines) {
      if (isQuestionStart(line) && currentBlock.length > 0) {
        blocks.push(currentBlock.join("\n"));
        currentBlock = [line];
      } else {
        currentBlock.push(line);
      }
    }
    if (currentBlock.length > 0) {
      blocks.push(currentBlock.join("\n"));
    }

    const results = [];
    let singleCount = 0, multiCount = 0, judgeCount = 0;

    blocks.forEach((block, idx) => {
      const q = this.parseSingleBlock(block, idx + 1);
      if (q) {
        results.push(q);
        if (q.type === "single") singleCount++;
        else if (q.type === "multiple") multiCount++;
        else if (q.type === "judge") judgeCount++;
      }
    });

    this.parsedQuestions = results;
    if (results.length > 0) {
      this.previewBadge.style.display = "inline-block";
      this.previewBadge.textContent = `✅ 成功智能识别 ${results.length} 道试题 (单选 ${singleCount} 题，多选 ${multiCount} 题，判断 ${judgeCount} 题)`;
    } else {
      this.previewBadge.style.display = "inline-block";
      this.previewBadge.textContent = "⚠️ 未能识别到完整题目结构，请参考示例格式";
    }
  }

  parseSingleBlock(text, index) {
    const lines = text.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);
    if (lines.length < 2) return null;

    let questionStem = "";
    const options = {};
    let answer = "";
    let explanation = "";
    let mnemonic = "";

    let readingStem = true;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // 匹配答案
      const ansMatch = line.match(/(?:【?答案】?|正确答案|参考答案)\s*[:：]?\s*([A-Za-z对错正确错误]+)/);
      if (ansMatch) {
        readingStem = false;
        let rawAns = ansMatch[1].trim().toUpperCase();
        if (rawAns === "对" || rawAns === "正确") rawAns = "A";
        if (rawAns === "错" || rawAns === "错误") rawAns = "B";
        answer = rawAns;
        continue;
      }

      // 匹配解析
      const expMatch = line.match(/(?:【?解析】?|考点解析)\s*[:：]?\s*(.*)/);
      if (expMatch) {
        readingStem = false;
        explanation = expMatch[1].trim();
        // 吸收后续直到口诀的行
        for (let j = i + 1; j < lines.length; j++) {
          if (/【?口诀】?|助记口诀/.test(lines[j])) break;
          explanation += " " + lines[j].trim();
        }
        continue;
      }

      // 匹配口诀
      const mneMatch = line.match(/(?:【?口诀】?|助记口诀)\s*[:：]?\s*(.*)/);
      if (mneMatch) {
        readingStem = false;
        mnemonic = mneMatch[1].trim();
        continue;
      }

      // 匹配选项行 (A. A、 A) A: 等)
      const optMatch = line.match(/^([A-Ea-e])[\.、\s\)\:：]\s*(.+)$/);
      if (optMatch) {
        readingStem = false;
        const optKey = optMatch[1].toUpperCase();
        options[optKey] = optMatch[2].trim();
        continue;
      }

      // 题干拼接
      if (readingStem) {
        if (!questionStem) {
          // 清除题号前缀
          questionStem = line.replace(/^(?:\d+[\.、\s]|第\s*\d+\s*题|【\d+】)\s*/, "");
        } else {
          questionStem += " " + line;
        }
      }
    }

    if (!questionStem) return null;

    // 判断题型
    const optKeys = Object.keys(options).sort();
    let type = "single";
    let section = "单项选择题";

    // 如果没有选项，但答案包含 A/B 且题干有判断意图
    if (optKeys.length === 0) {
      options["A"] = "正确";
      options["B"] = "错误";
      type = "judge";
      section = "判断题";
    } else if (
      optKeys.length === 2 &&
      (options["A"].includes("正确") || options["A"].includes("对"))
    ) {
      type = "judge";
      section = "判断题";
    } else if (answer.length > 1) {
      type = "multiple";
      section = "多项选择题";
    } else {
      type = "single";
      section = "单项选择题";
    }

    return {
      id: `CUSTOM-Q${String(index).padStart(2, "0")}`,
      section,
      type,
      score: type === "multiple" ? 2.0 : 1.0,
      question: questionStem,
      options,
      answer: answer || "A",
      explanation: explanation || "暂无详细解析。",
      mnemonic: mnemonic || "温故而知新，熟记考点。"
    };
  }

  applyImport() {
    if (!this.parsedQuestions || this.parsedQuestions.length === 0) {
      alert("请先输入有效试题文本或载入示例！");
      return;
    }

    const customPaper = {
      id: "custom_" + Date.now(),
      title: `自定义导入题库 (${new Date().toLocaleDateString()})`,
      subject: "自定义考卷",
      durationMinutes: 120,
      totalScore: this.parsedQuestions.reduce((acc, q) => acc + q.score, 0),
      questions: this.parsedQuestions
    };

    // 存入全局题库并加载
    if (window.examCore) {
      window.examCore.loadPaper(customPaper);
      this.hide();
      alert(`🎉 成功导入 ${this.parsedQuestions.length} 道题目，考卷已就绪！`);
    }
  }

  readJsonFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (!data.questions || !Array.isArray(data.questions)) {
          throw new Error("JSON 格式不符合考卷规范（需包含 questions 数组）");
        }
        if (window.examCore) {
          window.examCore.loadPaper(data);
          this.hide();
          alert(`🎉 成功从文件导入试卷《${data.title || "自定义试卷"}》，共 ${data.questions.length} 题！`);
        }
      } catch (err) {
        alert("❌ 读取试卷失败: " + err.message);
      }
    };
    reader.readAsText(file);
  }

  exportCurrentPaper() {
    if (!window.examCore || !window.examCore.currentPaper) {
      alert("当前没有正在运行的考卷可导出");
      return;
    }
    const paper = window.examCore.currentPaper;
    const blob = new Blob([JSON.stringify(paper, null, 2)], {
      type: "application/json;charset=utf-8"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${paper.subject || "银行从业"}_全真试卷_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = QuestionImporter;
}
