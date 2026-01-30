"""
クレジットカード運用最適化スクリプト

支払猶予を最大化しつつ、カード枠の制約を守り、最適なカード配分を計算する。

Usage:
    uv run python scripts/optimize_credit_schedule.py data/input_YYYYMM.yaml
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml


class Card:
    """カード情報"""
    def __init__(self, data: dict):
        self.id = data['id']
        self.name = data['name']
        self.brand = data['brand']
        self.closing_day = data['closing_day']
        self.payment_day_offset = data['payment_day_offset']
        self.payment_month_offset = data['payment_month_offset']
        self.credit_limit = data['credit_limit']
        self.invoice_card_payment = data['invoice_card_payment']
        self.application_days_offset = data.get('application_days_offset', 4)

        # 実行時に設定される値
        self.available_balance = 0
        self.grace_period_days = 0
        self.application_day = 0

    def calculate_grace_period(self, target_month: int, target_year: int) -> int:
        """支払猶予期間を計算"""
        # 申請日 = 締め日 + 1日
        if self.closing_day == 31:
            # 月末締めの場合
            closing_date = datetime(target_year, target_month, 1) + timedelta(days=32)
            closing_date = closing_date.replace(day=1) - timedelta(days=1)
            self.application_day = 1
        else:
            self.application_day = self.closing_day + 1
            closing_date = datetime(target_year, target_month, self.closing_day)

        # 着金日 = 申請日 + 4営業日（簡易計算: 4日後）
        application_date = closing_date + timedelta(days=1)
        arrival_date = application_date + timedelta(days=self.application_days_offset)

        # 支払日を計算
        arrival_month = arrival_date.month
        arrival_year = arrival_date.year

        # 締め日以降の着金かどうかで支払月が変わる
        if arrival_date.day > self.closing_day:
            # 締め日以降の着金 → 翌々月扱い
            payment_month_add = self.payment_month_offset + 1
        else:
            # 締め日以内の着金 → 予定通りの月
            payment_month_add = self.payment_month_offset

        # 支払月を計算
        payment_month = arrival_month + payment_month_add
        payment_year = arrival_year
        if payment_month > 12:
            payment_month -= 12
            payment_year += 1

        # 支払日を設定
        payment_date = datetime(payment_year, payment_month, self.payment_day_offset)

        # 支払猶予期間 = 支払日 - 申請日
        self.grace_period_days = (payment_date - application_date).days

        return self.grace_period_days

    def __repr__(self):
        return f"Card({self.name}, 猶予{self.grace_period_days}日)"


class Payment:
    """支払情報"""
    def __init__(self, payment_id: str, name: str, category: str, amount: int,
                 is_splittable: bool = False, payment_deadline_day: Optional[int] = None):
        self.id = payment_id
        self.name = name
        self.category = category
        self.amount = amount
        self.is_splittable = is_splittable
        self.payment_deadline_day = payment_deadline_day

        # 配分結果
        self.allocations: List[Dict] = []  # {card: Card, amount: int}

        # 追加属性（後で設定される）
        self.preferred_card: Optional[str] = None
        self.priority: int = 999
        self.application_date: Optional[str] = None
        self.current_card: Optional[str] = None  # 現在使っているカード

    def allocate(self, card: Card, amount: int):
        """カードに配分"""
        self.allocations.append({'card': card, 'amount': amount})

    def __repr__(self):
        return f"Payment({self.name}, {self.amount:,}円)"


class CreditCardOptimizer:
    """クレジットカード運用最適化"""

    def __init__(self, master_data_path: Path, input_data_path: Path):
        # データ読み込み
        with open(master_data_path, 'r', encoding='utf-8') as f:
            self.master_data = yaml.safe_load(f)

        with open(input_data_path, 'r', encoding='utf-8') as f:
            self.input_data = yaml.safe_load(f)

        # カード情報を初期化
        self.cards: Dict[str, Card] = {}
        for card_data in self.master_data['cards']:
            card = Card(card_data)
            self.cards[card.id] = card

        # 利用可能額を設定
        for card_id, balance in self.input_data['card_balances'].items():
            if card_id in self.cards:
                self.cards[card_id].available_balance = balance

        # 対象月
        self.target_year = self.input_data['target_month']['year']
        self.target_month = self.input_data['target_month']['month']
        self.days_in_month = self.input_data['target_month']['days_in_month']

        # 支払情報を初期化
        self.payments: List[Payment] = []

        # 結果
        self.warnings: List[str] = []

    def calculate_grace_periods(self):
        """全カードの支払猶予期間を計算"""
        for card in self.cards.values():
            card.calculate_grace_period(self.target_month, self.target_year)

        # 請求書カード払い可能なカードを支払猶予期間でソート
        self.invoice_cards = sorted(
            [c for c in self.cards.values() if c.invoice_card_payment],
            key=lambda x: x.grace_period_days,
            reverse=True
        )

    def load_payments(self):
        """支払情報を読み込み"""
        # 固定費（請求書カード払い）
        for p in self.master_data['fixed_invoice_payments']:
            payment = Payment(
                payment_id=p['id'],
                name=p['name'],
                category=p['category'],
                amount=p['amount'],
                is_splittable=p.get('is_splittable', False),
                payment_deadline_day=p.get('payment_deadline_day')
            )
            self.payments.append(payment)

        # 変動費（請求書カード払い）
        for p in self.master_data['variable_invoice_payments']:
            payment_input = self.input_data['variable_invoice_payments'].get(p['id'])

            # 新形式（辞書）と旧形式（数値）の両方に対応
            if isinstance(payment_input, dict):
                amount = payment_input.get('amount', p['typical_amount'])
                preferred_card = payment_input.get('preferred_card')
                priority = payment_input.get('priority', 999)
                application_date = payment_input.get('application_date')
            else:
                amount = payment_input if payment_input else p['typical_amount']
                preferred_card = None
                priority = 999
                application_date = None

            payment = Payment(
                payment_id=p['id'],
                name=p['name'],
                category=p['category'],
                amount=amount,
                is_splittable=p.get('is_splittable', False),
                payment_deadline_day=p.get('payment_deadline_day')
            )
            payment.preferred_card = preferred_card
            payment.priority = priority
            payment.application_date = application_date
            self.payments.append(payment)

        # 固定費（通常クレカ払い）
        for p in self.master_data['fixed_regular_payments']:
            payment = Payment(
                payment_id=p['id'],
                name=p['name'],
                category=p['category'],
                amount=p['amount'],
                is_splittable=True
            )
            payment.current_card = p.get('current_card')
            self.payments.append(payment)

        # 変動費（通常クレカ払い）
        for p in self.master_data['variable_regular_payments']:
            amount = self.input_data['variable_regular_payments'].get(p['id'], p['typical_amount'])
            payment = Payment(
                payment_id=p['id'],
                name=p['name'],
                category=p['category'],
                amount=amount,
                is_splittable=True
            )
            payment.current_card = p.get('current_card')
            self.payments.append(payment)

        # 広告チャージ（自動計算）
        for ad in self.master_data['ad_charges']:
            amount = ad['daily_amount'] * self.days_in_month
            payment = Payment(
                payment_id=ad['id'],
                name=ad['name'],
                category=ad['category'],
                amount=amount,
                is_splittable=True
            )
            self.payments.append(payment)

    def allocate_payments(self):
        """支払を最適配分"""
        # 【優先度1】preferred_cardが指定されている支払いを優先配分
        preferred_payments = sorted(
            [p for p in self.payments if p.preferred_card and not p.allocations],
            key=lambda x: x.priority
        )

        for payment in preferred_payments:
            preferred_card = self.cards.get(payment.preferred_card)
            if not preferred_card:
                self.warnings.append(f"⚠️ {payment.name}の優先カード「{payment.preferred_card}」が見つかりません")
                continue

            if preferred_card.available_balance >= payment.amount:
                payment.allocate(preferred_card, payment.amount)
                preferred_card.available_balance -= payment.amount
            else:
                self.warnings.append(f"⚠️ {payment.name}（{payment.amount:,}円）を{preferred_card.name}に配分できません（枠不足: {preferred_card.available_balance:,}円）")

        # 【優先度2】請求書カード払いの支払いを配分（優先配分済みを除外）
        invoice_payments = [p for p in self.payments
                           if p.category in ['地代家賃', '仕入', '荷造運賃']
                           and not p.allocations]  # 未配分のもの

        for payment in invoice_payments:
            if payment.is_splittable:
                # 分割可能な場合は、複数カードに配分
                self._allocate_splittable(payment)
            else:
                # 分割不可の場合は、1枚のカードに配分
                self._allocate_non_splittable(payment)

        # 【優先度3】通常クレカ払いを配分
        regular_payments = [p for p in self.payments if p.category in ['通信費', '広告宣伝費', '備品・消耗品費', '支払手数料']]
        for payment in regular_payments:
            self._allocate_splittable(payment)

        # 【優先度4】広告チャージを配分
        ad_payments = [p for p in self.payments if p.category == '仮払金']
        for payment in ad_payments:
            self._allocate_splittable(payment)

    def _allocate_non_splittable(self, payment: Payment):
        """分割不可の支払いを配分"""
        # 支払猶予が長いカードから順に試す
        for card in self.invoice_cards:
            if card.available_balance >= payment.amount:
                payment.allocate(card, payment.amount)
                card.available_balance -= payment.amount
                return

        # 枠が足りない場合は警告
        self.warnings.append(f"⚠️ {payment.name}（{payment.amount:,}円）を配分できるカードがありません")

    def _allocate_splittable(self, payment: Payment):
        """分割可能な支払いを配分"""
        remaining = payment.amount

        # 請求書カード払いの場合は、invoice_cardsから配分
        if payment.category in ['地代家賃', '仕入', '荷造運賃']:
            card_list = self.invoice_cards
        else:
            # 通常払いの場合は、全カードから配分（支払猶予が長い順）
            card_list = sorted(self.cards.values(), key=lambda x: x.grace_period_days, reverse=True)

        for card in card_list:
            if remaining <= 0:
                break

            if card.available_balance > 0:
                allocated_amount = min(remaining, card.available_balance)
                payment.allocate(card, allocated_amount)
                card.available_balance -= allocated_amount
                remaining -= allocated_amount

        if remaining > 0:
            self.warnings.append(f"⚠️ {payment.name}の{remaining:,}円を配分できませんでした")

    def generate_report(self) -> str:
        """レポートを生成"""
        lines = []
        lines.append("# クレジットカード運用最適化レポート")
        lines.append(f"\n**対象月**: {self.target_year}年{self.target_month}月")
        lines.append("")

        # カード情報
        lines.append("---")
        lines.append("\n## カード情報（支払猶予期間順）")
        lines.append("")
        lines.append("| カード名 | 猶予 | 枠 | 利用可能 | 請求書払い |")
        lines.append("|---------|------|-----|---------|-----------|")
        for card in sorted(self.cards.values(), key=lambda x: x.grace_period_days, reverse=True):
            invoice_mark = "○" if card.invoice_card_payment else "×"
            lines.append(f"| {card.name} | {card.grace_period_days}日 | {card.credit_limit:,}円 | "
                        f"{self.input_data['card_balances'].get(card.id, 0):,}円 | {invoice_mark} |")

        # 支払配分結果
        lines.append("\n---")
        lines.append("\n## 支払配分結果")
        lines.append("")

        for payment in self.payments:
            if payment.allocations:
                lines.append(f"\n### {payment.name} ({payment.category})")
                lines.append(f"**合計**: {payment.amount:,}円")
                lines.append("")
                for alloc in payment.allocations:
                    card = alloc['card']
                    amount = alloc['amount']
                    lines.append(f"- {card.name}: **{amount:,}円** (申請{card.application_day}日, 猶予{card.grace_period_days}日)")

        # カード別使用状況
        lines.append("\n---")
        lines.append("\n## カード別使用状況")
        lines.append("")

        card_usage = {}
        for payment in self.payments:
            for alloc in payment.allocations:
                card_id = alloc['card'].id
                amount = alloc['amount']
                if card_id not in card_usage:
                    card_usage[card_id] = {
                        'card': alloc['card'],
                        'total': 0,
                        'payments': []
                    }
                card_usage[card_id]['total'] += amount
                card_usage[card_id]['payments'].append({
                    'payment': payment.name,
                    'amount': amount
                })

        for card_id, usage in card_usage.items():
            card = usage['card']
            initial_balance = self.input_data['card_balances'].get(card_id, 0)
            used = usage['total']
            remaining = initial_balance - used

            status = "✓" if remaining >= 0 else "⚠️ 枠超過"
            lines.append(f"\n### {card.name}")
            lines.append(f"- **利用可能額**: {initial_balance:,}円")
            lines.append(f"- **使用予定額**: {used:,}円")
            lines.append(f"- **残り枠**: {remaining:,}円 {status}")
            lines.append(f"\n**内訳:**")
            for p in usage['payments']:
                lines.append(f"- {p['payment']}: {p['amount']:,}円")

        # 警告
        if self.warnings:
            lines.append("\n---")
            lines.append("\n## ⚠️ 警告")
            lines.append("")
            for warning in self.warnings:
                lines.append(f"- {warning}")

        # カード切り替え推奨
        lines.append("\n---")
        lines.append("\n## 💡 カード切り替え推奨")
        lines.append("")
        lines.extend(self._generate_card_switch_recommendations())

        # アクションリスト
        lines.append("\n---")
        lines.append("\n## 📋 アクションリスト")
        lines.append("")
        lines.extend(self._generate_action_list())

        # 引き落としスケジュール
        lines.append("\n---")
        lines.append("\n## 💳 引き落としスケジュール")
        lines.append("")
        lines.extend(self._generate_withdrawal_schedule())

        return "\n".join(lines)

    def _generate_card_switch_recommendations(self) -> List[str]:
        """カード切り替え推奨を生成"""
        lines = []

        for payment in self.payments:
            if not payment.current_card or not payment.allocations:
                continue

            # 配分されたカードを取得
            allocated_cards = [alloc['card'].id for alloc in payment.allocations]
            current_card_id = payment.current_card

            # 現在のカードと推奨カードが異なる場合
            if current_card_id not in allocated_cards:
                current_card = self.cards.get(current_card_id)
                recommended_cards = [alloc['card'] for alloc in payment.allocations]

                # 引き落とし日の差を計算
                if current_card and recommended_cards:
                    recommended_card = recommended_cards[0]  # 最初の推奨カード

                    # 簡易計算: 支払猶予の差
                    grace_diff = recommended_card.grace_period_days - current_card.grace_period_days

                    if grace_diff > 0:
                        lines.append(f"\n### {payment.name}")
                        lines.append(f"**金額**: {payment.amount:,}円")
                        lines.append(f"- **現在**: {current_card.name} (猶予{current_card.grace_period_days}日)")
                        lines.append(f"- **推奨**: {recommended_card.name} (猶予{recommended_card.grace_period_days}日)")
                        lines.append(f"- **メリット**: 切り替えで**{grace_diff}日**支払いが遅くなります")

        if not lines:
            lines.append("切り替え推奨なし（すべて最適なカードを使用中）")

        return lines

    def _generate_action_list(self) -> List[str]:
        """アクションリストを生成"""
        lines = []

        # 請求書カード払いの申請日を集計
        actions = []
        for payment in self.payments:
            if payment.application_date and payment.allocations:
                for alloc in payment.allocations:
                    actions.append({
                        'date': payment.application_date,
                        'payment': payment.name,
                        'card': alloc['card'].name,
                        'amount': alloc['amount']
                    })

        # 日付順にソート
        actions.sort(key=lambda x: x['date'])

        # 日付ごとにグループ化
        from itertools import groupby
        for date, group in groupby(actions, key=lambda x: x['date']):
            lines.append(f"\n### {date}")
            for action in group:
                lines.append(f"- [ ] **{action['payment']}**を{action['card']}で申請（{action['amount']:,}円）")

        if not lines:
            lines.append("申請予定なし")

        return lines

    def _generate_withdrawal_schedule(self) -> List[str]:
        """引き落としスケジュールを生成"""
        lines = []

        # カードごとの引き落とし情報を集計
        withdrawals = {}

        for payment in self.payments:
            for alloc in payment.allocations:
                card = alloc['card']
                amount = alloc['amount']

                # 引き落とし月・日を計算（簡易版: 実際の締め日・決済日は考慮しない）
                withdrawal_month = self.target_month + card.payment_month_offset
                withdrawal_year = self.target_year
                if withdrawal_month > 12:
                    withdrawal_month -= 12
                    withdrawal_year += 1

                withdrawal_date = f"{withdrawal_year}/{withdrawal_month:02d}/{card.payment_day_offset:02d}"

                if withdrawal_date not in withdrawals:
                    withdrawals[withdrawal_date] = {}

                if card.name not in withdrawals[withdrawal_date]:
                    withdrawals[withdrawal_date][card.name] = {
                        'total': 0,
                        'items': []
                    }

                withdrawals[withdrawal_date][card.name]['total'] += amount
                withdrawals[withdrawal_date][card.name]['items'].append({
                    'payment': payment.name,
                    'amount': amount
                })

        # 日付順にソート
        for date in sorted(withdrawals.keys()):
            lines.append(f"\n### {date}")
            date_total = 0
            for card_name, info in withdrawals[date].items():
                lines.append(f"\n**{card_name}**: {info['total']:,}円")
                for item in info['items']:
                    lines.append(f"- {item['payment']}: {item['amount']:,}円")
                date_total += info['total']
            lines.append(f"\n**→ この日の合計: {date_total:,}円**")

        if not lines:
            lines.append("引き落とし予定なし")

        return lines

    def run(self):
        """最適化を実行"""
        self.calculate_grace_periods()
        self.load_payments()
        self.allocate_payments()
        return self.generate_report()


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/optimize_credit_schedule.py data/input_YYYYMM.yaml")
        sys.exit(1)

    # パス設定
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    master_data_path = project_dir / 'docs' / 'master-data-v2.yaml'
    input_data_path = Path(sys.argv[1])

    if not input_data_path.is_absolute():
        input_data_path = project_dir / input_data_path

    # 最適化実行
    optimizer = CreditCardOptimizer(master_data_path, input_data_path)
    report = optimizer.run()

    # レポート出力
    print(report)

    # ファイルにも保存
    output_path = project_dir / 'data' / f'optimization_result_{optimizer.target_year}{optimizer.target_month:02d}.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nレポートを保存しました: {output_path}")


if __name__ == '__main__':
    main()
