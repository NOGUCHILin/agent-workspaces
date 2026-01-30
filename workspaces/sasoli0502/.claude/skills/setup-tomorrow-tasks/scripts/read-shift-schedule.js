/**
 * シフト表読み取りスクリプト
 * Google Sheets APIを使ってシフトデータを取得
 */

const SPREADSHEET_ID = '17j75NtzOjnDDc8ffr2nQzTmw5tU_nLm0h5pGGvIB0OA';
const SHEET_GID = '567968742'; // 2026/1のシートID

// Google SheetsのデータをCSV形式でエクスポート
async function fetchShiftData(date) {
  // YYYY-MM-DD形式の日付から日にち（DD）を取得
  const day = parseInt(date.split('-')[2]);

  // CSVエクスポートURL（認証不要で公開されている場合）
  const csvUrl = `https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/export?format=csv&gid=${SHEET_GID}`;

  console.log(`シフト表を取得中: ${date} (${day}日)`);
  console.log(`URL: ${csvUrl}`);

  try {
    const response = await fetch(csvUrl);

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const csvText = await response.text();
    const lines = csvText.split('\n');

    // CSVパース
    const rows = lines.map(line => {
      // 簡易CSVパース（カンマ区切り）
      return line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''));
    });

    // 1行目：月
    // 2行目：曜日
    // 3行目以降：スタッフ名と各日の割り当て

    console.log('\n--- シフト表データ ---');
    console.log('行数:', rows.length);
    console.log('列数:', rows[0]?.length);

    // 日付の列を特定（1日=インデックス1、2日=インデックス2、...）
    // A列(0)=月名、B列(1)=1日、C列(2)=2日、...
    const dateColumnIndex = day; // day日はインデックスday

    console.log(`\n${day}日の列インデックス: ${dateColumnIndex}`);
    console.log('\nスタッフ割り当て:');

    const assignments = {
      staff: [],
      roles: {}
    };

    // 行3以降でスタッフ名と割り当てを取得
    for (let i = 2; i < Math.min(rows.length, 35); i++) {
      const row = rows[i];
      const staffName = row[0]; // A列：スタッフ名
      const assignment = row[dateColumnIndex]; // 対象日の割り当て

      if (staffName && assignment) {
        console.log(`  ${staffName}: ${assignment}`);
        assignments.staff.push({ name: staffName, role: assignment });
      }
    }

    // 役割の割り当て（行31-34付近）
    console.log('\n役割割り当て:');
    for (let i = 30; i < Math.min(rows.length, 35); i++) {
      const row = rows[i];
      const roleName = row[0]; // A列：役割名
      const assignee = row[dateColumnIndex]; // 対象日の担当者

      if (roleName && assignee) {
        console.log(`  ${roleName}: ${assignee}`);
        assignments.roles[roleName] = assignee;
      }
    }

    return assignments;

  } catch (error) {
    console.error('エラー:', error.message);
    throw error;
  }
}

// メイン処理
async function main() {
  const args = process.argv.slice(2);
  const dateArg = args.indexOf('--date');

  // 明日の日付をデフォルトに
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const targetDate = dateArg !== -1 && args[dateArg + 1]
    ? args[dateArg + 1]
    : tomorrow.toISOString().split('T')[0];

  console.log(`対象日付: ${targetDate}`);

  const data = await fetchShiftData(targetDate);

  console.log('\n=== 取得完了 ===');
  console.log(JSON.stringify(data, null, 2));
}

main();
