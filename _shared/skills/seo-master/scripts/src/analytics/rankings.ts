/**
 * Keyword Ranking Tracker
 *
 * Tracks keyword rankings over time using GSC data.
 * Compares current period vs previous period.
 */

import { createGSCClient, validateConfig, getComparisonRanges, formatDate } from './gsc-client.js';

export interface RankingChange {
  keyword: string;
  currentPosition: number | null;
  previousPosition: number | null;
  change: number;
  changeLabel: string;
  currentClicks: number;
  currentImpressions: number;
}

export interface RankingsResult {
  siteUrl: string;
  currentPeriod: { start: string; end: string };
  previousPeriod: { start: string; end: string };
  changes: RankingChange[];
  summary: {
    improved: number;
    declined: number;
    stable: number;
    new: number;
    lost: number;
  };
}

/**
 * Track keyword rankings
 */
export async function trackRankings(
  siteUrl: string,
  targetKeywords: string[] = []
): Promise<RankingsResult> {
  const { keyFile } = validateConfig();
  const client = await createGSCClient(keyFile);
  const { current, previous } = getComparisonRanges(7);

  // Fetch current period
  const currentResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: current.startDate,
      endDate: current.endDate,
      dimensions: ['query'],
      rowLimit: 100,
    },
  });

  // Fetch previous period
  const prevResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: previous.startDate,
      endDate: previous.endDate,
      dimensions: ['query'],
      rowLimit: 100,
    },
  });

  const currentData = new Map<string, { position: number; clicks: number; impressions: number }>();
  const prevData = new Map<string, { position: number }>();

  (currentResponse.data.rows || []).forEach((row) => {
    currentData.set(row.keys?.[0] || '', {
      position: row.position || 0,
      clicks: row.clicks || 0,
      impressions: row.impressions || 0,
    });
  });

  (prevResponse.data.rows || []).forEach((row) => {
    prevData.set(row.keys?.[0] || '', {
      position: row.position || 0,
    });
  });

  // Determine which keywords to analyze
  const allKeywords =
    targetKeywords.length > 0
      ? targetKeywords.filter((k) => currentData.has(k) || prevData.has(k))
      : [...new Set([...currentData.keys()])].slice(0, 30);

  const changes: RankingChange[] = [];
  let improved = 0;
  let declined = 0;
  let stable = 0;
  let newCount = 0;
  let lost = 0;

  for (const keyword of allKeywords) {
    const currentInfo = currentData.get(keyword);
    const prevInfo = prevData.get(keyword);

    const currentPosition = currentInfo?.position ?? null;
    const previousPosition = prevInfo?.position ?? null;

    let change = 0;
    let changeLabel = '';

    if (currentPosition !== null && previousPosition !== null) {
      change = previousPosition - currentPosition; // positive = improved
      if (change > 0.5) {
        changeLabel = `↑ +${change.toFixed(1)}`;
        improved++;
      } else if (change < -0.5) {
        changeLabel = `↓ ${change.toFixed(1)}`;
        declined++;
      } else {
        changeLabel = '→ 0';
        stable++;
      }
    } else if (currentPosition !== null && previousPosition === null) {
      changeLabel = '🆕 New';
      newCount++;
    } else if (currentPosition === null && previousPosition !== null) {
      changeLabel = '❌ Lost';
      lost++;
    }

    changes.push({
      keyword,
      currentPosition,
      previousPosition,
      change,
      changeLabel,
      currentClicks: currentInfo?.clicks || 0,
      currentImpressions: currentInfo?.impressions || 0,
    });
  }

  // Sort by change (biggest improvements first)
  changes.sort((a, b) => b.change - a.change);

  return {
    siteUrl,
    currentPeriod: { start: current.startDate, end: current.endDate },
    previousPeriod: { start: previous.startDate, end: previous.endDate },
    changes,
    summary: { improved, declined, stable, new: newCount, lost },
  };
}

/**
 * Print rankings result to console
 */
export function printRankingsResult(result: RankingsResult): void {
  console.log(`\n📊 Keyword Rankings Tracker`);
  console.log(`Site: ${result.siteUrl}`);
  console.log(`Current: ${result.currentPeriod.start} → ${result.currentPeriod.end}`);
  console.log(`Previous: ${result.previousPeriod.start} → ${result.previousPeriod.end}\n`);

  console.log('📈 Ranking Changes (Position)');
  console.log('═'.repeat(70));
  console.log('Query'.padEnd(40) + 'Now'.padStart(8) + 'Prev'.padStart(8) + 'Change'.padStart(12));
  console.log('─'.repeat(70));

  result.changes.forEach(({ keyword, currentPosition, previousPosition, changeLabel }) => {
    const truncatedKeyword = keyword.length > 38 ? keyword.slice(0, 35) + '...' : keyword;
    const currentStr = currentPosition !== null ? currentPosition.toFixed(1) : '-';
    const prevStr = previousPosition !== null ? previousPosition.toFixed(1) : '-';

    console.log(
      truncatedKeyword.padEnd(40) +
        currentStr.padStart(8) +
        prevStr.padStart(8) +
        changeLabel.padStart(12)
    );
  });

  // Summary
  console.log('\n📊 Summary');
  console.log('─'.repeat(50));
  console.log(`✅ Improved: ${result.summary.improved}`);
  console.log(`❌ Declined: ${result.summary.declined}`);
  console.log(`➡️  Stable: ${result.summary.stable}`);
  if (result.summary.new > 0) console.log(`🆕 New: ${result.summary.new}`);
  if (result.summary.lost > 0) console.log(`❌ Lost: ${result.summary.lost}`);

  // Top improvements
  const topImprovements = result.changes.filter((c) => c.change > 1).slice(0, 5);
  if (topImprovements.length > 0) {
    console.log('\n🏆 Top Improvements:');
    topImprovements.forEach((c) => {
      console.log(`   "${c.keyword}" +${c.change.toFixed(1)} positions`);
    });
  }

  // Biggest drops
  const topDrops = result.changes.filter((c) => c.change < -1).slice(-5).reverse();
  if (topDrops.length > 0) {
    console.log('\n⚠️  Needs Attention:');
    topDrops.forEach((c) => {
      console.log(`   "${c.keyword}" ${c.change.toFixed(1)} positions`);
    });
  }
}
