// 原生 PPTX 生成：文字是真文字，形状是原生形状，只有两张运行截图是图片。
// 用法：node presentation/build_deck.js [输出路径]
// 换视觉只改下面的 C（配色）和 F（字体）；换内容只改各页的文本。
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const HERE = __dirname;
const EV   = path.join(HERE, 'evidence');
const OUT  = process.argv[2] || path.join(HERE, 'QC-Team.pptx');

const C = {
  deep:  '1B3A6B',   // 主蓝
  mid:   '4A7EBB',   // 中蓝
  soft:  '9CBEE3',   // 浅蓝
  wash:  'EAF1FA',   // 蓝底纹
  page:  'F7FAFD',   // 页底
  ink:   '1F2A37',
  grey:  '6B7A8C',
  line:  'D6E0EC',
  red:   'C0392B',
  green: '1E7A5E',
  white: 'FFFFFF',
};
const F = '苹方-简';
const W = 13.333, H = 7.5;

const pptx = new PptxGenJS();
pptx.defineLayout({ name: 'WIDE169', width: 13.333, height: 7.5 });
pptx.layout = 'WIDE169';
pptx.author = '王彩迪';
pptx.title = 'QC-Team 作业质检系统';

// ---------- 装饰构件 ----------
function dots(s, x, y, color = C.mid) {
  for (let i = 0; i < 4; i++) {
    s.addShape(pptx.ShapeType.ellipse, {
      x: x + i * 0.28, y, w: 0.13, h: 0.13,
      fill: { color, transparency: i * 18 }, line: { type: 'none' },
    });
  }
}

// 内容页外壳：细边框 + 左上角标签 + 标题 + 细线 + 右下装饰点
function shell(s, { tag, title, sub, footer }) {
  s.background = { color: C.page };
  // 左侧竖向渐变带（用三段不同透明度模拟渐变）
  for (let i = 0; i < 3; i++) {
    s.addShape(pptx.ShapeType.rect, {
      x: 0, y: i * (H / 3), w: 0.16, h: H / 3,
      fill: { color: C.mid, transparency: 15 + i * 25 }, line: { type: 'none' },
    });
  }
  // 右上角斜切装饰
  s.addShape(pptx.ShapeType.rtTriangle, {
    x: W - 2.6, y: 0, w: 2.6, h: 1.35, rotate: 180,
    fill: { color: C.wash }, line: { type: 'none' },
  });
  s.addShape(pptx.ShapeType.rtTriangle, {
    x: W - 1.5, y: 0, w: 1.5, h: 0.78, rotate: 180,
    fill: { color: C.soft, transparency: 45 }, line: { type: 'none' },
  });
  // 标签
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.62, y: 0.42, w: 0.22 + tag.length * 0.115, h: 0.34,
    fill: { color: C.deep }, line: { type: 'none' }, rectRadius: 0.06,
  });
  s.addText(tag, {
    x: 0.62, y: 0.42, w: 0.22 + tag.length * 0.115, h: 0.34,
    fontFace: F, fontSize: 11, bold: true, color: C.white, align: 'center', valign: 'middle',
  });
  // 标题
  s.addText(title, {
    x: 0.62, y: 0.88, w: W - 1.9, h: 0.62,
    fontFace: F, fontSize: 27, bold: true, color: C.deep, valign: 'middle',
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 0.62, y: 1.52, w: 1.5, h: 0.045, fill: { color: C.mid }, line: { type: 'none' },
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 2.12, y: 1.545, w: W - 2.74 - 0.62, h: 0.012, fill: { color: C.line }, line: { type: 'none' },
  });
  if (sub) s.addText(sub, {
    x: 0.62, y: 1.62, w: W - 1.9, h: 0.34,
    fontFace: F, fontSize: 13, color: C.grey, valign: 'middle',
  });
  if (footer) s.addText(footer, {
    x: 0.62, y: H - 0.62, w: W - 2.4, h: 0.34,
    fontFace: F, fontSize: 10.5, color: C.grey, valign: 'middle',
  });
  dots(s, W - 1.5, H - 0.52);
}

// 底部结论条
function banner(s, text, y = H - 1.42) {
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.62, y, w: W - 1.24, h: 0.62,
    fill: { color: C.deep }, line: { type: 'none' }, rectRadius: 0.08,
  });
  s.addText(text, {
    x: 0.62, y, w: W - 1.24, h: 0.62,
    fontFace: F, fontSize: 15.5, bold: true, color: C.white, align: 'center', valign: 'middle',
  });
}

// ---------- 1 封面 ----------
{
  const s = pptx.addSlide();
  s.background = { color: C.page };
  s.addShape(pptx.ShapeType.rtTriangle, {
    x: 0, y: H - 3.1, w: 6.4, h: 3.1, fill: { color: C.mid, transparency: 8 }, line: { type: 'none' },
  });
  s.addShape(pptx.ShapeType.rtTriangle, {
    x: 0, y: H - 2.0, w: 4.2, h: 2.0, fill: { color: C.deep, transparency: 15 }, line: { type: 'none' },
  });
  s.addShape(pptx.ShapeType.rtTriangle, {
    x: W - 4.6, y: 0, w: 4.6, h: 2.4, rotate: 180, fill: { color: C.wash }, line: { type: 'none' },
  });
  s.addText('QC-Team', {
    x: 0.95, y: 1.85, w: 9, h: 1.1,
    fontFace: F, fontSize: 52, bold: true, color: C.deep,
  });
  s.addText('一份作业发过来，我能保证什么', {
    x: 0.95, y: 2.95, w: 10, h: 0.7,
    fontFace: F, fontSize: 25, color: C.ink,
  });
  s.addText('ACADEMIC  QC  PIPELINE   ·   COMMAND-LINE  AGENT  TEAM', {
    x: 0.98, y: 3.62, w: 10, h: 0.34,
    fontFace: 'Helvetica Neue', fontSize: 11.5, color: C.mid, charSpacing: 2,
  });
  s.addShape(pptx.ShapeType.rect, { x: 0.98, y: 4.12, w: 0.9, h: 0.04, fill: { color: C.mid }, line: { type: 'none' } });
  s.addText('王彩迪　|　命令行课 · 第三课汇报　|　2026 年 8 月 25 日', {
    x: 0.98, y: 4.32, w: 9, h: 0.36, fontFace: F, fontSize: 13, color: C.grey,
  });
  dots(s, W - 1.9, H - 0.85, C.deep);
}

// ---------- 2 业务背景 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'WHY  THIS  EXISTS',
    title: '最需要守住的是两类高风险问题，人工逐条查既慢又漏',
    sub: '留学作业交付前，真正要守住的是学术诚信红线',
    footer: '这不是挑错别字的活，是守住「能不能交」的红线。',
  });
  const cards = [
    { n: '01', t: '文献是编的', d: '参考文献根本不存在。\n问 AI「这篇真吗」，它会\n幻觉出一篇看着很真的假论文。', c: C.red, tag: '代价：学术诚信风险' },
    { n: '02', t: '引用被用反了', d: '文献真实存在，但原文结论\n与稿件拿它支撑的论点\n方向相反。', c: C.deep, tag: '代价：结论失真与返工' },
  ];
  cards.forEach((k, i) => {
    const x = 0.62 + i * 4.55;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 2.18, w: 4.2, h: 2.9,
      fill: { color: i ? C.wash : 'FBEDEB' }, line: { color: i ? C.soft : 'EEC4BE', width: 1 }, rectRadius: 0.1,
    });
    s.addText(k.n, { x: x + 0.32, y: 2.34, w: 1.2, h: 0.6, fontFace: 'Helvetica Neue', fontSize: 31, bold: true, color: k.c });
    s.addText(k.t, { x: x + 0.32, y: 2.94, w: 3.5, h: 0.44, fontFace: F, fontSize: 19, bold: true, color: C.ink });
    s.addText(k.d, { x: x + 0.32, y: 3.42, w: 3.6, h: 1.0, fontFace: F, fontSize: 13, color: C.grey, lineSpacingMultiple: 1.25 });
    s.addShape(pptx.ShapeType.roundRect, { x: x + 0.32, y: 4.52, w: 2.5, h: 0.4, fill: { color: k.c }, line: { type: 'none' }, rectRadius: 0.07 });
    s.addText(k.tag, { x: x + 0.32, y: 4.52, w: 2.5, h: 0.4, fontFace: F, fontSize: 11, bold: true, color: C.white, align: 'center', valign: 'middle' });
  });
  // 右侧人工成本
  s.addText('人工核查', { x: 9.9, y: 2.2, w: 2.8, h: 0.32, fontFace: F, fontSize: 13, bold: true, color: C.grey });
  ['逐条找原文', '逐条比结论', '仍可能漏查'].forEach((t, i) => {
    s.addShape(pptx.ShapeType.ellipse, { x: 9.95, y: 2.72 + i * 0.62, w: 0.16, h: 0.16, fill: { color: C.red }, line: { type: 'none' } });
    s.addText(t, { x: 10.28, y: 2.62 + i * 0.62, w: 2.4, h: 0.36, fontFace: F, fontSize: 13, color: C.ink, valign: 'middle' });
  });
  s.addText('耗时长', { x: 9.9, y: 4.62, w: 2.6, h: 0.6, fontFace: F, fontSize: 30, bold: true, color: C.deep });
  s.addText('人工逐条回源，仍可能漏查', { x: 9.93, y: 5.18, w: 2.9, h: 0.3, fontFace: F, fontSize: 11, color: C.grey });
  banner(s, '这不是挑错别字的活，是守红线的活。');
}

// ---------- 3 上周能做到 / 做不到 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'BEFORE',
    title: '上周版本能出结果，但还不能承诺结果',
    sub: '一份作业发过来，系统已经有能力，但缺少可控制、可追责的过程',
    footer: '本周升级目标：把「模型流水线」变成「可被审计的组织」。',
  });
  const good = ['三个厂商模型分工审一遍', '假 DOI 走数据库真实核验', '输出红／黄／绿灯与修改清单', '一条命令可复用'];
  const bad  = ['跑挂了，不知道卡在哪一步', '上一步没干净，下一步照跑', '复核能看到主审答案', '结论无法回溯到证据'];
  [['已经能做到', good, C.green, '✓'], ['还做不到', bad, C.red, '✕']].forEach(([h, arr, col, mk], ci) => {
    const x = 0.75 + ci * 6.3;
    s.addText(h, { x, y: 2.18, w: 4, h: 0.34, fontFace: F, fontSize: 15, bold: true, color: col });
    s.addShape(pptx.ShapeType.rect, { x, y: 2.56, w: 5.4, h: 0.012, fill: { color: C.line }, line: { type: 'none' } });
    arr.forEach((t, i) => {
      const y = 2.78 + i * 0.62;
      s.addShape(pptx.ShapeType.ellipse, { x, y: y + 0.03, w: 0.3, h: 0.3, fill: { color: col }, line: { type: 'none' } });
      s.addText(mk, { x, y: y + 0.03, w: 0.3, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: C.white, align: 'center', valign: 'middle' });
      s.addText(t, { x: x + 0.44, y, w: 5, h: 0.36, fontFace: F, fontSize: 14.5, color: C.ink, valign: 'middle' });
    });
  });
  s.addShape(pptx.ShapeType.rect, { x: 6.5, y: 2.18, w: 0.012, h: 3.0, fill: { color: C.line }, line: { type: 'none' } });
  banner(s, '能出结果  ≠  敢承诺结果');
}

// ---------- 4 转折页 ----------
{
  const s = pptx.addSlide();
  s.background = { color: C.deep };
  s.addShape(pptx.ShapeType.rtTriangle, { x: 0, y: H - 2.6, w: 5.2, h: 2.6, fill: { color: C.mid, transparency: 60 }, line: { type: 'none' } });
  s.addShape(pptx.ShapeType.rtTriangle, { x: W - 3.6, y: 0, w: 3.6, h: 1.9, rotate: 180, fill: { color: C.mid, transparency: 65 }, line: { type: 'none' } });
  s.addText('THE  SHIFT', { x: 0.95, y: 0.7, w: 5, h: 0.36, fontFace: 'Helvetica Neue', fontSize: 12, bold: true, color: C.soft, charSpacing: 3 });
  s.addText('这周改的不是功能，是它的性质', { x: 0.95, y: 2.6, w: 11.4, h: 1.0, fontFace: F, fontSize: 40, bold: true, color: C.white, align: 'center' });
  s.addText('从「跑完了吗」，到「敢不敢签字」', { x: 0.95, y: 3.7, w: 11.4, h: 0.6, fontFace: F, fontSize: 20, color: C.soft, align: 'center' });
  s.addShape(pptx.ShapeType.rect, { x: 5.9, y: 4.5, w: 1.5, h: 0.035, fill: { color: C.soft }, line: { type: 'none' } });
  s.addText('工具关心结果；组织关心谁做的、凭什么、能不能查。', { x: 0.95, y: 4.8, w: 11.4, h: 0.4, fontFace: F, fontSize: 14, color: C.soft, align: 'center' });
  dots(s, W - 1.9, H - 0.85, C.soft);
}

// ---------- 5 状态机 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'UPGRADE  01',
    title: '给每一步定状态，跑挂了能立刻定位',
    sub: '五种状态由程序判定并独占写入，不接受 Agent 自报「我完成了」',
    footer: '业务价值：失败不会被当成成功继续往下传，能定位到「第几步、谁没交货」。',
  });
  const st = [
    { t: 'BLOCKED',   c: '8896A6' }, { t: 'READY', c: C.mid },
    { t: 'RUNNING',   c: C.deep },   { t: 'COMPLETED', c: C.green },
  ];
  st.forEach((k, i) => {
    const x = 1.0 + i * 2.75;
    s.addShape(pptx.ShapeType.ellipse, { x, y: 2.35, w: 1.15, h: 1.15, fill: { color: k.c }, line: { type: 'none' } });
    s.addText(String(i + 1).padStart(2, '0'), { x, y: 2.35, w: 1.15, h: 1.15, fontFace: 'Helvetica Neue', fontSize: 17, bold: true, color: C.white, align: 'center', valign: 'middle' });
    s.addText(k.t, { x: x - 0.35, y: 3.62, w: 1.85, h: 0.32, fontFace: 'Helvetica Neue', fontSize: 12.5, bold: true, color: k.c, align: 'center' });
    if (i < 3) s.addShape(pptx.ShapeType.rect, { x: x + 1.3, y: 2.88, w: 1.3, h: 0.05, fill: { color: C.line }, line: { type: 'none' } });
  });
  // FAILED 分支
  s.addShape(pptx.ShapeType.rect, { x: 7.05, y: 3.5, w: 0.05, h: 1.15, fill: { color: C.red }, line: { type: 'none' } });
  s.addShape(pptx.ShapeType.ellipse, { x: 6.5, y: 4.62, w: 1.15, h: 1.15, fill: { color: C.red }, line: { type: 'none' } });
  s.addText('!', { x: 6.5, y: 4.62, w: 1.15, h: 1.15, fontFace: F, fontSize: 22, bold: true, color: C.white, align: 'center', valign: 'middle' });
  s.addText('FAILED', { x: 7.78, y: 5.0, w: 1.4, h: 0.36, fontFace: 'Helvetica Neue', fontSize: 12.5, bold: true, color: C.red, valign: 'middle' });
  s.addShape(pptx.ShapeType.rect, { x: 2.3, y: 5.17, w: 4.2, h: 0.035, fill: { color: C.red, transparency: 35 }, line: { type: 'none' } });
  s.addText('修复依赖后回到 READY', { x: 2.3, y: 4.72, w: 4.2, h: 0.36, fontFace: F, fontSize: 12, bold: true, color: C.red, align: 'center' });
  // 判据框
  s.addShape(pptx.ShapeType.roundRect, { x: 9.3, y: 4.55, w: 3.4, h: 1.15, fill: { color: C.wash }, line: { color: C.soft, width: 1 }, rectRadius: 0.08 });
  s.addText('COMPLETED 判据', { x: 9.55, y: 4.68, w: 3, h: 0.32, fontFace: F, fontSize: 12, color: C.grey });
  s.addText('exit 0  +  产物字节数 > 0', { x: 9.55, y: 5.02, w: 3, h: 0.42, fontFace: F, fontSize: 15, bold: true, color: C.deep });
}

// ---------- 6 闸门 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'UPGRADE  02',
    title: '给每一关设凭证，杜绝「差不多就过」',
    sub: '五道闸门是许可链，不是装饰性的流程图',
    footer: '业务价值：文献没核完不准判断；强核未一致不准放行。顺序本身就是权限。',
  });
  const g = [
    ['G1', '来源', '来源已声明'], ['G2', '基线', '稿件已冻结'], ['G3', '文献', 'DOI 有回执'],
    ['G4', '双强核', '关键事实 2/2'], ['G5', '放行', '八板块齐全'],
  ];
  g.forEach((k, i) => {
    const x = 0.95 + i * 2.42;
    s.addShape(pptx.ShapeType.diamond, {
      x, y: 2.4, w: 1.7, h: 1.5,
      fill: { color: i === 4 ? C.green : C.deep }, line: { type: 'none' },
    });
    s.addText(`${k[0]}\n${k[1]}`, { x, y: 2.4, w: 1.7, h: 1.5, fontFace: F, fontSize: 13, bold: true, color: C.white, align: 'center', valign: 'middle', lineSpacingMultiple: 1.15 });
    s.addText(k[2], { x: x - 0.25, y: 4.05, w: 2.2, h: 0.34, fontFace: F, fontSize: 12.5, bold: true, color: C.ink, align: 'center' });
    if (i < 4) s.addShape(pptx.ShapeType.rect, { x: x + 1.78, y: 3.12, w: 0.6, h: 0.05, fill: { color: C.line }, line: { type: 'none' } });
  });
  s.addShape(pptx.ShapeType.rect, { x: 3.2, y: 4.85, w: 6.6, h: 0.035, fill: { color: C.red, transparency: 30 }, line: { type: 'none' } });
  s.addText('任一凭证缺失：阻断并回到对应环节', { x: 3.2, y: 4.98, w: 6.6, h: 0.36, fontFace: F, fontSize: 13, bold: true, color: C.red, align: 'center' });
}

// ---------- 7 责权利 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'UPGRADE  03',
    title: '把拍板权写死，换谁来跑都遵守同一套规则',
    sub: '「责、权、利」进入正式 Agent 契约，不再依赖临场默契',
    footer: 'AI 有提议权，没有上膛权；「利」不是工资，而是下一次继续被加载的资格。',
  });
  const head = ['角色', '责：必须交什么', '权：能决定什么', '利：为何被复用'];
  const cols = [0.85, 3.6, 7.1, 10.0];
  head.forEach((t, i) => s.addText(t, { x: cols[i], y: 2.18, w: 3.2, h: 0.34, fontFace: F, fontSize: 12.5, bold: true, color: C.grey }));
  s.addShape(pptx.ShapeType.rect, { x: 0.85, y: 2.56, w: 11.6, h: 0.02, fill: { color: C.deep }, line: { type: 'none' } });
  const rows = [
    ['主审', '按 D1–D7 给出判断', '强核票 1 / 2', '结论可回溯'],
    ['复核', '回原文核验关键事实', '强核票 1 / 2', '证据可复现'],
    ['整理者', '机械扫描并组织报告', '无票，可阻断', '产物可检查'],
  ];
  rows.forEach((r, ri) => {
    const y = 2.72 + ri * 0.86;
    if (ri % 2 === 0) s.addShape(pptx.ShapeType.rect, { x: 0.7, y: y - 0.08, w: 11.9, h: 0.78, fill: { color: C.wash, transparency: 40 }, line: { type: 'none' } });
    r.forEach((t, ci) => s.addText(t, {
      x: cols[ci], y, w: 3.2, h: 0.6,
      fontFace: F, fontSize: ci === 0 ? 16 : 14, bold: ci === 0 || ci === 2,
      color: ci === 0 ? C.deep : (ri === 2 && ci === 2 ? C.red : C.ink), valign: 'middle',
    }));
  });
  banner(s, '三个 Agent 都不直接写文件；编排器统一落盘，责任链才唯一。');
}

// ---------- 8 DIP × 质检 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'END-TO-END',
    title: 'DIP 与质检将串成一条线，生产闭环仍待实跑',
    sub: '从「写完了」到「敢交了」，每一次交接都留下可核验的指纹',
    footer: '业务价值：冻结后任何改动都能被发现，交付责任不再靠口头解释。',
  });
  const steps = [
    ['01', 'DIP 产稿', '接口已实现'], ['02', 'SHA-256 冻结', '适配器已测试'],
    ['03', 'QC-Team 验稿', '走完五道闸门'], ['04', '放行判断', '完整链路待实跑'],
  ];
  steps.forEach((k, i) => {
    const x = 1.05 + i * 3.0;
    s.addShape(pptx.ShapeType.ellipse, { x, y: 2.45, w: 1.3, h: 1.3, fill: { color: C.deep }, line: { color: C.soft, width: 1.5 } });
    s.addText(k[0], { x, y: 2.45, w: 1.3, h: 1.3, fontFace: 'Helvetica Neue', fontSize: 18, bold: true, color: C.white, align: 'center', valign: 'middle' });
    s.addText(k[1], { x: x - 0.62, y: 3.9, w: 2.55, h: 0.36, fontFace: F, fontSize: 15, bold: true, color: C.ink, align: 'center' });
    s.addText(k[2], { x: x - 0.62, y: 4.24, w: 2.55, h: 0.32, fontFace: F, fontSize: 12, color: C.grey, align: 'center' });
    if (i < 3) s.addShape(pptx.ShapeType.rect, { x: x + 1.42, y: 3.07, w: 1.42, h: 0.05, fill: { color: C.line }, line: { type: 'none' } });
  });
  s.addShape(pptx.ShapeType.roundRect, { x: 2.6, y: 4.95, w: 8.1, h: 0.62, fill: { color: 'FBEDEB' }, line: { color: 'EEC4BE', width: 1 }, rectRadius: 0.08 });
  s.addText('边界：交接脚本与测试已完成，真实 DIP production run 尚未发生。', {
    x: 2.6, y: 4.95, w: 8.1, h: 0.62, fontFace: F, fontSize: 13.5, bold: true, color: C.red, align: 'center', valign: 'middle',
  });
}

// ---------- 9 运行证据 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'EVIDENCE',
    title: '一次真实运行：假 DOI 被拦下，最终报告给出红灯',
    sub: '证据不放在口头承诺里，而放在运行记录、测试与可观察会话里',
    footer: '本次运行走 legacy 入口（python3 qc.py），五道闸门属 audited 入口，尚未在生产中跑过。　Agent View 是可观测层，不是 Agent Team 本身。',
  });
  const nums = [['16', '项自动化测试'], ['1', '次真实自动触发'], ['4', '轮模型交互（单次运行内）']];
  nums.forEach((k, i) => {
    const y = 2.25 + i * 1.15;
    s.addText(k[0], { x: 0.85, y, w: 1.5, h: 0.68, fontFace: 'Helvetica Neue', fontSize: 40, bold: true, color: i === 2 ? C.mid : C.deep });
    s.addText(k[1], { x: 0.9, y: y + 0.66, w: 3.0, h: 0.3, fontFace: F, fontSize: 11.5, color: C.grey });
  });
  s.addText('v1 曾因软链接失效与权限拒绝失败，v2 收紧 allowlist 后通过。', {
    x: 0.85, y: 5.72, w: 3.6, h: 0.6, fontFace: F, fontSize: 11.5, color: C.red, lineSpacingMultiple: 1.2,
  });
  s.addShape(pptx.ShapeType.roundRect, { x: 4.55, y: 2.1, w: 8.1, h: 2.0, fill: { color: C.white }, line: { color: C.line, width: 1 }, rectRadius: 0.08 });
  s.addImage({ path: `${EV}/claudepot-success.jpeg`, x: 4.72, y: 2.22, w: 7.76, h: 1.76, altText: 'Claudepot automation success evidence' });
  s.addShape(pptx.ShapeType.roundRect, { x: 4.55, y: 4.25, w: 8.1, h: 2.0, fill: { color: C.white }, line: { color: C.line, width: 1 }, rectRadius: 0.08 });
  s.addImage({ path: `${EV}/agent-view-completed.jpeg`, x: 4.72, y: 4.37, w: 7.76, h: 1.76, altText: 'Claude Agent View completed session evidence' });
  [['Claudepot · success', 2.24], ['Agent View · completed', 4.39]].forEach(([t, y]) => {
    s.addShape(pptx.ShapeType.roundRect, { x: 4.85, y, w: 2.35, h: 0.36, fill: { color: C.deep }, line: { type: 'none' }, rectRadius: 0.06 });
    s.addText(t, { x: 4.85, y, w: 2.35, h: 0.36, fontFace: F, fontSize: 11, bold: true, color: C.white, align: 'center', valign: 'middle' });
  });
}

// ---------- 10 边界与下一步 ----------
{
  const s = pptx.addSlide();
  shell(s, {
    tag: 'NEXT',
    title: '三项尚未完成，已明确列出并给出路径',
    sub: '把「定义了、测过了、真实跑过了」分开，可信度比全绿更重要',
    footer: 'GitHub · github.com/wangfeifei-321/qc-team',
  });
  s.addText('尚未完成', { x: 0.85, y: 2.18, w: 3, h: 0.34, fontFace: F, fontSize: 14, bold: true, color: C.red });
  s.addText('下一步', { x: 7.4, y: 2.18, w: 3, h: 0.34, fontFace: F, fontSize: 14, bold: true, color: C.deep });
  const pairs = [
    ['旧入口仍是单轮串联', '升级为独立首轮与多轮回源'],
    ['分歧后回原文闭环未实现', '最多三轮，无共识转人工裁决'],
    ['DIP 真实生产运行尚未跑', '用 frozen manifest 跑一次生产链'],
  ];
  pairs.forEach((p, i) => {
    const y = 2.62 + i * 0.92;
    s.addShape(pptx.ShapeType.roundRect, { x: 0.85, y, w: 5.4, h: 0.72, fill: { color: 'FBEDEB' }, line: { color: 'EEC4BE', width: 1 }, rectRadius: 0.08 });
    s.addText(String(i + 1).padStart(2, '0'), { x: 1.05, y, w: 0.6, h: 0.72, fontFace: 'Helvetica Neue', fontSize: 17, bold: true, color: C.red, valign: 'middle' });
    s.addText(p[0], { x: 1.72, y, w: 4.4, h: 0.72, fontFace: F, fontSize: 14, color: C.ink, valign: 'middle' });
    s.addShape(pptx.ShapeType.rect, { x: 6.42, y: y + 0.345, w: 0.85, h: 0.03, fill: { color: C.line }, line: { type: 'none' } });
    s.addShape(pptx.ShapeType.roundRect, { x: 7.4, y, w: 5.05, h: 0.72, fill: { color: C.wash }, line: { color: C.soft, width: 1 }, rectRadius: 0.08 });
    s.addText(p[1], { x: 7.62, y, w: 4.7, h: 0.72, fontFace: F, fontSize: 14, bold: true, color: C.deep, valign: 'middle' });
  });
  banner(s, '没做到的主动写清楚，比让别人从证据里问出来更可信。', H - 1.32);
}

pptx.writeFile({ fileName: OUT }).then(() => console.log('WROTE', OUT));
