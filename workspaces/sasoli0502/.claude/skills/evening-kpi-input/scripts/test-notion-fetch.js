/**
 * Notion APIからKPI用データを取得するテストスクリプト
 *
 * 取得対象:
 * - 査定商品開封 → AW列（到着数）
 * - 査定 → AY列（査定数）
 * - 修理(販売商品) → BY列（修理数）
 * - 出品(バックマーケット) → CB列（出品数・BM）
 * - 出品(ムスビー) → CV列（出品数・ムスビ）
 */

const NOTION_TOKEN = process.env.NOTION_TOKEN;
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

// KPI入力に必要なタスク名のマッピング
const KPI_TASK_MAPPING = {
  'AW': {  // 到着数
    column: 'AW',
    label: '到着数',
    taskNames: ['査定商品開封']
  },
  'AY': {  // 査定数
    column: 'AY',
    label: '査定数',
    taskNames: ['査定']  // 完全一致させるため
  },
  'BY': {  // 修理数
    column: 'BY',
    label: '修理数',
    taskNames: ['修理(販売商品)', '修理（販売商品）']
  },
  'CB': {  // 出品数（バックマーケット）
    column: 'CB',
    label: '出品数(BM)',
    taskNames: ['出品(バックマーケット)', '出品（バックマーケット）']
  },
  'CV': {  // 出品数（ムスビー）
    column: 'CV',
    label: '出品数(ムスビ)',
    taskNames: ['出品(ムスビー)', '出品（ムスビー）']  // 半角・全角両方対応
  }
};

// 特定の日付のタスクを全件取得（ページネーション対応）
async function getAllTasksByDate(date) {
  let allResults = [];
  let hasMore = true;
  let startCursor = undefined;

  while (hasMore) {
    const body = {
      filter: {
        property: '日付',
        date: { equals: date }
      },
      page_size: 100
    };

    if (startCursor) {
      body.start_cursor = startCursor;
    }

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

    if (data.results) {
      allResults = allResults.concat(data.results);
    }

    hasMore = data.has_more;
    startCursor = data.next_cursor;
  }

  return allResults;
}

// タスク名を取得（トリム処理を含む）
function getTaskName(task) {
  const name = task.properties?.['名前']?.title?.[0]?.plain_text || '';
  return name.trim();
}

// 担当者を取得
function getAssignees(task) {
  const people = task.properties?.['担当者']?.people || [];
  return people.map(p => p.name || '不明');
}

// 件数プロパティを取得
function getTaskCount(task) {
  return task.properties?.['件数']?.number || 0;
}

// KPIデータを集計（件数プロパティの合計）
function aggregateKPIData(tasks) {
  const results = {};

  for (const [column, config] of Object.entries(KPI_TASK_MAPPING)) {
    results[column] = {
      label: config.label,
      count: 0,
      details: []
    };

    for (const task of tasks) {
      const taskName = getTaskName(task);

      // 完全一致チェック（全てのタスク名で完全一致を使用）
      const isMatch = config.taskNames.some(name => taskName === name);

      if (isMatch) {
        const assignees = getAssignees(task);
        const taskCount = getTaskCount(task);  // 件数プロパティを取得

        // 担当者が設定されている場合のみカウント
        if (assignees.length > 0 && assignees[0] !== '不明') {
          results[column].count += taskCount;  // 件数を合計
          results[column].details.push({
            task: taskName,
            assignees: assignees,
            count: taskCount  // 個別の件数も記録
          });
        }
      }
    }
  }

  return results;
}

// メイン処理
async function main() {
  const date = process.argv[2] || new Date().toISOString().split('T')[0];

  console.log(`\n===== Notion KPIデータ取得テスト =====`);
  console.log(`対象日付: ${date}\n`);

  try {
    // タスク取得
    console.log('Notionからタスクを取得中...');
    const tasks = await getAllTasksByDate(date);
    console.log(`取得したタスク数: ${tasks.length}件\n`);

    // デバッグ: 全タスク名を出力
    if (process.argv.includes('--debug')) {
      console.log('--- 全タスク名一覧 ---');
      const taskNames = new Set();
      tasks.forEach(task => {
        const name = getTaskName(task);
        if (name) taskNames.add(name);
      });
      Array.from(taskNames).sort().forEach(name => {
        console.log(`  "${name}"`);
      });
      console.log('');
    }

    // KPIデータ集計
    console.log('--- KPIデータ集計結果 ---\n');
    const kpiData = aggregateKPIData(tasks);

    for (const [column, data] of Object.entries(kpiData)) {
      console.log(`${column}列 (${data.label}): ${data.count}件`);
      if (data.details.length > 0) {
        data.details.forEach(d => {
          console.log(`  - ${d.task} [${d.assignees.join(', ')}]: ${d.count}件`);
        });
      }
      console.log('');
    }

    // JSON出力（スクリプト連携用）
    console.log('--- JSON出力 ---');
    const output = {};
    for (const [column, data] of Object.entries(kpiData)) {
      output[column] = data.count;
    }
    console.log(JSON.stringify(output, null, 2));

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  }
}

main();
