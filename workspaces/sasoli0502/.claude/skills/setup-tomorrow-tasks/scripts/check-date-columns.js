/**
 * 日付列の確認
 */

const SPREADSHEET_ID = '17j75NtzOjnDDc8ffr2nQzTmw5tU_nLm0h5pGGvIB0OA';
const SHEET_GID = '567968742';

async function checkDateColumns() {
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

  console.log('=== 1行目（日付行）の全データ ===\n');

  const row1 = rows[0];
  for (let i = 0; i < row1.length; i++) {
    console.log(`列${i}: ${row1[i] || '(空白)'}`);
  }

  // 23日の列を探す
  console.log('\n=== 23日の列を検索 ===\n');

  let col23Index = -1;
  for (let i = 0; i < row1.length; i++) {
    if (row1[i] === '23日' || row1[i] === '23' || row1[i].includes('23')) {
      console.log(`23日候補: 列${i} = "${row1[i]}"`);
      if (row1[i] === '23日') {
        col23Index = i;
      }
    }
  }

  if (col23Index === -1) {
    console.log('23日の列が見つかりませんでした');
    return;
  }

  console.log(`\n23日の列インデックス: ${col23Index}`);
  console.log('\n=== 23日のシフトデータ ===\n');

  // 2行目は曜日
  console.log(`曜日: ${rows[1][col23Index]}`);

  // スタッフのシフト
  for (let i = 2; i < Math.min(rows.length, 40); i++) {
    const row = rows[i];
    const staffName = row[0];
    const assignment = row[col23Index];

    if (staffName && assignment) {
      console.log(`${staffName}: ${assignment}`);
    }
  }
}

checkDateColumns().catch(console.error);
