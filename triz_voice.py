#!/usr/bin/env python3
"""
TRIZ Voice Agent
================
🎤 音声入力 → 📝 文字起こし (Whisper) → 🔧 TRIZ 40原理分析 → 💾 結果保存

Usage:
    python triz_voice.py              # 音声入力モード
    python triz_voice.py --test       # マイクテスト
    python triz_voice.py --top 5      # 上位5件表示
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

# .env 自動読み込み
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

# ─────────────────────────────────────────────
# 依存チェック
# ─────────────────────────────────────────────
def check_deps():
    missing = []
    try:
        import sounddevice
    except ImportError:
        missing.append("sounddevice  →  pip install sounddevice scipy")
    try:
        import scipy
    except ImportError:
        missing.append("scipy  →  pip install scipy")
    if missing:
        print("❌ 不足しているパッケージ:")
        for m in missing:
            print(f"   {m}")
        sys.exit(1)


# ─────────────────────────────────────────────
# 音声録音
# ─────────────────────────────────────────────
def record_voice(samplerate: int = 16000) -> str:
    """
    マイクから録音して一時WAVファイルのパスを返す。
    Enter キーで録音を停止する。
    """
    import sounddevice as sd
    import numpy as np
    import scipy.io.wavfile as wav

    print()
    print("  ┌──────────────────────────────────────────┐")
    print("  │  🎤 録音中... アイデアを話してください   │")
    print("  │     話し終わったら Enter を押してください  │")
    print("  └──────────────────────────────────────────┘")
    print()

    frames = []

    def callback(indata, f, t, status):
        frames.append(indata.copy())

    stream = sd.InputStream(samplerate=samplerate, channels=1, dtype="int16", callback=callback)
    stream.start()
    input("  (録音中)  ")
    stream.stop()
    stream.close()

    if not frames:
        print("❌ 音声が録音されませんでした。")
        sys.exit(1)

    import numpy as np
    audio = np.concatenate(frames, axis=0)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav.write(tmp.name, samplerate, audio)
    print(f"  ✅ 録音完了 ({len(audio)/samplerate:.1f} 秒)")
    return tmp.name


# ─────────────────────────────────────────────
# Whisper API 文字起こし
# ─────────────────────────────────────────────
def transcribe_whisper(audio_path: str) -> str:
    """OpenAI Whisper API で音声→テキスト変換"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY が設定されていません。")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("❌ openai パッケージが必要です: pip install openai")
        sys.exit(1)

    print("  🔄 Whisper API で文字起こし中...")
    client = OpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ja",
        )
    text = result.text.strip()
    print(f"  ✅ 認識結果: 「{text}」")
    return text


# ─────────────────────────────────────────────
# TRIZ エージェント実行
# ─────────────────────────────────────────────
def run_triz(idea: str, top: int = 5, output_path: str = None) -> dict:
    """triz_agent.py の run_triz_agent を呼び出す"""
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

    try:
        from triz_agent import run_triz_agent
    except ImportError:
        print("❌ triz_agent.py が見つかりません。同じディレクトリに配置してください。")
        sys.exit(1)

    evaluation, all_ideas = run_triz_agent(
        idea=idea,
        top_n=top,
        lang="ja",
        output_file=output_path,
    )
    return {"evaluation": evaluation, "all_ideas": all_ideas}


# ─────────────────────────────────────────────
# Notion 保存用マークダウン生成
# ─────────────────────────────────────────────
def build_notion_markdown(idea: str, evaluation: dict) -> str:
    """Notion に貼り付けられる形式のマークダウンを生成する"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# TRIZ分析レポート",
        f"",
        f"**テーマ**: {idea}",
        f"**実行日時**: {now}",
        f"",
        f"---",
        f"",
    ]
    for item in evaluation.get("top_ideas", []):
        scores = item.get("scores", {})
        total = item.get("total_score", 0)
        rank = item.get("rank", "?")
        lines += [
            f"## 第{rank}位 — {item.get('principle_name', '')}（{total}/50点）",
            f"",
            f"**アイデア**: {item.get('idea', '')}",
            f"",
            f"**対象市場**: {item.get('target_market', '')}",
            f"",
            f"| 評価軸 | スコア |",
            f"|---|:---:|",
            f"| 市場規模・成長性 | {scores.get('market_size', 0)}/10 |",
            f"| 実現容易性 | {scores.get('feasibility', 0)}/10 |",
            f"| 収益モデル | {scores.get('revenue_model', 0)}/10 |",
            f"| 競合優位性 | {scores.get('competitive_advantage', 0)}/10 |",
            f"| イノベーション度 | {scores.get('innovation', 0)}/10 |",
            f"",
            f"**有望な理由**: {item.get('why_promising', '')}",
            f"",
            f"**主要リスク**: {item.get('key_risks', '')}",
            f"",
            f"**ネクストアクション**:",
        ]
        steps = item.get("next_steps", "")
        if isinstance(steps, list):
            for s in steps:
                lines.append(f"- {s}")
        else:
            for s in str(steps).split("\n"):
                if s.strip():
                    lines.append(f"- {s.strip()}")
        lines.append("")

    summary = evaluation.get("summary", "")
    if summary:
        lines += ["---", "", "## 総合考察", "", summary, ""]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# マイクテスト
# ─────────────────────────────────────────────
def test_microphone():
    import sounddevice as sd
    print("\n  🎤 マイクテスト（3秒間録音します）...")
    try:
        devices = sd.query_devices()
        default_input = sd.query_devices(kind="input")
        print(f"  デフォルト入力デバイス: {default_input['name']}")
        recording = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype="int16")
        sd.wait()
        max_vol = abs(recording).max()
        if max_vol > 100:
            print(f"  ✅ マイク正常（最大音量: {max_vol}）")
        else:
            print(f"  ⚠️  音量が非常に小さいです（{max_vol}）。マイクの設定を確認してください。")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        print("  システム環境設定 → プライバシーとセキュリティ → マイク でアクセスを許可してください。")


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="🎤 音声でアイデアを入力してTRIZ分析を実行するエージェント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python triz_voice.py              # 音声入力してTRIZ分析
  python triz_voice.py --test       # マイク動作テスト
  python triz_voice.py --top 3      # 上位3件のみ表示
  python triz_voice.py --output results/  # 指定フォルダに保存
        """,
    )
    parser.add_argument("--test", action="store_true", help="マイク動作テスト")
    parser.add_argument("--top", "-t", type=int, default=5, help="上位件数（デフォルト: 5）")
    parser.add_argument("--output", "-o", type=str, default=None, help="結果保存フォルダ")
    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        TRIZ Voice Agent — 音声 × 発明 × ビジネス評価        ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    check_deps()

    if args.test:
        test_microphone()
        return

    # ── 音声録音 ──────────────────────────────
    audio_path = record_voice()

    # ── 文字起こし ─────────────────────────────
    idea = transcribe_whisper(audio_path)
    os.unlink(audio_path)  # 一時ファイル削除

    if not idea:
        print("❌ 音声を認識できませんでした。もう一度お試しください。")
        sys.exit(1)

    # ── TRIZ 分析 ──────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output) if args.output else Path(__file__).parent / "triz_results"
    output_dir.mkdir(exist_ok=True)

    json_path = str(output_dir / f"triz_{timestamp}.json")
    md_path = str(output_dir / f"triz_{timestamp}.md")

    result = run_triz(idea=idea, top=args.top, output_path=json_path)

    # ── マークダウン生成 ────────────────────────
    md_content = build_notion_markdown(idea, result["evaluation"])
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # ── 完了メッセージ ──────────────────────────
    print()
    print("═" * 65)
    print("  💾 保存完了")
    print(f"     JSON: {json_path}")
    print(f"     MD:   {md_path}")
    print()
    print("  📋 Notionへの保存方法（Claude Codeで）:")
    print(f'     「{md_path} の内容をNotionの「TRIZアイデア」データベースに保存して」')
    print()
    print("  🐙 GitHubへのコミット方法（Claude Codeで）:")
    print(f'     「triz_results フォルダの結果をGitHubにコミットして」')
    print("═" * 65)


if __name__ == "__main__":
    main()
