#!/usr/bin/env python3
"""
TRIZ Innovation Agent
====================
TRIZの40発明原理を用いてアイデアを発展させ、
ビジネス実現性の観点で有望なアイデアに絞り込むエージェント。

Usage:
    python triz_agent.py
    python triz_agent.py --idea "あなたのアイデア"
    python triz_agent.py --idea "あなたのアイデア" --top 5 --lang ja
"""

import os
import sys
import json
import argparse
import textwrap
from pathlib import Path
from typing import Optional

# .env ファイルを自動読み込み（python-dotenv が利用可能な場合）
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

try:
    import anthropic as _anthropic_mod
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai as _openai_mod
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# 矛盾マトリックスを読み込む
try:
    from triz_matrix import PARAMETERS, lookup, get_param_name, describe_contradiction
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False

# ────────────────────────────────────────────────
# 40 TRIZ 発明原理 定義
# ────────────────────────────────────────────────
TRIZ_PRINCIPLES = [
    {
        "id": 1,
        "name": "分割 (Segmentation)",
        "description": "物体・システム・プロセスを独立した部分に分割する。組み立て/分解しやすくする。分割の程度を増加させる。",
        "keywords": ["モジュール化", "区分け", "パーツ化", "個別化"],
    },
    {
        "id": 2,
        "name": "抽出 (Taking out)",
        "description": "物体・システムから干渉している部分や特性を分離する。必要な部分や特性だけを抽出する。",
        "keywords": ["エッセンス抽出", "コア分離", "不要除去"],
    },
    {
        "id": 3,
        "name": "局所的品質 (Local quality)",
        "description": "均質な構造から不均質な構造へ移行する。物体や環境の各部分を最適な条件で機能させる。各部分に固有の機能を持たせる。",
        "keywords": ["ローカル最適化", "カスタマイズ", "場所特化"],
    },
    {
        "id": 4,
        "name": "非対称 (Asymmetry)",
        "description": "対称な形状を非対称に変える。すでに非対称なら非対称の程度を増加させる。",
        "keywords": ["非均一", "左右差", "片側強化"],
    },
    {
        "id": 5,
        "name": "統合 (Merging)",
        "description": "同一または類似の物体・操作を空間的に結合する。時間的に並列・同時に行う。",
        "keywords": ["統合", "合体", "同時実行", "並列化"],
    },
    {
        "id": 6,
        "name": "多機能化 (Universality)",
        "description": "部品が複数の機能を果たすようにする。他の部品の機能を不要にする。",
        "keywords": ["多用途", "複合機能", "オールインワン"],
    },
    {
        "id": 7,
        "name": "入れ子構造 (Nested doll)",
        "description": "ある物体を別の物体の中に入れる。入れ子式に複数の物体を通過させる。",
        "keywords": ["入れ子", "埋め込み", "コンパクト化", "包含"],
    },
    {
        "id": 8,
        "name": "釣り合いおもり (Anti-weight)",
        "description": "重力などの有害な力を補償するために別の力と結合する。有害な力を有益な力と結合する。",
        "keywords": ["バランス", "補償", "相殺", "カウンター"],
    },
    {
        "id": 9,
        "name": "事前の反作用 (Preliminary anti-action)",
        "description": "有害な影響を事前に知っている場合、予め反作用を加えておく。事前に応力をかけ、使用時の有害な応力を補償する。",
        "keywords": ["予防", "プリロード", "事前対策", "リスクヘッジ"],
    },
    {
        "id": 10,
        "name": "事前の作用 (Preliminary action)",
        "description": "要求される変化の全てまたは一部を事前に実行する。最も便利な位置から活動できるように事前に配置する。",
        "keywords": ["事前準備", "プリセット", "先行投資", "下準備"],
    },
    {
        "id": 11,
        "name": "事前のクッション (Beforehand cushioning)",
        "description": "比較的低い信頼性の物体について、非常用の手段を事前に準備することでリスクを補償する。",
        "keywords": ["バックアップ", "冗長性", "フェイルセーフ", "保険"],
    },
    {
        "id": 12,
        "name": "等ポテンシャル (Equipotentiality)",
        "description": "作動条件を変えることで、物体を持ち上げたり降ろしたりする必要性をなくす。",
        "keywords": ["フラット化", "段差なし", "アクセシビリティ", "均等化"],
    },
    {
        "id": 13,
        "name": "逆発想 (The other way round)",
        "description": "問題解決に使う作用を逆にする。動く部分を固定し、固定していた部分を動かす。物体や過程を上下・内外反転させる。",
        "keywords": ["逆転", "裏返し", "反転", "アンチテーゼ"],
    },
    {
        "id": 14,
        "name": "曲面化 (Spheroidality)",
        "description": "直線的な部分を球面的なものに変える。平面を球面に、立方体を球体に変える。ローラー・ボール・らせんを使う。",
        "keywords": ["曲線化", "円形", "スパイラル", "カーブ"],
    },
    {
        "id": 15,
        "name": "ダイナミクス (Dynamics)",
        "description": "物体・環境・プロセスの特性を、各動作段階で最適となるよう調整可能にする。物体を相互にスライドするいくつかの部分に分割する。固定した物体を動けるようにする。",
        "keywords": ["動的変化", "適応", "フレキシブル", "可変"],
    },
    {
        "id": 16,
        "name": "過不足作用 (Partial or excessive actions)",
        "description": "100%の効果達成が難しければ、少し多めか少なめの効果を達成する。問題が単純化される。",
        "keywords": ["概算", "近似", "過剰提供", "MVP"],
    },
    {
        "id": 17,
        "name": "次元移行 (Another dimension)",
        "description": "物体を1次元から2次元・3次元へ移行する。多層構造を用いる。物体を傾けたり横にしたりする。",
        "keywords": ["多次元", "レイヤー化", "立体化", "視点変換"],
    },
    {
        "id": 18,
        "name": "機械的振動 (Mechanical vibration)",
        "description": "物体を振動・振盪させる。すでに振動しているなら振動数を高める。超音波振動を用いる。",
        "keywords": ["振動", "周期的刺激", "リズム", "パルス"],
    },
    {
        "id": 19,
        "name": "周期的作用 (Periodic action)",
        "description": "連続的な作用を周期的・拍動的な作用に置き換える。すでに周期的なら周波数を変える。拍動間のポーズを利用する。",
        "keywords": ["定期的", "サイクル", "インターバル", "リピート"],
    },
    {
        "id": 20,
        "name": "有益作用の継続 (Continuity of useful action)",
        "description": "全ての部品が常にフル稼働するよう継続的に作業を行う。遊休・中断的・中間的作業をなくす。",
        "keywords": ["連続稼働", "ノンストップ", "効率最大化", "フル活用"],
    },
    {
        "id": 21,
        "name": "高速実行 (Skipping)",
        "description": "有害または危険なプロセスを高速で実行する。",
        "keywords": ["高速化", "スプリント", "スキップ", "超高速"],
    },
    {
        "id": 22,
        "name": "災い転じて福となす (Blessing in disguise)",
        "description": "有害な要因・特に環境の有害な影響を、正の効果を得るために利用する。有害なものを有害なものと組み合わせて除去する。",
        "keywords": ["問題の活用", "廃棄物利用", "ピンチをチャンスに", "副産物活用"],
    },
    {
        "id": 23,
        "name": "フィードバック (Feedback)",
        "description": "フィードバックを導入する。すでにフィードバックがあるならその量・影響を変える。",
        "keywords": ["フィードバックループ", "センサー", "自動調整", "リアルタイム監視"],
    },
    {
        "id": 24,
        "name": "仲介物 (Intermediary)",
        "description": "中間物・中継プロセスを使う。ある物体を別の物体に一時的に結合する。",
        "keywords": ["仲介", "プラットフォーム", "マーケットプレイス", "メディエーター"],
    },
    {
        "id": 25,
        "name": "セルフサービス (Self-service)",
        "description": "物体が補助・修復機能を実行することで、自分自身にサービスする。廃棄物・空白エネルギーを利用する。",
        "keywords": ["自動化", "セルフサービス", "自律", "自己修復"],
    },
    {
        "id": 26,
        "name": "コピー (Copying)",
        "description": "高価・こわれやすい・不便な物体の代わりに安いコピーを使う。可視光コピーを赤外線・紫外線コピーに置き換える。",
        "keywords": ["デジタル化", "バーチャル化", "シミュレーション", "スケール複製"],
    },
    {
        "id": 27,
        "name": "安価な短命 (Cheap short-living)",
        "description": "高価で耐久性のある物体を安価な物体の集まりに置き換え、品質をある程度犠牲にする。",
        "keywords": ["使い捨て", "サブスクリプション", "レンタル", "低コスト"],
    },
    {
        "id": 28,
        "name": "機械的作用の置換 (Mechanics substitution)",
        "description": "機械的手段を感覚的手段に置き換える。電気・磁気・電磁界を物体との相互作用に使う。",
        "keywords": ["センサー化", "デジタル化", "電子化", "非接触"],
    },
    {
        "id": 29,
        "name": "空気・水圧 (Pneumatics and hydraulics)",
        "description": "固体部分の代わりに気体・液体を用いる。空気・水圧・ハイドロスタティック・エア・クッションを使う。",
        "keywords": ["流体", "柔軟性", "充填", "適応形状"],
    },
    {
        "id": 30,
        "name": "柔軟な薄膜・フィルム (Flexible shells and thin films)",
        "description": "3次元構造の代わりに柔軟な薄膜・フィルムを使う。薄膜・フィルムを使って物体を環境から分離する。",
        "keywords": ["薄膜", "コーティング", "ラッピング", "スキン"],
    },
    {
        "id": 31,
        "name": "多孔性材料 (Porous materials)",
        "description": "物体を多孔性にする。物体がすでに多孔性なら孔を有用な物質で充填する。",
        "keywords": ["多孔質", "フィルター", "通気性", "網目構造"],
    },
    {
        "id": 32,
        "name": "色の変化 (Color changes)",
        "description": "物体・環境の色や透明度を変える。光を吸収しやすくするために物体・環境に色をつける。色の添加剤・蛍光トレーサーを使う。",
        "keywords": ["可視化", "インジケーター", "視覚的フィードバック", "カラーコード"],
    },
    {
        "id": 33,
        "name": "均質性 (Homogeneity)",
        "description": "主要物体と相互作用する物体を同じ材料で作る。",
        "keywords": ["標準化", "統一規格", "互換性", "エコシステム統合"],
    },
    {
        "id": 34,
        "name": "廃棄と回収 (Discarding and recovering)",
        "description": "機能を果たした物体の部品を廃棄・変化させる。機能中に直接物体の消耗部品を復元する。",
        "keywords": ["再生可能", "循環型", "廃棄後回収", "サーキュラーエコノミー"],
    },
    {
        "id": 35,
        "name": "パラメータの変化 (Parameter changes)",
        "description": "物体の物理的状態・濃度・柔軟性・温度などのパラメータを変化させる。",
        "keywords": ["パラメータ調整", "カスタマイズ", "チューニング", "最適化"],
    },
    {
        "id": 36,
        "name": "相変化 (Phase transitions)",
        "description": "相変化中に生じる現象（体積の変化・熱の吸収や放出など）を利用する。",
        "keywords": ["状態変化", "転換点", "ブレイクスルー", "パラダイムシフト"],
    },
    {
        "id": 37,
        "name": "熱膨張 (Thermal expansion)",
        "description": "熱膨張・熱収縮する材料を使う。異なる熱膨張係数を持つ材料を使う。",
        "keywords": ["温度変化活用", "環境適応", "熱エネルギー", "温度差利用"],
    },
    {
        "id": 38,
        "name": "酸化促進 (Strong oxidants)",
        "description": "通常の空気を酸素富化した空気に置き換える。酸化剤でアクティブ化する。オゾン・酸化窒素を使う。",
        "keywords": ["触媒作用", "加速", "反応促進", "エネルギー強化"],
    },
    {
        "id": 39,
        "name": "不活性雰囲気 (Inert atmosphere)",
        "description": "通常の環境を不活性な環境に置き換える。真空下でプロセスを実行する。",
        "keywords": ["保護環境", "安全空間", "隔離", "無菌化"],
    },
    {
        "id": 40,
        "name": "複合材料 (Composite materials)",
        "description": "均質な材料から複合材料に移行する。",
        "keywords": ["ハイブリッド", "異種融合", "クロスインダストリー", "組み合わせ"],
    },
]

# ────────────────────────────────────────────────
# バッチ設定
# ────────────────────────────────────────────────
BATCH_SIZE = 5  # 1回のAPI呼び出しで処理する原理数


def create_client():
    """利用可能なAPIクライアントを返す（Anthropic優先、OpenAIにフォールバック）"""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key and HAS_ANTHROPIC:
        client = _anthropic_mod.Anthropic(api_key=anthropic_key)
        client._provider = "anthropic"
        print("  🤖 モデル: Claude (Anthropic)")
        return client
    elif openai_key and HAS_OPENAI:
        client = _openai_mod.OpenAI(api_key=openai_key)
        client._provider = "openai"
        print("  🤖 モデル: GPT-4o (OpenAI)")
        return client
    else:
        print("エラー: APIキーが設定されていません。")
        print("  Anthropic: export ANTHROPIC_API_KEY='sk-ant-...'")
        print("  OpenAI:    export OPENAI_API_KEY='sk-proj-...'")
        sys.exit(1)


def _call_llm(client, prompt: str, max_tokens: int = 4096) -> str:
    """プロバイダーに応じてLLMを呼び出す"""
    provider = getattr(client, "_provider", "openai")
    if provider == "anthropic":
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return (msg.content[0].text or "").strip()
    else:
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.choices[0].message.content or ""
        return content.strip()


def analyze_contradictions(client, idea: str) -> dict:
    """
    Phase 0: アイデアの本質的矛盾を同定し、矛盾マトリックスから
    優先すべき発明原理を特定する。
    """
    if not HAS_MATRIX:
        return {"contradictions": [], "priority_principles": [], "problem_essence": ""}

    params_text = "\n".join(
        f"  {pid}: {info['ja']} ({info['en']})"
        for pid, info in PARAMETERS.items()
    )

    prompt = f"""あなたはTRIZ（発明的問題解決理論）の世界的専門家です。

## 分析対象のアイデア・課題
{idea}

## タスク
このアイデアが取り組む問題の**技術的矛盾**（または物理的矛盾）を特定し、
Altshullerの39工学パラメータにマッピングしてください。

## Altshullerの39工学パラメータ
{params_text}

## 指示
1. このアイデアの問題の本質（技術システムとして何を改善しようとしているか）を簡潔に述べる
2. 主要な技術的矛盾を最大3つ特定する
   - 改善しようとしているパラメータ（improving）
   - それによって悪化するパラメータ（worsening）
3. 各矛盾についてTRIZ矛盾マトリックスを参照し、推奨発明原理を特定する
4. 全矛盾を通じて最優先で適用すべき発明原理をまとめる

必ず以下のJSON形式のみで出力してください（マークダウン不要）:
{{
  "problem_essence": "問題の本質（1〜2文）",
  "contradictions": [
    {{
      "improving_param": <1-39の整数>,
      "improving_name": "<パラメータ名（日本語）>",
      "worsening_param": <1-39の整数>,
      "worsening_name": "<パラメータ名（日本語）>",
      "recommended_principles": [<原理番号リスト>],
      "reasoning": "<この矛盾が発生する理由（1文）>"
    }}
  ],
  "priority_principles": [<全矛盾を通じた優先原理番号リスト（重複なし、重要度順）>]
}}"""

    raw = _call_llm(client, prompt)
    if "```" in raw:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        raw = raw[start:end]

    try:
        result = json.loads(raw)
        # マトリックスで実際のルックアップを行い、LLMの回答を補正・補強する
        for c in result.get("contradictions", []):
            imp = c.get("improving_param", 0)
            wor = c.get("worsening_param", 0)
            if 1 <= imp <= 39 and 1 <= wor <= 39:
                matrix_principles = lookup(imp, wor)
                if matrix_principles:
                    # LLMの推奨とマトリックスの推奨をマージ（マトリックス優先）
                    llm_principles = c.get("recommended_principles", [])
                    merged = matrix_principles + [p for p in llm_principles if p not in matrix_principles]
                    c["recommended_principles"] = merged
                    c["matrix_lookup"] = matrix_principles
        # priority_principles も再構築
        all_matrix = []
        for c in result.get("contradictions", []):
            all_matrix.extend(c.get("matrix_lookup", []))
        if all_matrix:
            # 出現頻度順に並べる
            from collections import Counter
            freq = Counter(all_matrix)
            result["priority_principles"] = [p for p, _ in freq.most_common()]
        return result
    except (json.JSONDecodeError, Exception):
        return {"contradictions": [], "priority_principles": [], "problem_essence": ""}


def print_contradiction_analysis(analysis: dict):
    """矛盾分析結果を表示する"""
    if not analysis.get("contradictions"):
        return
    print()
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  🔬 矛盾マトリックス分析                                │")
    print("  └─────────────────────────────────────────────────────────┘")
    essence = analysis.get("problem_essence", "")
    if essence:
        wrapped = textwrap.fill(essence, width=58, initial_indent="  ", subsequent_indent="  ")
        print(f"  問題の本質: {wrapped.strip()}")
        print()
    for i, c in enumerate(analysis.get("contradictions", []), 1):
        imp = c.get("improving_name", "")
        wor = c.get("worsening_name", "")
        principles = c.get("recommended_principles", [])
        matrix_p = c.get("matrix_lookup", [])
        print(f"  矛盾 {i}: 【{imp}↑】 vs 【{wor}↓】")
        if matrix_p:
            print(f"    マトリックス推奨原理: {matrix_p}")
        print(f"    推奨原理（統合）   : {principles}")
        reason = c.get("reasoning", "")
        if reason:
            print(f"    理由: {reason}")
        print()
    priority = analysis.get("priority_principles", [])
    if priority:
        print(f"  ⭐ 最優先発明原理: {priority[:8]}")
    print()


def apply_principles_batch(
    client,
    idea: str,
    principles: list[dict],
    lang: str = "ja",
) -> list[dict]:
    """複数のTRIZ原理を一括で適用し、アイデアを生成する。"""

    principles_text = "\n".join(
        f"原理{p['id']}: {p['name']}\n  説明: {p['description']}\n  キーワード: {', '.join(p['keywords'])}"
        for p in principles
    )

    lang_instruction = "回答は日本語で" if lang == "ja" else "Respond in English"

    prompt = f"""あなたはTRIZ発明手法の専門家です。以下のオリジナルアイデアに対して、指定されたTRIZ発明原理を一つずつ適用し、新しいビジネスアイデアを生成してください。

## オリジナルアイデア
{idea}

## 適用するTRIZ原理
{principles_text}

## 指示
各原理について以下を出力してください：
1. その原理の本質をオリジナルアイデアにどう適用するか
2. 具体的な新しいビジネスアイデア（1〜2文で簡潔に）
3. 想定顧客・市場

必ず以下のJSON形式で出力してください（マークダウンなし）:
{{
  "results": [
    {{
      "principle_id": <原理番号>,
      "principle_name": "<原理名>",
      "application": "<この原理をどう適用したか>",
      "new_idea": "<具体的な新ビジネスアイデア>",
      "target_market": "<想定顧客・市場>"
    }}
  ]
}}

{lang_instruction}。JSONのみ出力してください。"""

    response_text = _call_llm(client, prompt)

    # JSON抽出（```json ブロックが含まれる場合に対応）
    if "```" in response_text:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        response_text = response_text[start:end]

    try:
        data = json.loads(response_text)
        return data.get("results", [])
    except json.JSONDecodeError as e:
        print(f"  [警告] JSON解析エラー: {e}")
        return []


def evaluate_business_feasibility(
    client,
    original_idea: str,
    generated_ideas: list[dict],
    top_n: int = 5,
    contradiction_analysis: dict = None,
    scope_filter: str = "",
) -> dict:
    """生成されたアイデアをビジネス実現性の観点で評価・ランキングする（2段階）。"""

    valid_ideas = [item for item in generated_ideas if item.get("new_idea")]

    # ── ステップ1: スコアリングのみ（短いプロンプト） ─────
    priority_ids = []
    if contradiction_analysis and contradiction_analysis.get("priority_principles"):
        priority_ids = contradiction_analysis["priority_principles"][:8]

    ideas_lines = "\n".join(
        f"{i+1}. [原理{item['principle_id']}:{item['principle_name']}] {item['new_idea']} (市場:{item['target_market']})"
        for i, item in enumerate(valid_ideas)
    )

    scope_line = f"\n【除外条件】{scope_filter}" if scope_filter else ""

    score_prompt = f"""以下のTRIZアイデアリストを5基準（市場規模・実現容易性・収益モデル・競合優位性・イノベーション度）で各10点採点し、上位{top_n}件の原理番号とスコアをJSON出力してください。
優先加点原理: {priority_ids}{scope_line}

アイデア一覧:
{ideas_lines}

出力形式（JSONのみ）:
{{"ranked": [{{"rank":1,"principle_id":番号,"principle_name":"名前","idea":"内容","target_market":"市場","scores":{{"market_size":点,"feasibility":点,"revenue_model":点,"competitive_advantage":点,"innovation":点}},"total_score":合計}}]}}"""

    score_text = _call_llm(client, score_prompt, max_tokens=4000)
    start = score_text.find("{")
    end = score_text.rfind("}") + 1
    if start != -1 and end > start:
        score_text = score_text[start:end]

    try:
        scored = json.loads(score_text)
        top_candidates = scored.get("ranked", [])[:top_n]
    except json.JSONDecodeError:
        top_candidates = valid_ideas[:top_n]

    if not top_candidates:
        return {"top_ideas": [], "summary": "評価中にエラーが発生しました。"}

    # ── ステップ2: 上位N件のみ詳細分析 ──────────────────
    top_ideas_result = []
    for candidate in top_candidates:
        pid = candidate.get("principle_id", 0)
        pname = candidate.get("principle_name", "")
        idea_text = candidate.get("idea") or candidate.get("new_idea", "")
        market = candidate.get("target_market", "")
        scores = candidate.get("scores", {})
        total = candidate.get("total_score", sum(scores.values()))

        detail_prompt = f"""以下の発明アイデアについて、事業開発・技術経営の専門家として詳細評価を行いJSONで返してください。

テーマ: {original_idea}
発明原理: 原理{pid} {pname}
アイデア: {idea_text}
対象市場: {market}

以下のJSON形式で出力（各フィールド300〜500字、固有名詞・専門用語・定量データを積極使用）:
{{"current_problems":"<現状課題と業界限界300-500字>","how_it_solves":"<本アイデアの解決メカニズム300-500字>","existing_comparison":"<既存事例との比較（企業名含む）300-500字>","target_persona":"<ターゲットペルソナと利用シーン300-500字>","concrete_companies":"<想定顧客企業3-5社と導入シナリオ300-500字>","why_promising":"<有望な理由（市場・技術・規制トレンド）300-500字>","key_risks":"<主要リスクと対策300-500字>","next_steps":["誰が何をいつまでに1","2","3","4","5"],"summary":"<この案の総括200字>"}}

JSONのみ出力してください。"""

        detail_text = _call_llm(client, detail_prompt, max_tokens=6000)
        d_start = detail_text.find("{")
        d_end = detail_text.rfind("}") + 1
        if d_start != -1 and d_end > d_start:
            detail_text = detail_text[d_start:d_end]

        try:
            detail = json.loads(detail_text)
        except json.JSONDecodeError:
            detail = {}

        top_ideas_result.append({
            "rank": candidate.get("rank", len(top_ideas_result) + 1),
            "principle_id": pid,
            "principle_name": pname,
            "idea": idea_text,
            "target_market": market,
            "scores": scores,
            "total_score": total,
            **detail,
        })

    # ── ステップ3: 総合考察 ───────────────────────────────
    names = "、".join(f"原理{t['principle_id']}:{t['principle_name']}" for t in top_ideas_result)
    summary_prompt = f"""テーマ「{original_idea}」のTRIZ分析で上位に選ばれたアイデア（{names}）について、ポートフォリオ分析・推奨優先順位・業界への影響・中長期ロードマップを300〜500字で総括してください。テキストのみ出力。"""
    summary = _call_llm(client, summary_prompt, max_tokens=1000)

    return {"top_ideas": top_ideas_result, "summary": summary}


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════╗
║           TRIZ イノベーション エージェント                   ║
║     40発明原理 × ビジネス実現性評価                         ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_progress(current: int, total: int, batch_ids: list[int]):
    ids_str = ", ".join(str(i) for i in batch_ids)
    pct = int(current / total * 100)
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"  [{bar}] {pct:3d}%  原理 {ids_str} を処理中...")


def print_results(evaluation: dict, original_idea: str):
    """結果をフォーマットして表示する。"""

    print("\n" + "═" * 65)
    print("  📊 TRIZ分析結果 — ビジネス実現性ランキング")
    print("═" * 65)
    print(f"  元のアイデア: {original_idea}\n")

    top_ideas = evaluation.get("top_ideas", [])

    for item in top_ideas:
        scores = item.get("scores", {})
        total = item.get("total_score", 0)
        rank = item.get("rank", "?")

        print(f"{'─' * 65}")
        print(f"  🏆 第{rank}位  [総合スコア: {total}/50点]")
        print(f"  原理: {item.get('principle_name', '?')}")
        print()

        idea_text = item.get("idea", "")
        wrapped = textwrap.fill(idea_text, width=60, initial_indent="  ", subsequent_indent="  ")
        print(f"  💡 アイデア:")
        print(wrapped)
        print()

        print(f"  🎯 対象市場: {item.get('target_market', '?')}")
        print()

        print("  📈 評価スコア:")
        score_items = [
            ("市場規模・成長性", scores.get("market_size", 0)),
            ("実現容易性",       scores.get("feasibility", 0)),
            ("収益モデル",       scores.get("revenue_model", 0)),
            ("競合優位性",       scores.get("competitive_advantage", 0)),
            ("イノベーション度", scores.get("innovation", 0)),
        ]
        for label, score in score_items:
            bar = "▓" * score + "░" * (10 - score)
            print(f"    {label:<14} [{bar}] {score}/10")
        print()

        current_problems = item.get("current_problems", "")
        if current_problems:
            wrapped = textwrap.fill(current_problems, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  🔴 現状の課題・問題点:")
            print(wrapped)
            print()

        how_it_solves = item.get("how_it_solves", "")
        if how_it_solves:
            wrapped = textwrap.fill(how_it_solves, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  🔧 解決メカニズム:")
            print(wrapped)
            print()

        why = item.get("why_promising", "")
        if why:
            wrapped = textwrap.fill(why, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  ✅ 有望な理由（深掘り分析）:")
            print(wrapped)
            print()

        existing_comparison = item.get("existing_comparison", "")
        if existing_comparison:
            wrapped = textwrap.fill(existing_comparison, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  📊 既存ソリューションとの比較:")
            print(wrapped)
            print()

        target_persona = item.get("target_persona", "")
        if target_persona:
            wrapped = textwrap.fill(target_persona, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  👤 ターゲットペルソナ:")
            print(wrapped)
            print()

        concrete_companies = item.get("concrete_companies", "")
        if concrete_companies:
            wrapped = textwrap.fill(concrete_companies, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  🏢 想定顧客企業:")
            print(wrapped)
            print()

        risks = item.get("key_risks", "")
        if risks:
            wrapped = textwrap.fill(risks, width=60, initial_indent="  ", subsequent_indent="  ")
            print(f"  ⚠️  主要リスクと対策:")
            print(wrapped)
            print()

        next_steps = item.get("next_steps", "")
        if next_steps:
            print(f"  🚀 ネクストアクション:")
            # リスト形式と文字列形式の両方に対応
            lines = next_steps if isinstance(next_steps, list) else next_steps.split("\n")
            for i, line in enumerate(lines, 1):
                line = str(line).strip()
                if line:
                    print(f"     {i}. {line}")
        print()

    print("═" * 65)
    summary = evaluation.get("summary", "")
    if summary:
        print("\n  📝 総合考察:")
        wrapped = textwrap.fill(summary, width=60, initial_indent="  ", subsequent_indent="  ")
        print(wrapped)
    print()


def save_results(evaluation: dict, original_idea: str, all_ideas: list[dict], output_file: str, contradiction_analysis: dict = None):
    """結果をJSONファイルに保存する。"""
    output = {
        "original_idea": original_idea,
        "contradiction_analysis": contradiction_analysis or {},
        "all_generated_ideas": all_ideas,
        "evaluation": evaluation,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  💾 全結果を保存しました: {output_file}")


def run_triz_agent(
    idea: str,
    top_n: int = 5,
    lang: str = "ja",
    output_file: Optional[str] = None,
    verbose: bool = False,
    scope_filter: str = "",
):
    """TRIZエージェントのメイン処理。"""
    print_banner()

    client = create_client()

    print(f"  📌 アイデア: {idea}")
    print(f"  🔢 適用原理数: {len(TRIZ_PRINCIPLES)}（40原理すべて）")
    print(f"  🏆 上位表示数: {top_n}件")
    print()

    # ── Phase 0: 矛盾マトリックス分析 ────────────────────
    print("━" * 65)
    print("  Phase 0: 矛盾マトリックスで技術的矛盾を同定中...")
    print("━" * 65)
    contradiction_analysis = analyze_contradictions(client, idea)
    print_contradiction_analysis(contradiction_analysis)
    priority_principles = contradiction_analysis.get("priority_principles", [])

    # ── フェーズ1: 40原理の適用（優先原理を先頭に） ──────
    print("━" * 65)
    print("  フェーズ 1/2: TRIZ 40原理を適用中...")
    if priority_principles:
        print(f"  （矛盾マトリックス推奨原理を優先: {priority_principles[:6]}）")
    print("━" * 65)

    # 優先原理を先頭に並べ替え
    priority_set = set(priority_principles)
    priority_batch = [p for p in TRIZ_PRINCIPLES if p["id"] in priority_set]
    remaining_batch = [p for p in TRIZ_PRINCIPLES if p["id"] not in priority_set]
    ordered_principles = priority_batch + remaining_batch

    all_generated = []
    batches = [
        ordered_principles[i : i + BATCH_SIZE]
        for i in range(0, len(ordered_principles), BATCH_SIZE)
    ]

    for i, batch in enumerate(batches):
        ids = [p["id"] for p in batch]
        # 優先原理かどうかを示すマーク
        mark = "⭐" if any(p["id"] in priority_set for p in batch) else "  "
        print_progress(i * BATCH_SIZE, len(TRIZ_PRINCIPLES), ids)

        results = apply_principles_batch(client, idea, batch, lang)
        # 優先原理にフラグを付ける
        for r in results:
            r["is_priority"] = r.get("principle_id") in priority_set
        all_generated.extend(results)

        if verbose:
            for r in results:
                flag = "⭐" if r.get("is_priority") else "  "
                print(f"  {flag} 原理{r.get('principle_id')}: {r.get('new_idea', '')[:60]}...")

    print_progress(len(TRIZ_PRINCIPLES), len(TRIZ_PRINCIPLES), [])
    print(f"\n  ✅ {len(all_generated)}件のアイデアを生成しました。")
    print(f"     うち矛盾マトリックス推奨原理: {sum(1 for r in all_generated if r.get('is_priority'))}件")
    print()

    # ── フェーズ2: ビジネス実現性評価 ─────────────────────
    print("━" * 65)
    print("  フェーズ 2/2: ビジネス実現性を評価中...")
    print("  （矛盾マトリックス推奨原理を優先考慮）")
    print("━" * 65)

    evaluation = evaluate_business_feasibility(
        client, idea, all_generated, top_n, contradiction_analysis, scope_filter
    )
    print(f"  ✅ 評価完了。上位{top_n}件に絞り込みました。")
    print()

    # ── 結果表示 ──────────────────────────────────────────
    print_results(evaluation, idea)

    # ── ファイル保存 ───────────────────────────────────────
    if output_file:
        save_results(evaluation, idea, all_generated, output_file, contradiction_analysis)

    return evaluation, all_generated


def main():
    parser = argparse.ArgumentParser(
        description="TRIZの40発明原理を用いてアイデアを発展させ、ビジネス実現性で絞り込むエージェント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python triz_agent.py
  python triz_agent.py --idea "遠隔地の医療診断を改善したい"
  python triz_agent.py --idea "食品ロスを削減したい" --top 3
  python triz_agent.py --idea "教育格差を解消したい" --output results.json
        """,
    )
    parser.add_argument(
        "--idea", "-i",
        type=str,
        default=None,
        help="発展させたいアイデアや解決したい課題",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=5,
        help="表示する上位アイデアの数（デフォルト: 5）",
    )
    parser.add_argument(
        "--lang", "-l",
        type=str,
        default="ja",
        choices=["ja", "en"],
        help="出力言語（ja: 日本語, en: 英語）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="全結果をJSONで保存するファイルパス",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="生成中のアイデアを逐次表示する",
    )
    parser.add_argument(
        "--scope-filter", "-f",
        type=str,
        default="",
        help="評価から除外する発明カテゴリの説明（例: 'サービス・プラットフォーム・ビジネスモデルは除外し、デバイス技術のみ選出'）",
    )

    args = parser.parse_args()

    # インタラクティブ入力
    if args.idea is None:
        print_banner()
        print("  アイデアや解決したい課題を入力してください。")
        print("  （例: 「高齢者の孤独感を解消したい」「食品廃棄を減らしたい」）")
        print()
        idea = input("  > ").strip()
        if not idea:
            print("アイデアが入力されていません。終了します。")
            sys.exit(0)
        top_n = input(f"  上位何件表示しますか？（デフォルト: {args.top}）: ").strip()
        top_n = int(top_n) if top_n.isdigit() else args.top
        save = input("  結果をJSONに保存しますか？(y/N): ").strip().lower()
        output_file = "triz_results.json" if save == "y" else None
    else:
        idea = args.idea
        top_n = args.top
        output_file = args.output

    run_triz_agent(
        idea=idea,
        top_n=top_n,
        lang=args.lang,
        output_file=output_file,
        verbose=args.verbose,
        scope_filter=args.scope_filter,
    )


if __name__ == "__main__":
    main()
