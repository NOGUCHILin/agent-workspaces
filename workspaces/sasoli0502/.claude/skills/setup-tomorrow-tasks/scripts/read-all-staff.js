/**
 * シフト表の全スタッフ名を取得
 */

const SPREADSHEET_ID = '17j75NtzOjnDDc8ffr2nQzTmw5tU_nLm0h5pGGvIB0OA';
const SHEET_GID = '567968742';

async function fetchAllStaff() {
  const csvUrl = `https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/export?format=csv&gid=${SHEET_GID}`;

  const response = await fetch(csvUrl);
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  const csvText = await response.text();
  const lines = csvText.split('\n');

  // CSVパース
  const rows = lines.map(line => {
    return line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''));
  });

  console.log('=== 全スタッフ名（A列）===\n');

  // 行1から40まで表示
  for (let i = 0; i < Math.min(rows.length, 40); i++) {
    const row = rows[i];
    const cellA = row[0] || '(空白)';
    console.log(`行${i + 1}: ${cellA}`);
  }

  console.log('\n=== 23日（列X, インデックス24）の全データ ===\n');

  // 23日の列（インデックス24）の全データ
  for (let i = 0; i < Math.min(rows.length, 40); i++) {
    const row = rows[i];
    const cellA = row[0] || '(空白)';
    const cellX = row[24] || '(空白)';
    console.log(`行${i + 1}: ${cellA} → ${cellX}`);
  }
}

fetchAllStaff().catch(console.error);
