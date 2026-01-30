"""
マネーフォワード仕訳帳CSVからクレジットカード取引を抽出
"""
import pandas as pd
from pathlib import Path

# CSVファイルのパス
csv_path = "/Users/noguchisara/Downloads/仕訳帳_20251029_1537.csv"

# CSVを読み込み（Shift-JIS or CP932）
try:
    df = pd.read_csv(csv_path, encoding='shift_jis')
except:
    df = pd.read_csv(csv_path, encoding='cp932')

print(f"総レコード数: {len(df)}")
print(f"\nカラム一覧:")
print(df.columns.tolist())

# データの先頭を確認
print(f"\n先頭5行:")
print(df.head())

# クレジットカード関連の取引を抽出
# 方法1: 勘定科目が「未払金」の取引
credit_cards_1 = df[df['借方勘定科目'].str.contains('未払金', na=False) |
                     df['貸方勘定科目'].str.contains('未払金', na=False)]

print(f"\n未払金の取引数: {len(credit_cards_1)}")

# 方法2: 補助科目にカード名が含まれる可能性
# カード会社のキーワード
card_keywords = ['カード', 'CARD', 'クレジット', '三井住友', '楽天', 'JCB', 'VISA', 'Master',
                 'AMEX', 'アメックス', 'セゾン', 'イオン', 'エポス', 'ビュー']

# 全カラムから抽出
credit_cards_2 = df[
    df['借方補助科目'].str.contains('|'.join(card_keywords), na=False) |
    df['貸方補助科目'].str.contains('|'.join(card_keywords), na=False)
]

print(f"カードキーワードでの取引数: {len(credit_cards_2)}")

# 両方を結合してユニークな取引を取得
credit_cards = pd.concat([credit_cards_1, credit_cards_2]).drop_duplicates(subset='取引No')

print(f"\n合計クレジットカード取引数: {len(credit_cards)}")

# 補助科目の一覧を確認
print(f"\n借方補助科目の一覧:")
print(df['借方補助科目'].dropna().unique()[:50])

print(f"\n貸方補助科目の一覧:")
print(df['貸方補助科目'].dropna().unique()[:50])

# クレジットカード別の集計
if len(credit_cards) > 0:
    print(f"\n借方補助科目別の取引数:")
    print(credit_cards['借方補助科目'].value_counts().head(20))

    print(f"\n貸方補助科目別の取引数:")
    print(credit_cards['貸方補助科目'].value_counts().head(20))

    # 結果を保存
    output_path = "/Users/noguchisara/projects/work/finance-cashflow/data/credit_card_transactions.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    credit_cards.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n抽出結果を保存: {output_path}")
