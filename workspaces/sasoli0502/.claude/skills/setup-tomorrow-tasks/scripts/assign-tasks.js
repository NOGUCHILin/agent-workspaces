/**
 * setup-tomorrow-tasks 自動担当者割り当てスクリプト
 *
 * シフト表を読み取り、Notionタスクに担当者を自動設定する
 */

const NOTION_TOKEN = process.env.NOTION_TOKEN || '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';
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

// タスクと役割の対応マッピング
const ROLE_TASK_MAPPING = {
  // ネコポス担当・発送準備担当（シャ）
  'シャ': [
    '梱包キット作成',
    '発送商品伝票貼付',
    '発送商品伝票貼付(バックマーケット)',
    '商品伝票貼付(バックマーケット)',
    '発送',
    '商品梱包',
    'BM在庫チェック',
    '梱包キット請求情報確認',
    '在庫管理(梱包資材)',
    '新品買取価格変更',
    '新品未開封確認',
    '整理整頓'
  ],
  // 電話番
  '電話番': [
    'カスタマー対応(電話)'
  ],
  // 店（店舗担当）
  '店': [
    'カスタマー対応（LINEとメール）',
    '買取カスタマー対応(LINE)',
    '買取カスタマー対応(メール)',
    '買取ユーザー対応',
    '買取支払い処理',
    '買取促進',
    '販売カスタマー対応（バックマーケット）',
    '販売カスタマー対応(バックマーケット)',
    '販売カスタマー対応(ムスビー)',
    '結び',
    '発送完了連絡ダブルチェック',
    '発送完了連絡用ファイル作成',
    '発送商品IMEI入力',
    '発送商品進捗変更',
    '店頭査定',
    '店頭修理お渡し',
    '店頭修理受付',
    '店頭買取',
    '店舗準備'
  ],
  // 裏/レ（査定・出品担当）- 複数人対応
  '裏': [
    '査定',
    '査定商品開封',
    '査定商品アクティベーション',
    '買取商品仕分け',
    '出品(バックマーケット)',
    '出品（バックマーケット）',
    '出品(ムスビー)',
    '出品（ムスビー）',
    '商品撮影(ムスビー)',
    '商品撮影（ムスビー）'
  ],
  // 修理担当（雑賀晴士・高橋諒がいる場合のみ）- 複数人対応
  '修理': [
    '修理(販売商品)',
    '修理（販売商品）',
    '修理(査定商品)',
    '修理（査定商品）',
    '在庫管理(修理パーツ)',
    '在庫管理（修理パーツ）'
  ],
  // 品質管理担当（佐々木悠斗のみ）
  '品質管理': [
    '品質管理'
  ]
};

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

// データベースのユーザー一覧を取得
async function getNotionUsers() {
  const result = await notionFetch('/users');
  return result.results;
}

// 明日の日付を取得 (YYYY-MM-DD形式)
function getTomorrowDate() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return tomorrow.toISOString().split('T')[0];
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

// ページ（タスク）を更新
async function updateTaskAssignee(pageId, userId) {
  return notionFetch(`/pages/${pageId}`, 'PATCH', {
    properties: {
      '担当者': {
        people: [{ id: userId }]
      }
    }
  });
}

// タスクを複製して新しい担当者を設定
async function duplicateTaskWithAssignee(task, userId, databaseId) {
  // 元のタスクのプロパティをコピー
  const properties = {};

  // 名前をコピー
  if (task.properties['名前']?.title) {
    properties['名前'] = { title: task.properties['名前'].title };
  }

  // 日付をコピー
  if (task.properties['日付']?.date) {
    properties['日付'] = { date: task.properties['日付'].date };
  }

  // 担当者を設定
  properties['担当者'] = { people: [{ id: userId }] };

  // 新しいページを作成
  return notionFetch('/pages', 'POST', {
    parent: { database_id: databaseId },
    properties: properties
  });
}

// タスク名でマッチング（部分一致）- 担当者未設定のタスクのみ
function findMatchingTasks(tasks, taskNames, onlyUnassigned = false) {
  return tasks.filter(task => {
    const title = task.properties?.['名前']?.title?.[0]?.plain_text ||
                  task.properties?.['タスク名']?.title?.[0]?.plain_text || '';
    const hasAssignee = task.properties?.['担当者']?.people?.length > 0;

    // 担当者未設定のみ対象にする場合
    if (onlyUnassigned && hasAssignee) {
      return false;
    }

    return taskNames.some(name => title.includes(name));
  });
}

// ユーザー名でユーザーIDを検索
function findUserByName(users, name) {
  return users.find(user =>
    user.name?.includes(name) || name.includes(user.name || '')
  );
}

// メイン処理
async function main() {
  const args = process.argv.slice(2);

  // コマンドライン引数の解析
  // 使用例: node assign-tasks.js --sha "名前" --denwa "名前" --mise "名前" --ura "名前1,名前2"
  const assignments = {
    'シャ': null,
    '電話番': null,
    '店': null,
    '裏': null,  // 複数人対応（カンマ区切り）
    '修理': null,  // 複数人対応（雑賀晴士・高橋諒のみ）
    '品質管理': null  // 佐々木悠斗のみ
  };

  for (let i = 0; i < args.length; i += 2) {
    const flag = args[i];
    const value = args[i + 1];

    if (flag === '--sha' && value) {
      assignments['シャ'] = value;
    } else if (flag === '--denwa' && value) {
      assignments['電話番'] = value;
    } else if (flag === '--mise' && value) {
      assignments['店'] = value;
    } else if (flag === '--ura' && value) {
      assignments['裏'] = value;  // カンマ区切りで複数人指定可能
    } else if (flag === '--shuri' && value) {
      assignments['修理'] = value;  // カンマ区切りで複数人指定可能（雑賀晴士・高橋諒のみ）
    } else if (flag === '--hinshitsu' && value) {
      assignments['品質管理'] = value;  // 佐々木悠斗のみ
    } else if (flag === '--date') {
      // カスタム日付指定
    } else if (flag === '--help') {
      console.log(`
使用方法:
  node assign-tasks.js [オプション]

オプション:
  --sha <名前>        ネコポス担当・発送準備担当を指定
  --denwa <名前>      電話番を指定
  --mise <名前>       店舗担当を指定
  --ura <名前>        裏/レ担当を指定（カンマ区切りで複数人可）
  --shuri <名前>      修理担当を指定（カンマ区切りで複数人可、雑賀晴士・高橋諒のみ）
  --hinshitsu <名前>  品質管理担当を指定（佐々木悠斗のみ）
  --date <日付>       対象日付 (YYYY-MM-DD形式、省略時は明日)
  --help              このヘルプを表示

例:
  node assign-tasks.js --sha "ナンユンティリゾーウー" --denwa "野口サラ" --mise "平山優大"
  node assign-tasks.js --ura "細谷尚央,江口那都" --date "2026-01-23"
  node assign-tasks.js --shuri "雑賀晴士,高橋諒" --date "2026-01-23"
  node assign-tasks.js --hinshitsu "佐々木悠斗" --date "2026-01-23"
`);
      return;
    }
  }

  // 日付を取得
  const dateArg = args.indexOf('--date');
  const targetDate = dateArg !== -1 && args[dateArg + 1]
    ? args[dateArg + 1]
    : getTomorrowDate();

  console.log(`対象日付: ${targetDate}`);
  console.log('担当者設定:', assignments);
  console.log('');

  try {
    // 1. Notionユーザー一覧を取得
    console.log('Notionユーザーを取得中...');
    const users = await getNotionUsers();
    console.log(`${users.length}人のユーザーを取得`);
    users.forEach(u => console.log(`  - ${u.name} (${u.id})`));
    console.log('');

    // 2. 各役割のタスクに担当者を設定
    let updatedCount = 0;

    for (const [role, assigneeName] of Object.entries(assignments)) {
      // 各役割の処理前にタスクを再取得（前の処理による変更を反映）
      const tasks = await getTasksByDate(targetDate);
      if (!assigneeName) {
        console.log(`${role}: 担当者未指定 - スキップ`);
        continue;
      }

      const taskNames = ROLE_TASK_MAPPING[role];

      // 裏/レ、修理役割は複製を行うため、担当者未設定のタスクのみを対象にする
      const onlyUnassigned = (role === '裏' || role === '修理');
      const matchingTasks = findMatchingTasks(tasks, taskNames, onlyUnassigned);

      // 複数人対応（カンマ区切り）- タスクを複製して各担当者に割り当て
      if (role === '裏' || role === '修理') {
        const names = assigneeName.split(',').map(n => n.trim());
        const foundUsers = [];

        // 修理担当の場合は雑賀晴士・高橋諒のみ許可
        const allowedRepairNames = ['雑賀晴士', '雑賀', '晴士', '高橋諒', '高橋', '諒'];

        for (const name of names) {
          // 修理担当の名前チェック
          if (role === '修理') {
            const isAllowed = allowedRepairNames.some(allowed =>
              name.includes(allowed) || allowed.includes(name)
            );
            if (!isAllowed) {
              console.log(`${role}: "${name}" は修理担当として設定できません（雑賀晴士・高橋諒のみ）- スキップ`);
              continue;
            }
          }

          const user = findUserByName(users, name);
          if (user) {
            foundUsers.push({ name, id: user.id });
          } else {
            console.log(`${role}: ユーザー "${name}" が見つかりません - スキップ`);
          }
        }

        if (foundUsers.length === 0) {
          console.log(`${role}: 有効なユーザーがいません - スキップ`);
          continue;
        }

        console.log(`${role}: 担当者未設定のタスク${matchingTasks.length}件を${foundUsers.length}人分複製中...`);

        for (const task of matchingTasks) {
          const title = task.properties?.['名前']?.title?.[0]?.plain_text ||
                        task.properties?.['タスク名']?.title?.[0]?.plain_text || '(無題)';

          // 最初の担当者は元のタスクを更新
          try {
            await updateTaskAssignee(task.id, foundUsers[0].id);
            console.log(`  ✓ ${title} → ${foundUsers[0].name}`);
            updatedCount++;
          } catch (error) {
            console.log(`  ✗ ${title} → ${foundUsers[0].name}: ${error.message}`);
          }

          // 2人目以降は複製して作成
          for (let i = 1; i < foundUsers.length; i++) {
            try {
              await duplicateTaskWithAssignee(task, foundUsers[i].id, NOTION_DATABASE_ID);
              console.log(`  ✓ ${title} → ${foundUsers[i].name} (複製)`);
              updatedCount++;
            } catch (error) {
              console.log(`  ✗ ${title} → ${foundUsers[i].name} (複製): ${error.message}`);
            }
          }
        }
      } else {
        // 単一担当者の場合

        // 品質管理担当の場合は佐々木悠斗のみ許可
        if (role === '品質管理') {
          const allowedQualityNames = ['佐々木悠斗', '佐々木', '悠斗'];
          const isAllowed = allowedQualityNames.some(allowed =>
            assigneeName.includes(allowed) || allowed.includes(assigneeName)
          );
          if (!isAllowed) {
            console.log(`${role}: "${assigneeName}" は品質管理担当として設定できません（佐々木悠斗のみ）- スキップ`);
            continue;
          }
        }

        const user = findUserByName(users, assigneeName);
        if (!user) {
          console.log(`${role}: ユーザー "${assigneeName}" が見つかりません - スキップ`);
          continue;
        }

        console.log(`${role} (${assigneeName}): ${matchingTasks.length}件のタスクを更新中...`);

        for (const task of matchingTasks) {
          const title = task.properties?.['名前']?.title?.[0]?.plain_text ||
                        task.properties?.['タスク名']?.title?.[0]?.plain_text || '(無題)';
          try {
            await updateTaskAssignee(task.id, user.id);
            console.log(`  ✓ ${title}`);
            updatedCount++;
          } catch (error) {
            console.log(`  ✗ ${title}: ${error.message}`);
          }
        }
      }
    }

    console.log('');
    console.log(`完了: ${updatedCount}件のタスクを更新しました`);

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  }
}

main();
