# Commodity Quant Team v3.8.0 — Claude Code Compatible

**Multi-agent adversarial debate framework built for the Claude Code paradigm. System prompt + tool use loop, file-based state management, 6-phase pipeline.**

[English](#commodity-quant-team-v380--claude-code-compatible) | [中文](#量化大宗分析团队-v380--claude-code-兼容版)

---

## Framework Paradigm

This repo follows **Claude Code** conventions:

- **Agents as Markdown files** — each agent is a self-contained `.md` system prompt
- **Tool use via conversation loop** — agent invokes tools through the standard tool_use/tool_result cycle
- **File-based state** — all artifacts written to disk, enabling human-in-the-loop review
- **Subprocess orchestration** — orchestrator spawns agent processes that read/write files

## Pipeline

```
P0 📡 Collect  → pigeon agent reads neodata/LongCat APIs → snapshot.md
P1 🛢️🥇🌍 R1   → 3 analyst agents in parallel (blind) → *_R1.md
P2 🦅 Precheck → hawkeye scans R1 against snapshot → precheck.md
P3 🛢️🥇🌍 R2   → 3 analyst agents (cross-exam) → *_R2.md
P4 🦅 Verdict  → hawkeye synthesizes → verdict.md
P5 🦅 Verify   → hawkeye self-audit → verification.md
```

## Quick Start

```bash
pip install -r pipeline/requirements.txt
python pipeline/setup_wizard.py
python orchestrator.py --date 2026-06-08 --run r001
```

## Agents

| File | Agent | Role |
|------|-------|------|
| `agents/pigeon.md` | Pigeon | Data collector |
| `agents/oilwell.md` | Oilwell | WTI crude analyst |
| `agents/goldsmith.md` | Goldsmith | Gold analyst |
| `agents/seawatcher.md` | Seawatcher | Macro strategist |
| `agents/hawkeye.md` | Hawkeye | Lead arbitrator + Verifier |

## What's New v3.8

| Feature | Description |
|---------|-------------|
| **Chain Security Layer** | Hash chain + identity fingerprints |
| **Evidence Quality Scoring** | 0-10 per citation |
| **Automated Precheck** | precheck.py scans citations against snapshot |
| **Verifier** | Post-judgment compliance audit |
| **Hard-Stop** | P0 fabrication ≥2 → REJECTED |

---

# 量化大宗分析团队 v3.8.0 — Claude Code 兼容版

**多 Agent 对抗辩论框架，基于 Claude Code 范式。System prompt + tool use loop，文件系统状态管理。**

## 快速开始

```bash
pip install -r pipeline/requirements.txt
python pipeline/setup_wizard.py
python orchestrator.py --date 2026-06-08 --run r001
```

## Agent 文件

| 文件 | Agent | 角色 |
|------|-------|------|
| `agents/pigeon.md` | 信鸽 | 数据采集 |
| `agents/oilwell.md` | 油井 | WTI 原油分析师 |
| `agents/goldsmith.md` | 金匠 | 黄金分析师 |
| `agents/seawatcher.md` | 观澜 | 宏观策略师 |
| `agents/hawkeye.md` | 鹰眼 | 裁决+验证 |

其他版本：[OpenAI Agents 兼容版](https://github.com/seraon/commodity-quant-openai) | [WorkBuddy 专家版](https://github.com/seraon/commodity-quant)

---

**Source Available** — 代码公开供查看和参考，未经作者明确授权不得用于商业用途、修改或再分发。
