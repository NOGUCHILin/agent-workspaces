/**
 * Notionタスクのプロパティ構造を確認するスクリプト
 */

const NOTION_TOKEN = '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';
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

async function getAllTasksByDate(date) {
  let allResults = [];
  let hasMore = true;
  let startCursor = undefined;

  while (hasMore) {
    const body = {
      filter: { property: '日付', date: { equals: date } },
      page_size: 100
    };
    if (startCursor) body.start_cursor = startCursor;

    const response = await fetch(
      `https://api.notion.com/v1/databases/${NOTION_DATABASE_ID}/query`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${NOTION_TOKEN}`,
          'Content-Type': 'application/json',
          'Notion-Version': '2022-06-28'
        },
        body: JSON.stringify(body)
      }
    );
    const data = await response.json();
    if (data.results) allResults = allResults.concat(data.results);
    hasMore = data.has_more;
    startCursor = data.next_cursor;
  }
  return allResults;
}

async function main() {
  const date = process.argv[2] || '2026-01-24';
  console.log(`対象日付: ${date}\n`);

  const tasks = await getAllTasksByDate(date);

  // 「査定商品開封」タスクを1つ取得してプロパティを確認
  const sampleTask = tasks.find(t => {
    const name = t.properties?.['名前']?.title?.[0]?.plain_text || '';
    return name.includes('査定商品開封');
  });

  if (sampleTask) {
    console.log('=== 査定商品開封タスクのプロパティ一覧 ===\n');
    for (const [key, value] of Object.entries(sampleTask.properties)) {
      console.log(`【${key}】`);
      console.log(`  type: ${value.type}`);

      // 値を取得
      if (value.type === 'title') {
        console.log(`  value: ${value.title?.[0]?.plain_text}`);
      } else if (value.type === 'number') {
        console.log(`  value: ${value.number}`);
      } else if (value.type === 'people') {
        const names = value.people?.map(p => p.name).join(', ');
        console.log(`  value: ${names}`);
      } else if (value.type === 'date') {
        console.log(`  value: ${value.date?.start}`);
      } else if (value.type === 'select') {
        console.log(`  value: ${value.select?.name}`);
      } else if (value.type === 'rich_text') {
        console.log(`  value: ${value.rich_text?.[0]?.plain_text}`);
      } else {
        console.log(`  raw: (complex type)`);
      }
      console.log('');
    }
  } else {
    console.log('査定商品開封タスクが見つかりません');
  }
}

main();
