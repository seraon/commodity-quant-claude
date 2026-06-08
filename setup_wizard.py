#!/usr/bin/env python3
"""Commodity Quant — Claude Code Compatible. Interactive setup wizard."""

import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    config_path = BASE / "config.yaml"
    template_path = BASE / "config_template.yaml"

    print("\nCommodity Quant — Claude Code Compatible v3.8")
    print("Configure your API endpoints.\n")

    if config_path.exists():
        if input("config.yaml exists. Overwrite? (y/n) [n]: ").strip().lower() != "y":
            print("Cancelled."); return

    cfg = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    for key in ["pigeon", "oilwell", "goldsmith", "seawatcher", "hawkeye"]:
        a = cfg["analysts"][key]
        print(f"\n── {a['name']} ({key}) ──")
        a["api_url"] = input(f"  API URL [{a.get('api_url','')}]: ").strip() or a.get("api_url", "")
        a["api_key"] = input(f"  API Key [{a.get('api_key','')[:4]}**** if set]: ").strip() or a.get("api_key", "")
        a["model"] = input(f"  Model [{a.get('model','')}]: ").strip() or a.get("model", "")

    config_path.write_text(yaml.dump(cfg, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    print(f"\nconfig.yaml saved.")


if __name__ == "__main__":
    main()
