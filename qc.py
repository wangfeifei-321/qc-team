#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质检团队 · 全自动版
====================
一条命令，自动跑完:
  0. Crossref 真实核验文献 (不靠AI)
  1. 主审  = Claude Code  (claude 命令)
  2. 复核  = Codex        (codex 命令)
  3. 整理  = MiniMax      (API)
  → 输出完整质检报告

用法:
  python3 qc.py 稿件.txt

环境要求 (你的 Mac 已满足):
  - claude 命令可用
  - codex 命令可用
  - .env 里填了 MINIMAX_API_KEY
"""
import sys, os, subprocess, json, urllib.request, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROLES = os.path.join(HERE, 'roles')
REPORTS = os.path.join(HERE, 'reports')

# ---------- 读取 .env 里的密钥 (绝不写死在代码里) ----------
def load_env():
    env_path = os.path.join(HERE, '.env')
    cfg = {}
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    # 也允许从系统环境变量读
    for k in ['MINIMAX_API_KEY', 'MINIMAX_API_URL', 'MINIMAX_MODEL']:
        if k not in cfg and os.environ.get(k):
            cfg[k] = os.environ[k]
    return cfg

def read(path):
    return open(path, encoding='utf-8', errors='ignore').read()

# ---------- 第1步: 调 Claude Code 当主审 ----------
def call_claude(role, doc, refs_fact):
    prompt = f"{role}\n\n=== 文献核验结果(事实底座,以此为准) ===\n{refs_fact}\n\n=== 待质检稿件 ===\n{doc}\n\n请按你的角色输出主审意见。"
    print('  ▶ 主审(Claude Code)正在核查...(可能要一两分钟)')
    try:
        # claude -p 是非交互模式,直接给prompt拿输出
        r = subprocess.run(['claude', '-p', prompt],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return f'[主审调用出错] {r.stderr[:500]}'
        return r.stdout.strip()
    except FileNotFoundError:
        return '[错误] 找不到 claude 命令。请确认 Claude Code 已安装。'
    except subprocess.TimeoutExpired:
        return '[错误] 主审超时。稿件可能太长,可分段。'

# ---------- 第2步: 调 Codex 当复核 ----------
def call_codex(role, doc, refs_fact, lead_review):
    prompt = f"{role}\n\n=== 文献核验结果 ===\n{refs_fact}\n\n=== 稿件 ===\n{doc}\n\n=== 主审意见(你要挑它的错) ===\n{lead_review}\n\n请按你的角色输出独立复核意见。"
    print('  ▶ 复核(Codex)正在独立核验、挑主审的错...')
    try:
        # codex exec 是非交互执行模式
        r = subprocess.run(['codex', 'exec', prompt],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            # 有些版本用 codex -q 或直接 codex, 给出提示
            return f'[复核调用出错] {r.stderr[:500]}\n(若报错,可能是 codex 子命令不同,见 README 排错)'
        return r.stdout.strip()
    except FileNotFoundError:
        return '[错误] 找不到 codex 命令。'
    except subprocess.TimeoutExpired:
        return '[错误] 复核超时。'

# ---------- 第3步: 调 MiniMax API 当整理 ----------
def call_minimax(role, lead_review, cross_review, refs_fact, cfg):
    key = cfg.get('MINIMAX_API_KEY', '')
    url = cfg.get('MINIMAX_API_URL', 'https://api.minimaxi.com/v1/text/chatcompletion_v2')
    model = cfg.get('MINIMAX_MODEL', 'MiniMax-Text-01')
    if not key:
        return '[错误] .env 里没有 MINIMAX_API_KEY。请填入后重跑。'

    user_content = (f"{role}\n\n=== 文献核验结果 ===\n{refs_fact}\n\n"
                    f"=== 主审意见 ===\n{lead_review}\n\n"
                    f"=== 复核意见 ===\n{cross_review}\n\n"
                    f"请综合两方,按你的角色输出一份包含全部8个板块的完整质检报告。")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": user_content}],
    }
    print('  ▶ 整理(MiniMax)正在综合两方、推荐替代、出报告...')
    try:
        req = urllib.request.Request(url,
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json',
                     'Authorization': f'Bearer {key}'})
        resp = json.loads(urllib.request.urlopen(req, timeout=600).read())
        # MiniMax 返回结构: choices[0].message.content
        return resp['choices'][0]['message']['content']
    except Exception as e:
        return (f'[MiniMax API 调用出错] {e}\n'
                f'请核对 .env 里的 MINIMAX_API_URL 和 MINIMAX_MODEL 是否和你平台文档一致。\n'
                f'(不同国产平台接口地址/模型名不同)')

# ---------- 主流程 ----------
def main():
    if len(sys.argv) < 2:
        print('用法: python3 qc.py 稿件.txt'); sys.exit(1)
    docpath = sys.argv[1]
    if not os.path.exists(docpath):
        print(f'找不到文件: {docpath}'); sys.exit(1)

    cfg = load_env()
    name = os.path.splitext(os.path.basename(docpath))[0]
    stamp = time.strftime('%Y-%m-%d_%H%M%S')
    os.makedirs(REPORTS, exist_ok=True)

    print('='*50)
    print(f'  质检团队启动 · 稿件: {name}')
    print('='*50)

    # 第0步: 文献真实核验
    print('\n▶ 第0步: Crossref 真实核验文献...')
    subprocess.run(['python3', os.path.join(HERE, 'scripts', 'verify_refs.py'), docpath])
    refs_path = os.path.join(REPORTS, '_refs_verified.json')
    refs_fact = read(refs_path) if os.path.exists(refs_path) else '(无DOI或核验未产出)'

    doc = read(docpath)

    # 第1步: 主审
    print('\n▶ 第1步: 主审')
    lead = call_claude(read(os.path.join(ROLES, '01_主审_claude.md')), doc, refs_fact)
    open(os.path.join(REPORTS, f'{name}_1主审.md'), 'w', encoding='utf-8').write(lead)

    # 第2步: 复核
    print('\n▶ 第2步: 复核')
    cross = call_codex(read(os.path.join(ROLES, '02_复核_codex.md')), doc, refs_fact, lead)
    open(os.path.join(REPORTS, f'{name}_2复核.md'), 'w', encoding='utf-8').write(cross)

    # 第3步: 整理
    print('\n▶ 第3步: 整理')
    final = call_minimax(read(os.path.join(ROLES, '03_整理_minimax.md')), lead, cross, refs_fact, cfg)
    outpath = os.path.join(REPORTS, f'{name}_质检报告_{stamp}.md')
    open(outpath, 'w', encoding='utf-8').write(final)

    print('\n' + '='*50)
    print(f'  ✅ 完成! 最终报告:')
    print(f'  {outpath}')
    print('='*50)

if __name__ == '__main__':
    main()
