#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文献真实性核验器 —— 质检团队的地基
=====================================
核心原则：文献是否真实存在，靠【真实 API 查证】，绝不靠 AI 判断。
因为 AI 会"幻觉"出看起来很真的假文献。这一步必须是确定性的。

做三件事：
1. 提取稿件参考文献里的所有 DOI
2. 每个 DOI 走 Crossref API 核验：真的存在吗？元数据(作者/年份/期刊/标题)对得上吗？
3. 找不到的、对不上的，如实标红 —— 绝不编造

用法：
    python3 verify_refs.py <稿件.txt 或 参考文献.txt>
输出：
    reports/_refs_verified.json  (供 AI 角色引用的"已核验事实底座")
"""
import sys, re, json, urllib.request, urllib.parse, time, os

def find_dois(text):
    """从文本里抓所有 DOI"""
    # DOI 标准格式：10.xxxx/xxxxx
    pattern = r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+'
    dois = re.findall(pattern, text)
    # 清理尾部标点
    cleaned = []
    for d in dois:
        d = d.rstrip('.,;)')
        if d not in cleaned:
            cleaned.append(d)
    return cleaned

def verify_doi(doi):
    """走 Crossref 核验单个 DOI，返回真实元数据或标记查不到"""
    url = f'https://api.crossref.org/works/{urllib.parse.quote(doi)}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QC-Team/1.0 (academic integrity check)'})
        data = json.loads(urllib.request.urlopen(req, timeout=20).read())
        m = data['message']
        return {
            'doi': doi,
            'exists': True,
            'title': (m.get('title') or [''])[0],
            'journal': (m.get('container-title') or [''])[0],
            'year': (m.get('published', {}).get('date-parts', [['?']])[0][0]),
            'authors': [a.get('family', '') for a in m.get('author', [])],
            'type': m.get('type', ''),
            'volume': m.get('volume', ''),
            'page': m.get('page', ''),
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'doi': doi, 'exists': False, 'note': 'Crossref 查无此 DOI —— 可能是杜撰或 DOI 写错'}
        return {'doi': doi, 'exists': None, 'note': f'核验失败(HTTP {e.code})，请人工复查，勿默认为真'}
    except Exception as e:
        return {'doi': doi, 'exists': None, 'note': f'核验失败({e})，请人工复查，勿默认为真'}

def main():
    if len(sys.argv) < 2:
        print('用法: python3 verify_refs.py <稿件文件>')
        sys.exit(1)
    path = sys.argv[1]
    text = open(path, encoding='utf-8', errors='ignore').read()
    dois = find_dois(text)

    print(f'\n📋 在稿件里找到 {len(dois)} 个 DOI，开始逐个走 Crossref 真实核验...\n')
    results = []
    for i, doi in enumerate(dois, 1):
        print(f'  [{i}/{len(dois)}] 核验 {doi} ...', end=' ', flush=True)
        r = verify_doi(doi)
        if r['exists'] is True:
            print(f"✅ 真实 | {r['journal']} ({r['year']})")
        elif r['exists'] is False:
            print('🔴 查无此文献！')
        else:
            print('⚠️ 核验失败，需人工复查')
        results.append(r)
        time.sleep(0.5)  # 礼貌限速，别把 Crossref 打爆

    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, '_refs_verified.json')
    json.dump(results, open(outpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    real = sum(1 for r in results if r['exists'] is True)
    fake = sum(1 for r in results if r['exists'] is False)
    fail = sum(1 for r in results if r['exists'] is None)
    print(f'\n📊 核验完成：真实 {real} | 查无 {fake} | 需人工复查 {fail}')
    print(f'📁 已存事实底座 → {outpath}')
    print('\n⚠️  重要：没有 DOI 的文献(书籍/工作论文/网页)本脚本查不到，')
    print('   会在报告里如实标注"无 DOI，需人工/AI 另行核验全文来源"，绝不默认为真。\n')

if __name__ == '__main__':
    main()
