const NOTION_TOKEN = process.env.NOTION_TOKEN;
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

async function getAllTasksByDate(date) {
  let allResults = [];
  let hasMore = true;
  let startCursor = undefined;
  while (hasMore) {
    const body = { filter: { property: '日付', date: { equals: date } }, page_size: 100 };
    if (startCursor) body.start_cursor = startCursor;
    const response = await fetch('https://api.notion.com/v1/databases/' + NOTION_DATABASE_ID + '/query', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + NOTION_TOKEN, 'Content-Type': 'application/json', 'Notion-Version': '2022-06-28' },
      body: JSON.stringify(body)
    }).then(r => r.json());
    allResults = allResults.concat(response.results);
    hasMore = response.has_more;
    startCursor = response.next_cursor;
  }
  return allResults;
}

async function main() {
  const date = process.argv[2] || '2026-01-23';
  const tasks = await getAllTasksByDate(date);
  console.log(date + 'のタスク数:', tasks.length);
  console.log('');

  // タスク名の一覧を表示（重複カウント）
  const categories = {};
  tasks.forEach(task => {
    const title = task.properties?.['名前']?.title?.[0]?.plain_text || '(無題)';
    const assignee = task.properties?.['担当者']?.people?.[0]?.name || '未設定';
    const key = title;
    if (!categories[key]) categories[key] = { assigned: 0, unassigned: 0 };
    if (assignee === '未設定') {
      categories[key].unassigned++;
    } else {
      categories[key].assigned++;
    }
  });

  console.log('タスク一覧:');
  Object.entries(categories).sort().forEach(([name, count]) => {
    if (count.unassigned > 0 || count.assigned > 0) {
      console.log('  -', name, '(未設定:' + count.unassigned + ', 設定済:' + count.assigned + ')');
    }
  });
}

main();
