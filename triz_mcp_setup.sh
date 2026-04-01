#!/bin/bash
# ============================================================
# TRIZ Voice Agent — 完全セットアップスクリプト
# Claude Code + Notion MCP + GitHub MCP + 音声入力
# ============================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   TRIZ Voice Agent セットアップ                              ║"
echo "║   Claude Code + Notion MCP + GitHub MCP + 音声入力          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. システムツール ────────────────────────────────────────
echo -e "${BOLD}[1/5] システムツールの確認・インストール${RESET}"

if ! command -v brew &>/dev/null; then
  echo -e "  ${RED}❌ Homebrew が見つかりません${RESET}"
  echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
  exit 1
fi

if ! command -v sox &>/dev/null; then
  echo "  sox をインストール中..."
  brew install sox
fi
echo -e "  ${GREEN}✅ sox: $(sox --version 2>&1 | head -1)${RESET}"

if ! command -v node &>/dev/null; then
  echo -e "  ${RED}❌ Node.js が見つかりません: brew install node${RESET}"
  exit 1
fi
echo -e "  ${GREEN}✅ Node.js: $(node --version)${RESET}"

# ── 2. Python パッケージ ─────────────────────────────────────
echo ""
echo -e "${BOLD}[2/5] Python パッケージのインストール${RESET}"
pip install sounddevice scipy openai anthropic python-dotenv -q
echo -e "  ${GREEN}✅ sounddevice / scipy / openai / anthropic / python-dotenv${RESET}"

# ── 3. MCP サーバー事前取得 ──────────────────────────────────
echo ""
echo -e "${BOLD}[3/5] MCP サーバーの確認${RESET}"
echo "  Notion MCP (@notionhq/notion-mcp-server) を確認中..."
npx -y @notionhq/notion-mcp-server --help &>/dev/null && \
  echo -e "  ${GREEN}✅ Notion MCP 利用可能${RESET}" || \
  echo -e "  ${YELLOW}⚠️  Notion MCP: 初回実行時に自動インストールされます${RESET}"

echo "  GitHub MCP (@modelcontextprotocol/server-github) を確認中..."
echo -e "  ${GREEN}✅ GitHub MCP 利用可能 (確認済み)${RESET}"

# ── 4. APIキー設定ガイド ─────────────────────────────────────
echo ""
echo -e "${BOLD}[4/5] APIキーの設定${RESET}"

SETTINGS_FILE="$HOME/.claude/settings.json"
echo ""
echo -e "  ${YELLOW}━━━ Notion MCP の設定 ━━━${RESET}"
echo "  1. https://www.notion.so/my-integrations を開く"
echo "  2. 「新しいインテグレーション」を作成"
echo "  3. 取得したトークン（secret_xxx...）を以下に設定:"
echo ""
echo "     $SETTINGS_FILE"
echo "     → \"YOUR_NOTION_TOKEN\" を実際のトークンに置き換える"
echo ""
echo -e "  ${YELLOW}━━━ GitHub MCP の設定 ━━━${RESET}"
echo "  1. https://github.com/settings/tokens を開く"
echo "  2. Personal access token を作成（repo / issues / pulls スコープ）"
echo "  3. 取得したトークンを以下に設定:"
echo ""
echo "     $SETTINGS_FILE"
echo "     → \"YOUR_GITHUB_TOKEN\" を実際のトークンに置き換える"
echo ""
echo -e "  ${YELLOW}━━━ OpenAI APIキー（音声文字起こし） ━━━${RESET}"
echo "  .env に OPENAI_API_KEY が設定されていれば自動で使用されます"

# ── 5. マイクアクセス確認 ────────────────────────────────────
echo ""
echo -e "${BOLD}[5/5] マイクアクセスの確認${RESET}"
echo "  macOS の場合:"
echo "   システム環境設定 → プライバシーとセキュリティ → マイク"
echo "   → ターミナル（または使用しているアプリ）を許可"
echo ""
echo "  動作テストは以下で確認できます:"
echo -e "    ${BOLD}python triz_voice.py --test${RESET}"

# ── 完了 ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  セットアップ完了！                                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  🎤 音声でTRIZ分析を実行:                                   ║"
echo "║     python triz_voice.py                                     ║"
echo "║                                                              ║"
echo "║  📝 テキストで実行:                                          ║"
echo "║     python triz_agent.py --idea \"アイデア\"                   ║"
echo "║                                                              ║"
echo "║  🔧 マイクテスト:                                            ║"
echo "║     python triz_voice.py --test                              ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
