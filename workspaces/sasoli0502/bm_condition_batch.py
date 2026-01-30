"""
Back Market BMコンディション一括更新スクリプト

フロー:
1. Google Sheets APIでBMコンディション未入力のレコード一覧取得
2. Back Market APIで各レコードのSKU検索→コンディション取得
3. Kintone REST APIでBMコンディションを更新
"""

import json
import sys
import time
import base64
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ===== 設定 =====
BASE_DIR = Path(__file__).parent
BM_SESSION_PATH = BASE_DIR / "auth" / "backmarket_session.json"
KINTONE_APP_ID = 11
KINTONE_LOGIN = "noguchisara@japanconsulting.co.jp"
KINTONE_PASS = "4126uprose"
KINTONE_BASE = "https://japanconsulting.cybozu.com"

# SKUサフィックスの4バリエーション
SKU_SUFFIXES = ["s", "S", "\uff53", "\uff33"]  # s, S, ｓ, Ｓ

# 処理対象レコード (338613は処理済みなので除外)
RECORDS_TO_PROCESS = [
    "338469", "338354", "337761", "337737", "337736", "337735",
    "337186", "337100", "336996", "336428", "335903", "335713",
    "335506", "335348", "334967", "334879", "334815", "334747",
    "334733", "334554", "334107", "333276", "332848", "332595",
    "330860", "330802", "330689", "330631", "330540", "330431",
    "330310", "330259", "330254", "330101", "330051", "329942",
    "329432", "329331", "329234", "328596", "328136", "327559",
    "325632", "324907", "321721", "318016", "312276", "298420",
    "297161", "294276", "289205", "288191"
]

sys.stdout.reconfigure(encoding='utf-8')


def search_bm_order(page, record_num):
    """Back MarketでSKU検索し、注文IDを返す"""
    for suffix in SKU_SUFFIXES:
        sku = f"{record_num}{suffix}"
        url = f"https://www.backmarket.co.jp/bm/merchants/orders?page=1&pageSize=10&endDate=2026-01-29&sku={sku}"
        try:
            resp = page.evaluate(f"""async () => {{
                const r = await fetch('{url}');
                return await r.json();
            }}""")
            if resp and resp.get("count", 0) > 0:
                results = resp.get("results", [])
                if results:
                    order_id = results[0]["id"]
                    found_sku = sku
                    return order_id, found_sku
        except Exception as e:
            print(f"  [WARN] SKU {sku} search error: {e}")
            continue
    return None, None


def get_bm_condition(page, order_id):
    """注文詳細からコンディション(gradeラベル)を取得"""
    url = f"https://www.backmarket.co.jp/bm/merchants/orders/{order_id}"
    try:
        resp = page.evaluate(f"""async () => {{
            const r = await fetch('{url}');
            return await r.json();
        }}""")
        order_lines = resp.get("orderLines", [])
        if order_lines:
            grade = order_lines[0].get("grade", {})
            appearance = order_lines[0].get("appearance", {})
            grade_label = grade.get("label", "")
            appearance_label = appearance.get("label", "")
            # gradeラベルを優先して返す
            return grade_label or appearance_label
    except Exception as e:
        print(f"  [WARN] Order {order_id} detail error: {e}")
    return None


def update_kintone(record_num, condition):
    """KintoneのBMコンディションフィールドを更新"""
    auth = base64.b64encode(f"{KINTONE_LOGIN}:{KINTONE_PASS}".encode()).decode()
    headers = {
        "X-Cybozu-Authorization": auth,
        "Content-Type": "application/json"
    }
    payload = {
        "app": KINTONE_APP_ID,
        "id": int(record_num),
        "record": {
            "BackMarketコンディション": {
                "value": condition
            }
        }
    }
    resp = requests.put(
        f"{KINTONE_BASE}/k/v1/record.json",
        headers=headers,
        json=payload
    )
    return resp.status_code == 200, resp.text


def main():
    print(f"=== BMコンディション一括更新 ===")
    print(f"対象レコード数: {len(RECORDS_TO_PROCESS)}")
    print()

    # 結果集計
    success_list = []
    not_found_list = []
    error_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Back Marketセッション読込
        session_path = str(BM_SESSION_PATH)
        if not BM_SESSION_PATH.exists():
            print("[ERROR] Back Marketセッションファイルが見つかりません")
            return

        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        # Back Marketページにアクセスしてセッションを有効化
        page.goto("https://www.backmarket.co.jp/bo-seller/orders/all", wait_until="domcontentloaded")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)  # セッション確認のため少し待機

        for i, record_num in enumerate(RECORDS_TO_PROCESS):
            print(f"[{i+1}/{len(RECORDS_TO_PROCESS)}] レコード {record_num}...", end=" ", flush=True)

            # Step 1: Back MarketでSKU検索
            order_id, found_sku = search_bm_order(page, record_num)

            if order_id is None:
                print("→ BM注文なし (SKU該当なし)")
                not_found_list.append(record_num)
                continue

            # Step 2: 注文詳細からコンディション取得
            condition = get_bm_condition(page, order_id)

            if not condition:
                print(f"→ 注文{order_id}見つかったがコンディション取得失敗")
                error_list.append((record_num, f"order {order_id} - no condition"))
                continue

            # Step 3: Kintone更新
            ok, resp_text = update_kintone(record_num, condition)

            if ok:
                print(f"→ {condition} (SKU: {found_sku}, 注文: {order_id}) ✓ Kintone更新済み")
                success_list.append((record_num, condition, found_sku, order_id))
            else:
                print(f"→ {condition} 取得成功, Kintone更新失敗: {resp_text}")
                error_list.append((record_num, f"Kintone update failed: {resp_text}"))

            # API負荷軽減
            time.sleep(0.5)

        browser.close()

    # ===== 結果サマリー =====
    print()
    print("=" * 60)
    print(f"=== 処理完了 ===")
    print(f"成功: {len(success_list)}件")
    print(f"BM注文なし: {len(not_found_list)}件")
    print(f"エラー: {len(error_list)}件")
    print()

    if success_list:
        print("--- 成功一覧 ---")
        for rec, cond, sku, oid in success_list:
            print(f"  {rec}: {cond} (SKU: {sku})")

    if not_found_list:
        print()
        print("--- BM注文なし (SKU該当なし) ---")
        for rec in not_found_list:
            print(f"  {rec}")

    if error_list:
        print()
        print("--- エラー ---")
        for rec, err in error_list:
            print(f"  {rec}: {err}")

    # 結果をJSONファイルに保存
    result = {
        "success": [{"record": r, "condition": c, "sku": s, "order_id": o} for r, c, s, o in success_list],
        "not_found": not_found_list,
        "errors": [{"record": r, "error": e} for r, e in error_list]
    }
    result_path = BASE_DIR / "bm_condition_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n結果保存先: {result_path}")


if __name__ == "__main__":
    main()
