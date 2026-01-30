#!/usr/bin/env python3
"""
cats株式会社への返金請求書PDF作成スクリプト
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from datetime import datetime
import os

def create_invoice_pdf(output_path):
    """請求書PDFを作成"""

    # PDFキャンバス作成
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # 日本語フォント設定（Macのシステムフォントを使用）
    font_paths = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]

    font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Japanese', font_path))
                font_registered = True
                break
            except:
                continue

    if not font_registered:
        print("警告: 日本語フォントが見つかりません。代替フォントを使用します。")
        font_name = 'Helvetica'
    else:
        font_name = 'Japanese'

    # タイトル
    c.setFont(font_name, 24)
    c.drawCentredString(width/2, height - 50*mm, "請求書")

    # 線を引く
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.line(50*mm, height - 55*mm, width - 50*mm, height - 55*mm)

    # 請求書情報
    c.setFont(font_name, 10)
    y = height - 70*mm
    c.drawString(40*mm, y, f"請求書番号: INV-20251023-001")
    c.drawString(40*mm, y - 5*mm, f"発行日: 2025年10月23日")
    c.drawRightString(width - 40*mm, y, f"支払期限: 2025年10月31日")

    # 請求先
    y -= 20*mm
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "【請求先】")
    c.setFont(font_name, 10)
    c.drawString(40*mm, y - 7*mm, "cats株式会社 御中")
    c.drawString(40*mm, y - 12*mm, "ご担当者様")

    # 請求元
    y -= 25*mm
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "【請求元】")
    c.setFont(font_name, 10)
    c.drawString(40*mm, y - 7*mm, "株式会社ecot")
    c.drawString(40*mm, y - 12*mm, "〒101-0021 東京都千代田区外神田4丁目3-3 1F")
    c.drawString(40*mm, y - 17*mm, "TEL: 03-6262-9910")
    c.drawString(40*mm, y - 22*mm, "代表者: 本間 久隆")

    # 請求内容テーブル
    y -= 28*mm
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "【請求内容】")

    # テーブルヘッダー
    y -= 10*mm
    table_y = y
    c.setFillColor(colors.lightgrey)
    c.rect(40*mm, table_y - 8*mm, width - 80*mm, 8*mm, fill=1, stroke=1)

    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    c.drawString(42*mm, table_y - 6*mm, "項目")
    c.drawString(90*mm, table_y - 6*mm, "期間")
    c.drawRightString(width - 42*mm, table_y - 6*mm, "金額（税込）")

    # テーブル内容
    table_y -= 8*mm
    c.rect(40*mm, table_y - 8*mm, width - 80*mm, 8*mm, fill=0, stroke=1)
    c.setFont(font_name, 11)
    c.drawString(42*mm, table_y - 6*mm, "返金")
    c.drawString(90*mm, table_y - 6*mm, "2025年3月〜2025年7月")
    c.drawRightString(width - 42*mm, table_y - 6*mm, "¥522,500")

    # 返金理由
    table_y -= 12*mm
    c.setFont(font_name, 10)
    c.drawString(40*mm, table_y, "返金理由: サービス未利用期間における請求分の返金")

    # 合計金額（強調）
    y = table_y - 15*mm
    c.setFillColor(colors.lightgrey)
    c.rect(40*mm, y - 12*mm, width - 80*mm, 12*mm, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont(font_name, 14)
    c.drawRightString(width - 42*mm, y - 8*mm, "ご請求金額: ¥522,500（税込）")

    # 振込先情報
    y -= 22*mm
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "【お振込先】")
    c.setFont(font_name, 10)
    c.drawString(40*mm, y - 7*mm, "銀行名: 三菱UFJ銀行")
    c.drawString(40*mm, y - 12*mm, "支店名: 高田馬場支店")
    c.drawString(40*mm, y - 17*mm, "口座種別: 普通")
    c.drawString(40*mm, y - 22*mm, "口座番号: 0102540")
    c.drawString(40*mm, y - 27*mm, "口座名義: カ）エコット")

    # 支払方法
    y -= 33*mm
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "【お支払い方法】")
    c.setFont(font_name, 10)
    c.drawString(40*mm, y - 6*mm, "・銀行振込")
    c.drawString(40*mm, y - 11*mm, "・支払期限: 2025年10月31日")
    c.drawString(40*mm, y - 16*mm, "・振込手数料は貴社にてご負担いただきますようお願い申し上げます。")

    # 備考
    y -= 24*mm
    c.setFont(font_name, 12)
    c.drawString(40*mm, y, "【備考】")
    c.setFont(font_name, 10)
    c.drawString(40*mm, y - 6*mm, "返金期間: 2025年3月〜2025年7月")
    c.drawString(40*mm, y - 11*mm, "請求明細: 返金")
    c.drawString(40*mm, y - 17*mm, "お振込みいただきましたら、お手数ですが弊社までご連絡いただけますと幸いです。")

    # フッター
    y -= 25*mm
    if y < 30*mm:  # 下部余白確保
        y = 30*mm
    c.setFont(font_name, 10)
    c.drawCentredString(width/2, y, "以上、よろしくお願い申し上げます。")

    # PDF保存
    c.save()
    print(f"請求書PDFを作成しました: {output_path}")

if __name__ == "__main__":
    output_path = "/Users/noguchisara/projects/work/misc-tasks/outputs/cats返金_請求書_20251023.pdf"
    create_invoice_pdf(output_path)
