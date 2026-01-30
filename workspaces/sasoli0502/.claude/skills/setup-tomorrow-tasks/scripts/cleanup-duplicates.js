/**
 * 重複タスク削除スクリプト
 *
 * 裏/レ関連タスクの重複を削除し、1つだけ残して担当者を空にする
 */

const NOTION_TOKEN = process.env.NOTION_TOKEN || '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';
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

// 裏/レ関連のタスク名
const URA_TASKS = [
  '査定',
  '査定商品開封',
  '査定商品アクティベーション',
  '出品(バックマーケット)',
  '出品（バックマーケット）',
  '出品(結び)',
  '出品（結び）',
  '商品撮影(結び)',
  '商品撮影（結び）'
];

// Notion API呼び出し
async function notionFetch(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${NOTION_TOKEN}`,
      'Content-Type': 'application/json',
      'Notion-Version': '2022-06-28'
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`https://api.notion.com/v1${endpoint}`, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Notion API error: ${response.status} - ${errorText}`);
  }

  return response.json();
}

// 特定の日付のタスクを取得
async function getTasksByDate(date) {
  const response = await notionFetch(`/databases/${NOTION_DATABASE_ID}/query`, 'POST', {
    filter: {
      property: '日付',
      date: {
        equals: date
      }
    }
  });

  return response.results;
}

// ページをアーカイブ（削除）
async function archivePage(pageId) {
  return notionFetch(`/pages/${pageId}`, 'PATCH', {
    archived: true
  });
}

// ページの担当者を空にする
async function clearAssignee(pageId) {
  return notionFetch(`/pages/${pageId}`, 'PATCH', {
    properties: {
      '担当者': {
        people: []
      }
    }
  });
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
  console.log('');

  try {
    // タスクを取得
    console.log('タスクを取得中...');
    const tasks = await getTasksByDate(targetDate);
    console.log(`${tasks.length}件のタスクを取得`);
    console.log('');

    // 裏/レ関連タスクを抽出してグループ化
    const uraTaskGroups = {};

    for (const task of tasks) {
      const title = task.properties?.['名前']?.title?.[0]?.plain_text ||
                    task.properties?.['タスク名']?.title?.[0]?.plain_text || '';

      // 裏/レ関連タスクかチェック
      const matchedTaskName = URA_TASKS.find(name => title.includes(name));
      if (matchedTaskName) {
        // 正規化したタスク名でグループ化（半角・全角括弧の違いを吸収）
        const normalizedName = matchedTaskName
          .replace('（', '(')
          .replace('）', ')');

        if (!uraTaskGroups[normalizedName]) {
          uraTaskGroups[normalizedName] = [];
        }
        uraTaskGroups[normalizedName].push(task);
      }
    }

    console.log('裏/レ関連タスクの重複状況:');
    for (const [name, group] of Object.entries(uraTaskGroups)) {
      console.log(`  ${name}: ${group.length}件`);
    }
    console.log('');

    // 重複を削除
    let deletedCount = 0;
    let keptCount = 0;

    for (const [name, group] of Object.entries(uraTaskGroups)) {
      if (group.length <= 1) {
        console.log(`${name}: 重複なし`);
        if (group.length === 1) {
          // 担当者を空にする
          await clearAssignee(group[0].id);
          console.log(`  → 担当者をクリア`);
          keptCount++;
        }
        continue;
      }

      console.log(`${name}: ${group.length}件 → 1件に削減`);

      // 最初の1件を残す（担当者を空にする）
      const keepTask = group[0];
      await clearAssignee(keepTask.id);
      console.log(`  → 保持: ${keepTask.id} (担当者クリア)`);
      keptCount++;

      // 残りを削除
      for (let i = 1; i < group.length; i++) {
        try {
          await archivePage(group[i].id);
          console.log(`  → 削除: ${group[i].id}`);
          deletedCount++;
        } catch (error) {
          console.log(`  → 削除失敗: ${group[i].id}: ${error.message}`);
        }
      }
    }

    console.log('');
    console.log(`完了: ${deletedCount}件削除, ${keptCount}件保持（担当者クリア済み）`);

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  }
}

main();
