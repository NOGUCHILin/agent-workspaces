/**
 * 完全重複タスク削除スクリプト（ページネーション対応）
 *
 * 同じ名前のタスクが複数ある場合、1つだけ残して担当者を空にする
 */

const NOTION_TOKEN = process.env.NOTION_TOKEN || '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';
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

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

// 特定の日付の全タスクを取得（ページネーション対応）
async function getAllTasksByDate(date) {
  let allResults = [];
  let hasMore = true;
  let startCursor = undefined;

  while (hasMore) {
    const body = {
      filter: {
        property: '日付',
        date: {
          equals: date
        }
      },
      page_size: 100
    };

    if (startCursor) {
      body.start_cursor = startCursor;
    }

    const response = await notionFetch(`/databases/${NOTION_DATABASE_ID}/query`, 'POST', body);
    allResults = allResults.concat(response.results);
    hasMore = response.has_more;
    startCursor = response.next_cursor;
  }

  return allResults;
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
    // 全タスクを取得
    console.log('全タスクを取得中...');
    const tasks = await getAllTasksByDate(targetDate);
    console.log(`${tasks.length}件のタスクを取得`);
    console.log('');

    // タスクを名前でグループ化
    const taskGroups = {};

    for (const task of tasks) {
      const title = task.properties?.['名前']?.title?.[0]?.plain_text ||
                    task.properties?.['タスク名']?.title?.[0]?.plain_text || '(無題)';

      if (!taskGroups[title]) {
        taskGroups[title] = [];
      }
      taskGroups[title].push(task);
    }

    // 重複があるタスクを表示
    console.log('重複タスク:');
    let hasDuplicates = false;
    let totalDuplicates = 0;
    for (const [name, group] of Object.entries(taskGroups)) {
      if (group.length > 1) {
        console.log(`  ${name}: ${group.length}件`);
        hasDuplicates = true;
        totalDuplicates += group.length - 1;
      }
    }

    if (!hasDuplicates) {
      console.log('  重複なし');
      return;
    }
    console.log(`\n合計: ${totalDuplicates}件の重複を削除予定`);
    console.log('');

    // 重複を削除
    let deletedCount = 0;
    let keptCount = 0;

    for (const [name, group] of Object.entries(taskGroups)) {
      if (group.length <= 1) {
        continue;
      }

      process.stdout.write(`${name}: ${group.length}件 → 1件... `);

      // 最初の1件を残す（担当者を空にする）
      const keepTask = group[0];
      try {
        await clearAssignee(keepTask.id);
        keptCount++;
      } catch (error) {
        console.log(`保持失敗: ${error.message}`);
        continue;
      }

      // 残りを削除
      let localDeleted = 0;
      for (let i = 1; i < group.length; i++) {
        try {
          await archivePage(group[i].id);
          deletedCount++;
          localDeleted++;
        } catch (error) {
          console.log(`削除失敗: ${error.message}`);
        }
      }
      console.log(`${localDeleted}件削除`);
    }

    console.log('');
    console.log(`完了: ${deletedCount}件削除, ${keptCount}件保持（担当者クリア済み）`);

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  }
}

main();
