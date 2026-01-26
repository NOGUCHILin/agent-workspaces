/**
 * SEO Opportunity Finder
 *
 * Identifies quick-win SEO opportunities from GSC data:
 * - Low CTR (high impressions but low clicks)
 * - Striking distance (position 5-20)
 * - Link building candidates (high CTR but low position)
 * - Missing content (no dedicated page for query)
 */

import { createGSCClient, validateConfig, getDateRange } from './gsc-client.js';

export interface Opportunity {
  query: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
  topPage: string;
}

export interface OpportunitiesResult {
  siteUrl: string;
  dateRange: { start: string; end: string };
  lowCTR: Opportunity[];
  strikingDistance: Opportunity[];
  linkBuilding: Opportunity[];
  missingContent: Opportunity[];
  topPerformers: Opportunity[];
  summary: {
    lowCTR: number;
    strikingDistance: number;
    linkBuilding: number;
    missingContent: number;
    topPerformers: number;
  };
  priorityActions: string[];
}

/**
 * Find SEO opportunities from GSC data
 */
export async function findOpportunities(siteUrl: string): Promise<OpportunitiesResult> {
  const { keyFile } = validateConfig();
  const client = await createGSCClient(keyFile);
  const dateRange = getDateRange(28);

  // Fetch query-level data
  const queryResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      dimensions: ['query'],
      rowLimit: 200,
    },
  });

  // Fetch query+page data for detailed analysis
  const queryPageResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      dimensions: ['query', 'page'],
      rowLimit: 500,
    },
  });

  const queryRows = queryResponse.data.rows || [];
  const queryPageRows = queryPageResponse.data.rows || [];

  // Build query-to-pages mapping
  const queryToPages = new Map<
    string,
    Array<{ page: string; clicks: number; impressions: number; ctr: number; position: number }>
  >();

  for (const row of queryPageRows) {
    const query = row.keys?.[0] || '';
    const page = row.keys?.[1] || '';

    if (!queryToPages.has(query)) {
      queryToPages.set(query, []);
    }
    queryToPages.get(query)!.push({
      page,
      clicks: row.clicks || 0,
      impressions: row.impressions || 0,
      ctr: row.ctr || 0,
      position: row.position || 0,
    });
  }

  const lowCTR: Opportunity[] = [];
  const strikingDistance: Opportunity[] = [];
  const linkBuilding: Opportunity[] = [];
  const missingContent: Opportunity[] = [];
  const topPerformers: Opportunity[] = [];

  const genericPages = ['/', '/prices', '/about', '/contact', '/stores', '/articles'];

  for (const row of queryRows) {
    const query = row.keys?.[0] || '';
    const clicks = row.clicks || 0;
    const impressions = row.impressions || 0;
    const ctr = row.ctr || 0;
    const position = row.position || 0;

    const pages = queryToPages.get(query) || [];
    const topPageInfo = pages.length > 0 ? pages.sort((a, b) => b.clicks - a.clicks)[0] : null;

    let topPage = '-';
    try {
      topPage = topPageInfo ? new URL(topPageInfo.page).pathname : '-';
    } catch {
      topPage = topPageInfo?.page || '-';
    }

    // Skip very low impression queries
    if (impressions < 10) continue;

    const opportunity: Opportunity = { query, clicks, impressions, ctr, position, topPage };

    // Low CTR (high impressions but CTR < 2%)
    if (impressions >= 100 && ctr < 0.02 && position <= 20) {
      lowCTR.push(opportunity);
    }

    // Striking distance (position 5-20, good impressions)
    if (position >= 5 && position <= 20 && impressions >= 50) {
      strikingDistance.push(opportunity);
    }

    // Link building candidates (high CTR but position > 10)
    if (ctr >= 0.05 && position > 10 && impressions >= 20) {
      linkBuilding.push(opportunity);
    }

    // Top performers (for reference)
    if (position <= 3 && clicks >= 10) {
      topPerformers.push(opportunity);
    }

    // Missing content
    if (impressions >= 50 && genericPages.includes(topPage)) {
      missingContent.push(opportunity);
    }
  }

  // Sort opportunities
  lowCTR.sort((a, b) => b.impressions - a.impressions);
  strikingDistance.sort((a, b) => a.position - b.position);
  linkBuilding.sort((a, b) => b.ctr - a.ctr);
  missingContent.sort((a, b) => b.impressions - a.impressions);

  // Generate priority actions
  const priorityActions: string[] = [];

  if (missingContent.length > 0) {
    const top = missingContent[0];
    priorityActions.push(
      `Create dedicated page for: "${top.query}" (${top.impressions} imp, showing on ${top.topPage})`
    );
  }

  if (lowCTR.length > 0) {
    const top = lowCTR[0];
    priorityActions.push(
      `Rewrite meta for: "${top.query}" (${top.impressions} imp, ${(top.ctr * 100).toFixed(1)}% CTR)`
    );
  }

  if (strikingDistance.length > 0) {
    const top = strikingDistance[0];
    priorityActions.push(`Boost content for: "${top.query}" (position ${top.position.toFixed(1)})`);
  }

  if (linkBuilding.length > 0) {
    priorityActions.push(`Get backlinks for: "${linkBuilding[0].query}"`);
  }

  return {
    siteUrl,
    dateRange: { start: dateRange.startDate, end: dateRange.endDate },
    lowCTR,
    strikingDistance,
    linkBuilding,
    missingContent,
    topPerformers,
    summary: {
      lowCTR: lowCTR.length,
      strikingDistance: strikingDistance.length,
      linkBuilding: linkBuilding.length,
      missingContent: missingContent.length,
      topPerformers: topPerformers.length,
    },
    priorityActions,
  };
}

/**
 * Print opportunities result to console
 */
export function printOpportunitiesResult(result: OpportunitiesResult): void {
  console.log(`\n🔍 SEO Opportunity Analysis`);
  console.log(`Site: ${result.siteUrl}`);
  console.log(`Period: ${result.dateRange.start} → ${result.dateRange.end}\n`);

  // Low CTR
  console.log('🎯 LOW CTR OPPORTUNITIES');
  console.log('   High impressions but clicks are low. Improve title & meta description.');
  console.log('─'.repeat(70));

  if (result.lowCTR.length === 0) {
    console.log('   No significant low CTR opportunities found.');
  } else {
    console.log('   Query'.padEnd(30) + 'Imp'.padStart(7) + 'CTR'.padStart(7) + 'Pos'.padStart(6) + '  Top Page');
    result.lowCTR.slice(0, 10).forEach((row) => {
      const q = row.query.length > 28 ? row.query.slice(0, 25) + '...' : row.query;
      console.log(
        `   ${q.padEnd(30)}${row.impressions.toString().padStart(7)}${(row.ctr * 100).toFixed(1).padStart(6)}%${row.position.toFixed(1).padStart(6)}  ${row.topPage}`
      );
    });
  }

  // Missing content
  console.log('\n\n📝 MISSING CONTENT OPPORTUNITIES');
  console.log('   These queries have no dedicated page. Consider creating targeted content.');
  console.log('─'.repeat(70));

  if (result.missingContent.length === 0) {
    console.log('   No missing content opportunities found.');
  } else {
    console.log('   Query'.padEnd(30) + 'Imp'.padStart(7) + 'Pos'.padStart(6) + '  Currently showing');
    result.missingContent.slice(0, 10).forEach((row) => {
      const q = row.query.length > 28 ? row.query.slice(0, 25) + '...' : row.query;
      console.log(
        `   ${q.padEnd(30)}${row.impressions.toString().padStart(7)}${row.position.toFixed(1).padStart(6)}  ${row.topPage}`
      );
    });
  }

  // Striking distance
  console.log('\n\n🎯 STRIKING DISTANCE (Position 5-20)');
  console.log('   Small improvements could push these to page 1 top spots.');
  console.log('─'.repeat(70));

  if (result.strikingDistance.length === 0) {
    console.log('   No striking distance keywords found.');
  } else {
    console.log('   Query'.padEnd(30) + 'Imp'.padStart(7) + 'Clicks'.padStart(7) + 'Pos'.padStart(6));
    result.strikingDistance.slice(0, 10).forEach((row) => {
      const q = row.query.length > 28 ? row.query.slice(0, 25) + '...' : row.query;
      console.log(
        `   ${q.padEnd(30)}${row.impressions.toString().padStart(7)}${row.clicks.toString().padStart(7)}${row.position.toFixed(1).padStart(6)}`
      );
    });
  }

  // Link building
  console.log('\n\n🔗 LINK BUILDING CANDIDATES');
  console.log('   High CTR shows user interest. Backlinks could boost rankings.');
  console.log('─'.repeat(70));

  if (result.linkBuilding.length === 0) {
    console.log('   No link building candidates found.');
  } else {
    console.log('   Query'.padEnd(30) + 'CTR'.padStart(7) + 'Pos'.padStart(6) + '  Page');
    result.linkBuilding.slice(0, 10).forEach((row) => {
      const q = row.query.length > 28 ? row.query.slice(0, 25) + '...' : row.query;
      console.log(
        `   ${q.padEnd(30)}${(row.ctr * 100).toFixed(1).padStart(6)}%${row.position.toFixed(1).padStart(6)}  ${row.topPage}`
      );
    });
  }

  // Summary
  console.log('\n\n📈 SUMMARY');
  console.log('─'.repeat(50));
  console.log(`Low CTR opportunities: ${result.summary.lowCTR}`);
  console.log(`Missing content opportunities: ${result.summary.missingContent}`);
  console.log(`Striking distance keywords: ${result.summary.strikingDistance}`);
  console.log(`Link building candidates: ${result.summary.linkBuilding}`);
  console.log(`Top performers (reference): ${result.summary.topPerformers}`);

  // Priority actions
  if (result.priorityActions.length > 0) {
    console.log('\n🚀 PRIORITY ACTIONS');
    console.log('─'.repeat(50));
    result.priorityActions.forEach((action, i) => {
      console.log(`${i + 1}. ${action}`);
    });
  }
}
