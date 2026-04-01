#!/bin/bash
# TRIZ Agent セットアップスクリプト

echo "========================================"
echo "  TRIZ Innovation Agent セットアップ"
echo "========================================"

# anthropic パッケージのインストール
echo ""
echo "[1/3] anthropic パッケージをインストール中..."
pip install anthropic python-dotenv -q
echo "  ✅ 完了"

# .env ファイルの確認
echo ""
echo "[2/3] 環境変数の確認..."

ENV_FILE="$(dirname "$0")/.env"

if [ -f "$ENV_FILE" ]; then
    if grep -q "ANTHROPIC_API_KEY" "$ENV_FILE"; then
        echo "  ✅ .env に ANTHROPIC_API_KEY が見つかりました"
    else
        echo "  ⚠️  .env に ANTHROPIC_API_KEY がありません"
        echo ""
        echo "  .env に以下を追加してください:"
        echo "  ANTHROPIC_API_KEY=sk-ant-..."
    fi
elif [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ 環境変数 ANTHROPIC_API_KEY が設定されています"
else
    echo "  ⚠️  ANTHROPIC_API_KEY が見つかりません"
    echo ""
    echo "  以下のいずれかの方法で設定してください:"
    echo ""
    echo "  方法1: シェルに直接設定（一時的）"
    echo "    export ANTHROPIC_API_KEY='sk-ant-...'"
    echo ""
    echo "  方法2: .env ファイルに保存（推奨）"
    echo "    echo \"ANTHROPIC_API_KEY=sk-ant-...\" >> .env"
    echo ""
    echo "  APIキーは https://console.anthropic.com/ で取得できます"
fi

# 動作確認
echo ""
echo "[3/3] 動作確認..."
python -c "import anthropic; print('  ✅ anthropic', anthropic.__version__, 'が使用可能です')" 2>/dev/null || echo "  ❌ anthropic のインポートに失敗しました"

echo ""
echo "========================================"
echo "  セットアップ完了！"
echo ""
echo "  実行方法:"
echo "    python triz_agent.py"
echo "    python triz_agent.py --idea \"あなたのアイデア\""
echo "    python triz_agent.py --idea \"アイデア\" --top 3 --output results.json"
echo "========================================"
