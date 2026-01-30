/**
 * クリーンスレート方式タスク作成スクリプト
 *
 * 1. 対象日の既存タスクを全削除
 * 2. テンプレートから新規作成（担当者設定済み）
 */

const NOTION_TOKEN = process.env.NOTION_TOKEN;
const NOTION_DATABASE_ID = '16983ea4-7788-80b0-b834-c5d077724297';

// ========== タスクテンプレート ==========
// 役割ごとのタスク定義

const TASK_TEMPLATES = {
  // 発送準備担当（ネコポス担当）
  '発送準備': [
    '梱包キット作成',
    '梱包キット請求情報確認',
    '発送',
    '商品伝票貼付(バックマーケット)',
    '商品梱包(バックマーケット)',
    'BM在庫チェック',
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
    '買取カスタマー対応(LINE)',
    '買取カスタマー対応(メール)',
    '買取ユーザー対応',
    '買取支払い処理',
    '買取促進',
    '販売カスタマー対応(バックマーケット)',
    '販売カスタマー対応(ムスビー)',
    '発送完了連絡ダブルチェック(バックマーケット)',
    '発送完了連絡用ファイル作成(バックマーケット)',
    '発送商品IMEI入力(バックマーケット)',
    '発送商品進捗変更(バックマーケット)',
    '店頭査定',
    '店頭修理お渡し',
    '店頭修理受付',
    '店頭買取',
    '店舗準備'
  ],

  // 裏（査定・出品担当）- 複数人に複製
  '裏': [
    '査定',
    '査定商品開封',
    '査定商品アクティベーション',
    '買取商品仕分け',
    '出品(バックマーケット)',
    '出品(ムスビー) ',
    '商品撮影(ムスビー) '
  ],

  // 修理担当（雑賀晴士・高橋諒のみ）- 複数人に複製
  '修理': [
    '修理(販売商品)',
    '修理(査定商品)',
    '在庫管理(修理パーツ)'
  ],

  // 品質管理（佐々木悠斗のみ）
  '品質管理': [
    '品質管理'
  ],

  // 担当者なし（その他）
  'なし': [
    '割れパネル販売',
    '買取価格変更'
  ]
};

// 削除対象タスク（作成しない）
const EXCLUDED_TASKS = [
  'BM販売価格変更',
  '座席分担',
  '在庫管理棚卸'
];

// 修理担当として許可される名前（この2人のみ修理タスクを担当可能）
const REPAIR_STAFF = ['雑賀晴士', '高橋諒'];
const ALLOWED_REPAIR_NAMES = ['雑賀晴士', '雑賀', '晴士', '高橋諒', '高橋', '諒'];

// 品質管理担当として許可される名前
const ALLOWED_QUALITY_NAMES = ['佐々木悠斗', '佐々木', '悠斗'];

// シフト表→Notion名前マッピング
const NAME_MAPPING = {
  // 旧字体・表記揺れ
  '雜賀晴士': '雑賀晴士',
  '雜賀 晴士': '雑賀晴士',
  // ひらがな表記
  '野口創': 'のぐち そう',
  '野口 創': 'のぐち そう',
  // 英語→カタカナ（外国人スタッフ）
  'NANT YOON': 'ナンユンティリゾーウー',
  'NANTYOON': 'ナンユンティリゾーウー',
  'THIRI ZAW OO': 'ナンユンティリゾーウー',  // 同一人物の場合
  'THIRIZAWOO': 'ナンユンティリゾーウー',
  'SADEGH MEHRSHAD': 'サデグメフルシャード',
  'SADEGHMEHRSHAD': 'サデグメフルシャード',
  // メールアドレス表記
  '本間久隆': 'honmahisataka@japanconsulting.co.jp',
  '本間 久隆': 'honmahisataka@japanconsulting.co.jp',
  // シフト表の略称
  'シャ': 'ナンユンティリゾーウー',
  '細': '細谷尚央',
  '原': '原紅映',
  '江': '江口那都',
  'メ': 'サデグメフルシャード'
};

// 名前の正規化（旧字体→新字体、マッピング適用）
function normalizeName(name) {
  // まずスペース除去せずにマッピングを確認
  if (NAME_MAPPING[name]) {
    return NAME_MAPPING[name];
  }

  // スペース除去版でマッピング確認
  const noSpace = name.replace(/\s+/g, '');
  if (NAME_MAPPING[noSpace]) {
    return NAME_MAPPING[noSpace];
  }

  // 旧字体変換
  const normalized = name
    .replace(/雜/g, '雑')
    .replace(/\s+/g, '');

  if (NAME_MAPPING[normalized]) {
    return NAME_MAPPING[normalized];
  }

  return normalized;
}

// ========== Notion API ==========

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

// ユーザー一覧取得
async function getNotionUsers() {
  const result = await notionFetch('/users');
  return result.results;
}

// 日付でタスク取得（ページネーション対応）
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

    const response = await notionFetch(`/databases/${NOTION_DATABASE_ID}/query`, 'POST', body);
    allResults = allResults.concat(response.results);
    hasMore = response.has_more;
    startCursor = response.next_cursor;
  }

  return allResults;
}

// タスク削除（アーカイブ）
async function archiveTask(pageId) {
  return notionFetch(`/pages/${pageId}`, 'PATCH', { archived: true });
}

// タスク作成
async function createTask(name, date, userId = null) {
  const properties = {
    '名前': { title: [{ text: { content: name } }] },
    '日付': { date: { start: date } }
  };

  if (userId) {
    properties['担当者'] = { people: [{ id: userId }] };
  }

  return notionFetch('/pages', 'POST', {
    parent: { database_id: NOTION_DATABASE_ID },
    properties
  });
}

// ユーザー名でユーザーを検索
function findUserByName(users, name) {
  return users.find(user =>
    user.name?.includes(name) || name.includes(user.name || '')
  );
}

// 明日の日付を取得
function getTomorrowDate() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return tomorrow.toISOString().split('T')[0];
}

// ========== メイン処理 ==========

async function main() {
  const args = process.argv.slice(2);

  // ヘルプ表示
  if (args.includes('--help')) {
    console.log(`
使用方法:
  node create-tasks.js [オプション]

オプション:
  --hassou <名前>     発送準備担当（ネコポス担当）を指定
  --denwa <名前>      電話番を指定
  --mise <名前>       店舗担当を指定
  --ura <名前>        裏/レ担当を指定（カンマ区切りで複数人可）
  --hinshitsu <名前>  品質管理担当を指定（佐々木悠斗のみ）
  --date <日付>       対象日付 (YYYY-MM-DD形式、省略時は明日)
  --dry-run           実際には実行せず、何が行われるか表示
  --help              このヘルプを表示

※修理担当は自動検出: 裏担当の中から雑賀晴士・高橋諒がいれば自動的に修理タスクにも設定

例:
  node create-tasks.js --hassou "細谷尚央" --denwa "原紅映" --mise "雑賀晴士"
  node create-tasks.js --ura "江口那都,野口器,高橋諒" --date "2026-01-25"
`);
    return;
  }

  // 引数解析
  const assignments = {
    '発送準備': null,
    '電話番': null,
    '店': null,
    '裏': [],    // 複数人対応
    '修理': [],  // 自動検出
    '品質管理': null
  };

  let targetDate = getTomorrowDate();
  let dryRun = false;

  for (let i = 0; i < args.length; i++) {
    const flag = args[i];
    const value = args[i + 1];

    switch (flag) {
      case '--hassou': assignments['発送準備'] = normalizeName(value); i++; break;
      case '--denwa': assignments['電話番'] = normalizeName(value); i++; break;
      case '--mise': assignments['店'] = normalizeName(value); i++; break;
      case '--ura':
        assignments['裏'] = value.split(',').map(n => normalizeName(n.trim()));
        i++;
        break;
      case '--hinshitsu': assignments['品質管理'] = normalizeName(value); i++; break;
      case '--date': targetDate = value; i++; break;
      case '--dry-run': dryRun = true; break;
    }
  }

  // 修理担当を自動検出（裏担当の中から雑賀晴士・高橋諒を抽出）
  const allStaff = [
    assignments['発送準備'],
    assignments['電話番'],
    assignments['店'],
    ...assignments['裏']
  ].filter(Boolean);

  for (const staff of allStaff) {
    for (const repairStaff of REPAIR_STAFF) {
      if (staff.includes(repairStaff) || repairStaff.includes(staff)) {
        if (!assignments['修理'].includes(staff)) {
          assignments['修理'].push(staff);
        }
      }
    }
  }

  console.log('========================================');
  console.log('クリーンスレート方式タスク作成');
  console.log('========================================');
  console.log(`対象日付: ${targetDate}`);
  console.log(`ドライラン: ${dryRun ? 'はい' : 'いいえ'}`);
  console.log('');
  console.log('担当者設定:');
  console.log(`  発送準備: ${assignments['発送準備'] || '未指定'}`);
  console.log(`  電話番: ${assignments['電話番'] || '未指定'}`);
  console.log(`  店: ${assignments['店'] || '未指定'}`);
  console.log(`  裏: ${assignments['裏'].length > 0 ? assignments['裏'].join(', ') : '未指定'}`);
  console.log(`  修理: ${assignments['修理'].length > 0 ? assignments['修理'].join(', ') + ' (自動検出)' : 'なし'}`);
  console.log(`  品質管理: ${assignments['品質管理'] || '未指定'}`);
  console.log('');

  try {
    // 1. Notionユーザー一覧を取得
    console.log('Step 1: Notionユーザーを取得中...');
    const users = await getNotionUsers();
    console.log(`  ${users.length}人のユーザーを取得`);

    // ユーザーIDを解決
    const userIds = {};
    for (const [role, name] of Object.entries(assignments)) {
      if (role === '裏' || role === '修理') {
        // 複数人対応
        userIds[role] = [];
        for (const n of name) {
          // 修理担当の名前チェック
          if (role === '修理') {
            const isAllowed = ALLOWED_REPAIR_NAMES.some(a => n.includes(a) || a.includes(n));
            if (!isAllowed) {
              console.log(`  警告: "${n}" は修理担当として設定できません`);
              continue;
            }
          }
          const user = findUserByName(users, n);
          if (user) {
            userIds[role].push({ name: n, id: user.id });
          } else if (n) {
            console.log(`  警告: ユーザー "${n}" が見つかりません`);
          }
        }
      } else if (name) {
        // 品質管理の名前チェック
        if (role === '品質管理') {
          const isAllowed = ALLOWED_QUALITY_NAMES.some(a => name.includes(a) || a.includes(name));
          if (!isAllowed) {
            console.log(`  警告: "${name}" は品質管理担当として設定できません`);
            continue;
          }
        }
        const user = findUserByName(users, name);
        if (user) {
          userIds[role] = { name, id: user.id };
        } else {
          console.log(`  警告: ユーザー "${name}" が見つかりません`);
        }
      }
    }
    console.log('');

    // 2. 既存タスクを削除
    console.log('Step 2: 既存タスクを削除中...');
    const existingTasks = await getAllTasksByDate(targetDate);
    console.log(`  ${existingTasks.length}件の既存タスクを検出`);

    if (!dryRun) {
      let deletedCount = 0;
      for (const task of existingTasks) {
        try {
          await archiveTask(task.id);
          deletedCount++;
        } catch (error) {
          console.log(`  削除失敗: ${error.message}`);
        }
      }
      console.log(`  ${deletedCount}件を削除完了`);
    } else {
      console.log('  (ドライラン: 削除はスキップ)');
    }
    console.log('');

    // 3. 新規タスクを作成
    console.log('Step 3: 新規タスクを作成中...');
    let createdCount = 0;

    for (const [role, taskNames] of Object.entries(TASK_TEMPLATES)) {
      for (const taskName of taskNames) {
        // 除外タスクはスキップ
        if (EXCLUDED_TASKS.includes(taskName)) {
          continue;
        }

        if (role === '裏' || role === '修理') {
          // 複数人対応：各担当者ごとにタスク作成
          const assignees = userIds[role] || [];
          if (assignees.length === 0) {
            // 担当者未指定の場合は1つだけ作成（担当者なし）
            if (!dryRun) {
              await createTask(taskName, targetDate, null);
            }
            console.log(`  ✓ ${taskName} (担当者なし)`);
            createdCount++;
          } else {
            for (const assignee of assignees) {
              if (!dryRun) {
                await createTask(taskName, targetDate, assignee.id);
              }
              console.log(`  ✓ ${taskName} → ${assignee.name}`);
              createdCount++;
            }
          }
        } else if (role === 'なし') {
          // 担当者なし
          if (!dryRun) {
            await createTask(taskName, targetDate, null);
          }
          console.log(`  ✓ ${taskName} (担当者なし)`);
          createdCount++;
        } else {
          // 単一担当者
          const assignee = userIds[role];
          if (!dryRun) {
            await createTask(taskName, targetDate, assignee?.id || null);
          }
          console.log(`  ✓ ${taskName} → ${assignee?.name || '未設定'}`);
          createdCount++;
        }
      }
    }

    console.log('');
    console.log('========================================');
    console.log(`完了: ${createdCount}件のタスクを作成しました`);
    console.log('========================================');

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  }
}

main();
