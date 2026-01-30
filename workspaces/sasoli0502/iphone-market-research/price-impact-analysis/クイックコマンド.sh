#!/bin/bash
# 買取価格変更効果計測 - クイックコマンド集

echo "=========================================="
echo "買取価格変更効果計測 - クイックコマンド"
echo "=========================================="
echo ""

BASE_DIR="/Users/noguchisara/projects/work/iphone-market-research/price-impact-analysis"
cd "$BASE_DIR"

echo "📂 現在のディレクトリ: $(pwd)"
echo ""

echo "使用可能なコマンド:"
echo ""
echo "1️⃣  価格変更履歴の生成"
echo "   uv run python scripts/create_price_change_log.py --auto"
echo ""
echo "2️⃣  データ収集・整形"
echo "   uv run python scripts/collect_data.py"
echo ""
echo "3️⃣  効果分析"
echo "   uv run python scripts/analyze_impact.py --change-date 2025-11-19"
echo ""
echo "4️⃣  レポート生成"
echo "   uv run python scripts/generate_report.py --change-date 2025-11-19"
echo ""
echo "5️⃣  一括実行（2-4をまとめて）"
echo "   uv run python scripts/collect_data.py && \\"
echo "   uv run python scripts/analyze_impact.py --change-date 2025-11-19 && \\"
echo "   uv run python scripts/generate_report.py --change-date 2025-11-19"
echo ""
echo "=========================================="
