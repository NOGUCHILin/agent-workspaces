/**
 * 明日のタスク全削除スクリプト（一時的な使用）
 */

const NOTION_TOKEN = process.env.NOTION_TOKEN;
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

    if (tasks.length === 0) {
      console.log('削除対象タスクがありません');
      return;
    }

    console.log(`${tasks.length}件のタスクを全て削除します`);
    console.log('');

    // 削除実行
    let deletedCount = 0;
    for (const task of tasks) {
      const title = task.properties?.['名前']?.title?.[0]?.plain_text || '(無題)';
      try {
        await archivePage(task.id);
        deletedCount++;
        if (deletedCount % 10 === 0) {
          console.log(`削除中... ${deletedCount}/${tasks.length}`);
        }
      } catch (error) {
        console.log(`✗ ${title} の削除に失敗: ${error.message}`);
      }
    }

    console.log('');
    console.log(`完了: ${deletedCount}件のタスクを削除しました`);

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  }
}

main();
