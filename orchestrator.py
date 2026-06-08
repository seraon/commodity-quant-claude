#!/usr/bin/env python3
"""
Commodity Quant Pipeline — Claude Code Compatible v3.8.0

Claude Code convention: agents are markdown system prompts loaded at runtime.
Tool use is implicit in the conversation loop. All state lives in files.

Usage:
  python orchestrator.py --date 2026-06-08 --run r001
"""

import argparse, hashlib, subprocess, sys, yaml, requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
PIPELINE = BASE / "pipeline"
ARTIFACTS = PIPELINE / "artifacts"
AGENTS_DIR = BASE / "agents"

PHASES = ["P0", "P1", "P2", "P3", "P4", "P5"]
ANALYST_NAMES = {"oilwell": "油井", "goldsmith": "金匠", "seawatcher": "观澜"}


def load_config():
    p = BASE / "config.yaml"
    if not p.exists():
        print("ERROR: config.yaml not found. Run: python pipeline/setup_wizard.py")
        sys.exit(1)
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def run_agent(agent_name: str, system_path: str, user_prompt: str, cfg: dict,
              seq: int = 0, prev_hash: str = "genesis") -> tuple[str, str]:
    """Call an agent via OpenAI-compatible API with a markdown system prompt.
    Claude Code pattern: system prompt loaded from file, conversation loop.
    Returns (content, content_hash).
    """
    ac = cfg.get("analysts", {}).get(agent_name, {})
    if not ac.get("api_key"):
        print(f"[SKIP] {agent_name}: no API key")
        return "", ""

    system = Path(system_path).read_text(encoding="utf-8")
    r = requests.post(
        ac["api_url"],
        headers={"Authorization": f"Bearer {ac['api_key']}", "Content-Type": "application/json"},
        json={
            "model": ac.get("model", "deepseek-v4-pro"),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": ac.get("max_tokens", 4000),
            "temperature": 0.7,
        },
        timeout=ac.get("timeout_seconds", 120),
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]

    # Chain security
    agent_id = f"{agent_name}-agent"
    fingerprint = hashlib.sha256(system.encode()).hexdigest()[:8]
    payload = f"{prev_hash}|{agent_id}|{seq}|{content}"
    content_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]

    chain_header = f"""---
chain:
  seq: {seq}
  agent_id: "{agent_id}"
  prev_hash: "{prev_hash}"
  hash: "{content_hash}"
agent:
  role: "{agent_id}"
  fingerprint: "{fingerprint}"
---

"""
    return chain_header + content, content_hash


def phase_0(cfg, date, run_id):
    """P0: Pigeon collects."""
    prompt = f"Collect all commodity data for {date}. Write to pipeline/artifacts/{date}_{run_id}_snapshot.md"
    c, _ = run_agent("pigeon", str(AGENTS_DIR / "pigeon.md"), prompt, cfg)
    if not c:
        return None
    out = ARTIFACTS / f"{date}_{run_id}_snapshot.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(c, encoding="utf-8")
    return str(out)


def phase_1(cfg, date, run_id, snapshot):
    """P1: 3 analysts in parallel."""
    snap = Path(snapshot).read_text(encoding="utf-8")
    results = {}

    def run(name, label):
        out = ARTIFACTS / f"{date}_{run_id}_{name}_R1.md"
        prompt = f"## Data Snapshot\n{snap}\n\nWrite your R1 analysis for {date}. Annotate every number with [source: XX]."
        c, ch = run_agent(name, str(AGENTS_DIR / f"{name}.md"), prompt, cfg, seq=1)
        if c:
            out.write_text(c, encoding="utf-8")
            return name, str(out), ch
        return name, None, ""

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(run, n, l) for n, l in ANALYST_NAMES.items()]
        for f in futures:
            n, p, ch = f.result()
            if p:
                results[n] = p
                results[f"{n}_hash"] = ch
    return results


def phase_2(cfg, date, run_id, snapshot, r1):
    """P2: Hawkeye precheck."""
    snap = Path(snapshot).read_text(encoding="utf-8")
    parts = [f"Precheck all R1 reports against this snapshot.\n\n## Snapshot\n{snap[:4000]}"]
    for n, l in ANALYST_NAMES.items():
        if n in r1:
            parts.append(f"## {l} R1\n{Path(r1[n]).read_text(encoding='utf-8')[:2000]}")
    prompt = "\n\n".join(parts)
    prompt += f"\n\nScan every number. Mark [!match]/[!drift]/[!unsourced]. Score evidence quality 0-10. Write to pipeline/artifacts/{date}_{run_id}_precheck.md"
    c, _ = run_agent("hawkeye", str(AGENTS_DIR / "hawkeye.md"), prompt, cfg, seq=2)
    out = ARTIFACTS / f"{date}_{run_id}_precheck.md"
    out.write_text(c, encoding="utf-8")
    return str(out) if c else None


def phase_3(cfg, date, run_id, precheck, r1):
    """P3: Cross-exam."""
    pc = Path(precheck).read_text(encoding="utf-8") if precheck else ""
    results = {}
    for name, peers in [("oilwell", ["goldsmith", "seawatcher"]),
                         ("goldsmith", ["oilwell", "seawatcher"]),
                         ("seawatcher", ["oilwell", "goldsmith"])]:
        parts = [f"## Precheck\n{pc[:3000]}"]
        for pn in peers:
            if pn in r1:
                parts.append(f"## {ANALYST_NAMES[pn]} R1\n{Path(r1[pn]).read_text(encoding='utf-8')[:2000]}")
        prompt = "\n\n".join(parts)
        prompt += f"\n\nRespond to each precheck flag. Address peer claims. Write R2 to pipeline/artifacts/{date}_{run_id}_{name}_R2.md"
        c, _ = run_agent(name, str(AGENTS_DIR / f"{name}.md"), prompt, cfg, seq=3,
                          prev_hash=r1.get(f"{name}_hash", "genesis"))
        if c:
            out = ARTIFACTS / f"{date}_{run_id}_{name}_R2.md"
            out.write_text(c, encoding="utf-8")
            results[name] = str(out)
    return results


def phase_4(cfg, date, run_id, snapshot, r1, r2):
    """P4: Hawkeye verdict."""
    snap = Path(snapshot).read_text(encoding="utf-8")[:4000]
    parts = [f"Deliver final verdict for {date}.\n\n## Snapshot\n{snap}"]
    for ph, data in [("R1", r1), ("R2", r2)]:
        for n, l in ANALYST_NAMES.items():
            if n in data:
                parts.append(f"## {l} {ph}\n{Path(data[n]).read_text(encoding='utf-8')[:2000]}")
    prompt = "\n\n".join(parts[-6:])
    prompt += f"\n\nWrite verdict to pipeline/artifacts/{date}_{run_id}_verdict.md"
    c, _ = run_agent("hawkeye", str(AGENTS_DIR / "hawkeye.md"), prompt, cfg, seq=4)
    out = ARTIFACTS / f"{date}_{run_id}_verdict.md"
    out.write_text(c, encoding="utf-8")
    return str(out) if c else None


def phase_5(cfg, date, run_id, snapshot, verdict):
    """P5: Verifier."""
    snap = Path(snapshot).read_text(encoding="utf-8")[:4000]
    v = Path(verdict).read_text(encoding="utf-8")[:3000]
    prompt = f"Verify your verdict against the snapshot.\n\n## Snapshot\n{snap}\n\n## Verdict\n{v}\n\nMark every number. Hard-stop: P0 ≥2 → [!REJECTED]. Write to pipeline/artifacts/{date}_{run_id}_verification.md"
    c, _ = run_agent("hawkeye", str(AGENTS_DIR / "hawkeye.md"), prompt, cfg, seq=5)
    out = ARTIFACTS / f"{date}_{run_id}_verification.md"
    out.write_text(c, encoding="utf-8")
    return str(out) if c else None


def main():
    p = argparse.ArgumentParser(description="Commodity Quant — Claude Code Compatible v3.8")
    p.add_argument("--date", required=True)
    p.add_argument("--run", default="r001")
    args = p.parse_args()

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()

    print(f"\nCommodity Quant v3.8 (Claude Code)\n  {args.date}/{args.run}\n")
    print("  Agents loaded from agents/*.md\n")

    snap = phase_0(cfg, args.date, args.run)
    if not snap:
        print("[FATAL] P0"); sys.exit(1)
    r1 = phase_1(cfg, args.date, args.run, snap)
    if len(r1) < 6:
        print("[FATAL] P1"); sys.exit(1)
    pc = phase_2(cfg, args.date, args.run, snap, r1)
    r2 = phase_3(cfg, args.date, args.run, pc, r1)
    v = phase_4(cfg, args.date, args.run, snap, r1, r2)
    vf = phase_5(cfg, args.date, args.run, snap, v)
    print(f"\nDone — {ARTIFACTS}\n  snapshot: {snap}\n  precheck: {pc}\n  verdict:  {v}\n  verify:   {vf}")


if __name__ == "__main__":
    main()
