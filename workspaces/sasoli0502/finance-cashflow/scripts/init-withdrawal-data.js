// 初期引き落としデータを設定するスクリプト
// ブラウザのコンソールで実行してください

function initWithdrawalData() {
    const initialData = {
        // 2025-11-04 (火)
        '2025-11-04_toyota': 1366686,
        '2025-11-04_saison': 1693656,

        // 2025-11-10 (月)
        '2025-11-10_shinkin_visa': 1619160,
        '2025-11-10_shinkin_jcb': 878329,
        '2025-11-10_jfr': 0,
        '2025-11-10_amex': 2005301,

        // 2025-11-26 (水)
        '2025-11-26_amazon': 1015090,
        '2025-11-26_gpc': 36000,
        '2025-11-26_mi': 278019,

        // 2025-12-02 (火) - 暫定
        '2025-12-02_toyota': 10858
    };

    localStorage.setItem('withdrawalAmounts', JSON.stringify(initialData));
    console.log('✅ 初期データを設定しました');
    console.log('データ:', initialData);

    // ページをリロードして反映
    if (confirm('ページをリロードして反映しますか？')) {
        location.reload();
    }
}

// 実行
initWithdrawalData();
