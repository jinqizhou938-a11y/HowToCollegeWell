#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 book/*.md 的条目解析出来，生成自包含的单文件检索页 index.html。

用法：
    python build_index.py
输出：
    ../index.html（数据内嵌，双击即可打开，不需要服务器、不需要联网）
"""

import glob
import json
import os
import re
import html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOOK = os.path.join(ROOT, "book")
OUT = os.path.join(ROOT, "index.html")

FIELD_RE = re.compile(r"^-\s*(成本|说人话|收益|证据等级|来源|备注)[:：]\s*(.*)$")
TAG_RE = re.compile(
    r"<!--\s*成本标签:\s*钱=(\S+)\s*时间=(\S+)\s*毅力=(\S+)\s*收益=(\S+)\s*口径=(\S+?)\s*-->"
)


def parse_chapter(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    title = ""
    for ln in lines:
        m = re.match(r"^#\s+(.+)$", ln)
        if m:
            title = m.group(1).strip()
            break
    entries = []
    cur = None
    for ln in lines:
        m = re.match(r"^###\s+(\d+)\.\s*(.+)$", ln)
        if m:
            if cur:
                entries.append(cur)
            cur = {
                "n": int(m.group(1)),
                "title": m.group(2).strip(),
                "tag": None,
                "fields": {},
                "extra": [],
            }
            continue
        if cur is None:
            continue
        tm = TAG_RE.search(ln)
        if tm:
            cur["tag"] = {
                "money": tm.group(1),
                "time": tm.group(2),
                "will": tm.group(3),
                "gain": tm.group(4),
                "scope": tm.group(5),
            }
            continue
        fm = FIELD_RE.match(ln.strip())
        if fm:
            cur["fields"][fm.group(1)] = fm.group(2).strip()
            continue
        if ln.strip():
            cur["extra"].append(ln.strip())
    if cur:
        entries.append(cur)
    return title, entries


def main():
    chapters = []
    for path in sorted(glob.glob(os.path.join(BOOK, "*.md"))):
        title, entries = parse_chapter(path)
        if not entries:
            continue
        chapters.append(
            {
                "file": os.path.basename(path),
                "title": title,
                "entries": entries,
            }
        )

    total = sum(len(c["entries"]) for c in chapters)
    # 统计引用来源：来源字段里的可点击链接数（去重）
    urls = set()
    for c in chapters:
        for e in c["entries"]:
            for u in re.findall(r"https?://[^\s<>）)】]+", e["fields"].get("来源", "")):
                urls.add(u.rstrip("。，、；"))
    nsrc = len(urls)
    data = json.dumps(chapters, ensure_ascii=False)

    page = TEMPLATE.replace("__DATA__", data).replace("__TOTAL__", str(total))
    page = page.replace("__NCH__", str(len(chapters)))
    page = page.replace("__NSRC__", str(nsrc))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("chapters:", len(chapters), "entries:", total, "source links:", nsrc)
    print("written:", OUT)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>高性价比大学指南 · 在线检索</title>
<style>
:root{
  --bg:#f7f7f5; --panel:#ffffff; --line:#e3e3df; --ink:#1d1d1b; --ink2:#4b4b47;
  --muted:#8a8a83; --accent:#2f5d8a; --accent2:#3a7d55; --warn:#a8541f;
  --chip:#eef1f4; --shadow:0 1px 2px rgba(0,0,0,.05),0 6px 20px rgba(0,0,0,.04);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:26px 20px 20px}
.wrap{max-width:1080px;margin:0 auto}
h1{font-size:23px;margin:0 0 6px;letter-spacing:.5px}
.sub{color:var(--ink2);font-size:13.5px;margin-bottom:14px}
.stats{display:flex;gap:18px;flex-wrap:wrap;color:var(--muted);font-size:12.5px}
.stats b{color:var(--ink);font-weight:600}
main{max-width:1080px;margin:0 auto;padding:18px 20px 80px}
.controls{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;box-shadow:var(--shadow);margin-bottom:16px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.row:last-child{margin-bottom:0}
input[type=text],select{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--ink)}
input[type=text]{flex:1;min-width:200px}
label.chk{display:inline-flex;align-items:center;gap:5px;font-size:13px;color:var(--ink2);
  background:var(--chip);border:1px solid var(--line);border-radius:20px;padding:4px 11px;cursor:pointer;user-select:none}
label.chk input{margin:0}
label.chk.on{background:#e2ebf4;border-color:#b8cde0;color:var(--accent)}
.grp{font-size:12px;color:var(--muted);margin-right:2px}
#count{color:var(--muted);font-size:12.5px;margin:2px 0 12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:15px 17px;margin-bottom:11px;box-shadow:var(--shadow)}
.card h3{font-size:15.5px;margin:0 0 8px;line-height:1.5}
.card h3 .num{color:var(--muted);font-weight:400;margin-right:6px}
.card .plain{color:var(--ink);font-size:14px}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0 4px}
.tag{font-size:11.5px;padding:2px 8px;border-radius:20px;background:var(--chip);color:var(--ink2);border:1px solid var(--line)}
.tag.gA{background:#e4f0e6;border-color:#bfdcc5;color:var(--accent2)}
.tag.gB{background:#f3efe3;border-color:#e0d7bd;color:#8a6a1f}
.tag.gC{background:#f0eeee;border-color:#ded8d8;color:#7a6a6a}
.tag.gx{background:#e6eef5;border-color:#c3d5e4;color:var(--accent)}
.tag.warn{background:#f7e9de;border-color:#e8cbb4;color:var(--warn)}
.cost{display:grid;grid-template-columns:56px 1fr;gap:4px 10px;font-size:13.5px;margin-top:9px}
.cost dt{color:var(--muted);text-align:right}
.cost dd{margin:0;color:var(--ink2);word-break:break-word}
.cost dd a{word-break:break-all}
details{margin-top:8px}
summary{cursor:pointer;font-size:12.5px;color:var(--accent);list-style:none;display:inline-block;padding:2px 0}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ "}
details[open] summary::before{content:"▾ "}
.ch{font-size:11.5px;color:var(--muted);margin-bottom:7px}
.empty{color:var(--muted);padding:30px;text-align:center}
footer{color:var(--muted);font-size:12.5px;text-align:center;padding:0 20px 50px}
@media(max-width:600px){ .cost{grid-template-columns:1fr } .cost dt{text-align:left} }
</style>
</head>
<body>
<header><div class="wrap">
  <h1>高性价比大学指南 · 在线检索</h1>
  <div class="sub">用最少的钱、时间和精力，换回最多的成绩、能力、钱和选择权。</div>
  <div class="stats">
    <span>条目 <b>__TOTAL__</b> 条</span>
    <span>章节 <b>__NCH__</b> 节</span>
    <span>引用来源 <b>__NSRC__</b> 个官方链接</span>
    <span>数据来自 <code>book/*.md</code>，与正文同步</span>
  </div>
</div></header>

<main>
  <div class="controls">
    <div class="row">
      <input type="text" id="q" placeholder="搜索关键词：绩点、保研、助学贷款、刷单、体测、档案、试用期、AED、帮信罪、12356……">
      <select id="ch"><option value="">全部章节</option></select>
    </div>
    <div class="row">
      <span class="grp">证据等级</span>
      <label class="chk"><input type="checkbox" class="g" value="A">A 有原文（法条／文号／文献）</label>
      <label class="chk"><input type="checkbox" class="g" value="B">B 有官方依据</label>
      <label class="chk"><input type="checkbox" class="g" value="C">C 通行做法</label>
    </div>
    <div class="row">
      <span class="grp">换回什么</span>
      <label class="chk"><input type="checkbox" class="s" value="成绩">成绩</label>
      <label class="chk"><input type="checkbox" class="s" value="时间精力">时间精力</label>
      <label class="chk"><input type="checkbox" class="s" value="金钱">金钱</label>
      <label class="chk"><input type="checkbox" class="s" value="选择权">选择权</label>
    </div>
    <div class="row">
      <span class="grp">成本</span>
      <label class="chk"><input type="checkbox" id="free">不花钱</label>
      <label class="chk"><input type="checkbox" id="quick">不花时间</label>
      <label class="chk"><input type="checkbox" id="easy">不需要毅力</label>
      <label class="chk"><input type="checkbox" id="big">收益大</label>
      <span class="grp" style="margin-left:6px">排序</span>
      <select id="sort">
        <option value="cost">按性价比</option>
        <option value="book">按章节顺序</option>
        <option value="gain">按收益量级</option>
      </select>
    </div>
  </div>
  <div id="count"></div>
  <div id="list"></div>
</main>

<footer>《高性价比大学指南》· 条目化、可筛选 · 正文在 book/ 目录，法律条文、部委文件与文献的来源链接都在每条里 · 重新运行 tools/build_index.py 即可更新本页</footer>

<script>
const DATA = __DATA__;

function tier(e){
  const t = e.tag || {};
  const costZero = t.money === '0' && t.time === '少' && t.will === '否';
  if (t.gain === '大' && costZero) return '极高';
  if ((t.gain === '大' && (t.money === '0' || t.money === '低') && (t.time === '少' || t.time === '中'))
      || (t.gain === '中' && costZero)) return '高';
  return '一般';
}
const GAIN_RANK = {'大':3,'中':2,'小':1};
const TIER_RANK = {'极高':3,'高':2,'一般':1};

const flat = [];
DATA.forEach((c, ci) => c.entries.forEach((e, ei) => {
  flat.push(Object.assign({}, e, {ci, ei, ch: c.title, file: c.file, tier: tier(e)}));
}));

const chSel = document.getElementById('ch');
DATA.forEach((c, i) => {
  const o = document.createElement('option');
  o.value = i; o.textContent = c.title;
  chSel.appendChild(o);
});

const esc = s => (s || '').replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
function linkify(s){
  s = esc(s);
  return s.replace(/(https?:\/\/[^\s<>）)]+)/g, u => '<a href="' + u + '" target="_blank" rel="noopener">' + u + '</a>');
}
function tagHtml(e){
  const t = e.tag || {};
  const parts = [];
  if (e.tier) parts.push('<span class="tag gx">性价比 ' + e.tier + '</span>');
  parts.push('<span class="tag g' + (e.fields['证据等级'] || 'C') + '">证据 ' + (e.fields['证据等级'] || '?') + '</span>');
  if (t.scope) parts.push('<span class="tag">换回 ' + t.scope + '</span>');
  if (t.gain) parts.push('<span class="tag">收益 ' + t.gain + '</span>');
  const cost = [];
  if (t.money) cost.push('钱:' + t.money);
  if (t.time) cost.push('时间:' + t.time);
  if (t.will) cost.push('毅力:' + t.will);
  if (cost.length) parts.push('<span class="tag">' + cost.join(' · ') + '</span>');
  const warn = /争议|地区差异|各校差异/.test(e.fields['备注'] || '');
  if (warn) parts.push('<span class="tag warn">看备注</span>');
  return '<div class="tags">' + parts.join('') + '</div>';
}
function card(e){
  const f = e.fields || {};
  const rows = ['成本','收益','来源','备注'].filter(k => f[k])
    .map(k => '<dt>' + k + '</dt><dd>' + linkify(f[k]) + '</dd>').join('');
  const plain = f['说人话'] ? '<div class="plain">' + linkify(f['说人话']) + '</div>' : '';
  const extra = (e.extra && e.extra.length) ? '<div class="plain" style="color:var(--ink2);font-size:13px">' + e.extra.map(linkify).join('<br>') + '</div>' : '';
  return '<div class="card"><div class="ch">' + esc(e.ch) + '</div>'
    + '<h3><span class="num">' + e.n + '.</span>' + esc(e.title) + '</h3>'
    + plain + tagHtml(e)
    + '<details><summary>展开：成本 / 收益 / 来源 / 备注</summary><dl class="cost">' + rows + '</dl></details>'
    + extra + '</div>';
}

function apply(){
  const q = document.getElementById('q').value.trim().toLowerCase();
  const chv = chSel.value;
  const gs = [...document.querySelectorAll('.g:checked')].map(x => x.value);
  const ss = [...document.querySelectorAll('.s:checked')].map(x => x.value);
  const free = document.getElementById('free').checked;
  const quick = document.getElementById('quick').checked;
  const easy = document.getElementById('easy').checked;
  const big = document.getElementById('big').checked;
  const sort = document.getElementById('sort').value;

  document.querySelectorAll('label.chk').forEach(l => {
    const i = l.querySelector('input');
    l.classList.toggle('on', i && i.checked);
  });

  let out = flat.filter(e => {
    const t = e.tag || {}; const f = e.fields || {};
    if (chv !== '' && String(e.ci) !== chv) return false;
    if (gs.length && !gs.includes(f['证据等级'])) return false;
    if (ss.length && !ss.includes(t.scope)) return false;
    if (free && t.money !== '0') return false;
    if (quick && t.time !== '少') return false;
    if (easy && t.will !== '否') return false;
    if (big && t.gain !== '大') return false;
    if (q){
      const hay = [e.title, e.ch, f['说人话'], f['收益'], f['备注'], f['来源'], t.scope, t.gain].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  if (sort === 'cost') out.sort((a,b) => (TIER_RANK[b.tier]-TIER_RANK[a.tier]) || (GAIN_RANK[b.tag?.gain||''] - GAIN_RANK[a.tag?.gain||'']) || a.ci - b.ci || a.n - b.n);
  else if (sort === 'book') out.sort((a,b) => a.ci - b.ci || a.n - b.n);
  else out.sort((a,b) => (GAIN_RANK[b.tag?.gain||''] - GAIN_RANK[a.tag?.gain||'']) || a.ci - b.ci || a.n - b.n);

  document.getElementById('count').textContent = '共 ' + out.length + ' 条' + (out.length !== flat.length ? '（全库 ' + flat.length + ' 条）' : '');
  document.getElementById('list').innerHTML = out.length ? out.map(card).join('') : '<div class="empty">没有匹配的条目，换个关键词或清掉筛选条件。</div>';
}

document.getElementById('q').addEventListener('input', apply);
chSel.addEventListener('change', apply);
document.getElementById('sort').addEventListener('change', apply);
document.querySelectorAll('.g,.s,#free,#quick,#easy,#big').forEach(x => x.addEventListener('change', apply));
apply();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
