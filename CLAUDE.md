# TRIZ Innovation Agent — Claude Code 操作ガイド

## 構成

```
音声入力 (Aqua Voice)
    ↓
python triz_agent.py   ← TRIZ 40原理分析
    ↓
Notion MCP             ← 結果をNotionに保存
GitHub MCP             ← 結果をGitHubにコミット
```

## よく使うコマンド

### TRIZ 分析を実行する
```bash
# テキスト入力（Aqua Voice で話して入力）
python triz_agent.py --idea "アイデア" --top 5

# 結果をJSONで保存
python triz_agent.py --idea "アイデア" --output triz_results/result.json
```

### 音声入力 (Aqua Voice)
1. ターミナルで `python triz_agent.py` を起動
2. 「アイデアを入力 >」が表示されたら Aqua Voice を起動（⇧⇧）
3. アイデアを話す → 自動でテキスト入力される

## Notion MCP の使い方

TRIZ結果をNotionに保存するには、以下のように依頼してください：

```
「triz_results/triz_XXXXXX.json の内容を Notion に保存して」
「以下の分析結果を Notion の TRIZ データベースに新しいページとして追加して」
```

Notionページの構成例:
- タイトル: テーマ名（例：高齢者の孤独感を解消したい）
- 本文: ランキング・スコア・ネクストアクション

## GitHub MCP の使い方

結果をGitHubに保存するには：

```
「triz_results フォルダの内容を claude/focused-herschel ブランチにコミットして」
「TRIZ分析結果をコミットしてPRを作成して」
```

## ファイル構成

| ファイル | 役割 |
|---|---|
| `triz_agent.py` | TRIZ 40原理分析エンジン（メイン） |
| `triz_voice.py` | 音声録音 + Whisper API 文字起こし（Aqua Voice代替） |
| `triz_set_tokens.py` | Notion/GitHub トークン設定ツール |
| `triz_mcp_setup.sh` | 初回セットアップスクリプト |
| `triz_results/` | 分析結果の保存フォルダ |
| `~/.claude/settings.json` | MCP サーバー設定 |

## MCP トークンの設定・更新

```bash
python triz_set_tokens.py
```

## セットアップが終わっていない場合

```bash
bash triz_mcp_setup.sh
python triz_set_tokens.py
```
