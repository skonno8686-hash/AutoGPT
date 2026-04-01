#!/usr/bin/env python3
"""
MCP トークン設定ツール
~/.claude/settings.json の Notion / GitHub トークンを対話形式で設定する
"""

import json
import subprocess
import sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def open_url(url: str):
    subprocess.run(["open", url], check=False)


def update_settings(notion_token: str = None, github_token: str = None):
    with open(SETTINGS_PATH) as f:
        settings = json.load(f)

    if notion_token:
        headers = json.dumps({
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28"
        })
        settings["mcpServers"]["notion"]["env"]["OPENAPI_MCP_HEADERS"] = headers

    if github_token:
        settings["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token

    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 保存しました: {SETTINGS_PATH}")


def check_current():
    with open(SETTINGS_PATH) as f:
        settings = json.load(f)
    notion_ok = "YOUR_NOTION_TOKEN" not in settings["mcpServers"]["notion"]["env"].get("OPENAPI_MCP_HEADERS", "")
    github_ok = "YOUR_GITHUB_TOKEN" not in settings["mcpServers"]["github"]["env"].get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    return notion_ok, github_ok


def main():
    print()
    print("═" * 55)
    print("  MCP トークン設定ツール")
    print("═" * 55)

    notion_ok, github_ok = check_current()
    print(f"  Notion MCP : {'✅ 設定済み' if notion_ok else '❌ 未設定'}")
    print(f"  GitHub MCP : {'✅ 設定済み' if github_ok else '❌ 未設定'}")
    print()

    if notion_ok and github_ok:
        print("  すべてのトークンが設定済みです！")
        print("  Claude Code を再起動すると MCP が有効になります。")
        return

    # ── Notion ──────────────────────────────────────
    if not notion_ok:
        print("  ── Notion インテグレーショントークンの取得 ──")
        print("  ブラウザで Notion インテグレーション作成ページを開きます...")
        open_url("https://www.notion.so/my-integrations")
        print()
        print("  手順:")
        print("   1. 「新しいインテグレーション」をクリック")
        print("   2. 名前: TRIZ Agent など")
        print("   3. 「送信」→ 表示された secret_xxx... をコピー")
        print()
        token = input("  Notion トークンを貼り付けてください: ").strip()
        if token and token != "YOUR_NOTION_TOKEN":
            update_settings(notion_token=token)
        else:
            print("  ⚠️  スキップしました")
        print()

    # ── GitHub ──────────────────────────────────────
    if not github_ok:
        print("  ── GitHub Personal Access Token の取得 ──")
        print("  ブラウザで GitHub トークン作成ページを開きます...")
        open_url("https://github.com/settings/tokens/new?description=TRIZ-MCP&scopes=repo,issues,pull_requests")
        print()
        print("  手順:")
        print("   1. Expiration を設定（90日推奨）")
        print("   2. 「Generate token」をクリック")
        print("   3. 表示された ghp_xxx... をコピー")
        print()
        token = input("  GitHub トークンを貼り付けてください: ").strip()
        if token and token != "YOUR_GITHUB_TOKEN":
            update_settings(github_token=token)
        else:
            print("  ⚠️  スキップしました")
        print()

    # ── 完了 ────────────────────────────────────────
    notion_ok, github_ok = check_current()
    print("═" * 55)
    print("  設定結果:")
    print(f"  Notion MCP : {'✅ 設定済み' if notion_ok else '❌ 未設定'}")
    print(f"  GitHub MCP : {'✅ 設定済み' if github_ok else '❌ 未設定'}")
    if notion_ok or github_ok:
        print()
        print("  ✅ Claude Code を再起動してください。")
        print("     MCPサーバーが自動で起動します。")
    print("═" * 55)


if __name__ == "__main__":
    main()
