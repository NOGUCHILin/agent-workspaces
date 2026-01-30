/**
 * GSC Performance Data Fetcher
 *
 * Fetches search performance data including:
 * - Overall metrics (clicks, impressions, CTR, position)
 * - Top queries
 * - Top pages
 * - Device breakdown
 */

import { searchconsole_v1 } from 'googleapis';
import { createGSCClient, validateConfig, getDateRange, DateRange } from './gsc-client.js';

export interface PerformanceMetrics {
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

export interface QueryData extends PerformanceMetrics {
  query: string;
}

export interface PageData extends PerformanceMetrics {
  page: string;
  path: string;
}

export interface DeviceData extends PerformanceMetrics {
  device: string;
}

export interface PerformanceResult {
  siteUrl: string;
  dateRange: DateRange;
  overall: PerformanceMetrics;
  topQueries: QueryData[];
  topPages: PageData[];
  byDevice: DeviceData[];
}

/**
 * Fetch GSC performance data for a site
 */
export async function fetchPerformance(
  siteUrl: string,
  days: number = 30
): Promise<PerformanceResult> {
  const { keyFile } = validateConfig();
  const client = await createGSCClient(keyFile);
  const dateRange = getDateRange(days);

  // Fetch overall performance
  const overallResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      dimensions: [],
    },
  });

  const overallRow = overallResponse.data.rows?.[0];
  const overall: PerformanceMetrics = {
    clicks: overallRow?.clicks || 0,
    impressions: overallRow?.impressions || 0,
    ctr: overallRow?.ctr || 0,
    position: overallRow?.position || 0,
  };

  // Fetch top queries
  const queriesResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      dimensions: ['query'],
      rowLimit: 20,
    },
  });

  const topQueries: QueryData[] = (queriesResponse.data.rows || []).map((row) => ({
    query: row.keys?.[0] || '',
    clicks: row.clicks || 0,
    impressions: row.impressions || 0,
    ctr: row.ctr || 0,
    position: row.position || 0,
  }));

  // Fetch top pages
  const pagesResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      dimensions: ['page'],
      rowLimit: 15,
    },
  });

  const topPages: PageData[] = (pagesResponse.data.rows || []).map((row) => {
    const pageUrl = row.keys?.[0] || '';
    let path = pageUrl;
    try {
      path = new URL(pageUrl).pathname;
    } catch {
      // Keep original if URL parsing fails
    }
    return {
      page: pageUrl,
      path,
      clicks: row.clicks || 0,
      impressions: row.impressions || 0,
      ctr: row.ctr || 0,
      position: row.position || 0,
    };
  });

  // Fetch by device
  const deviceResponse = await client.searchanalytics.query({
    siteUrl,
    requestBody: {
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      dimensions: ['device'],
    },
  });

  const byDevice: DeviceData[] = (deviceResponse.data.rows || []).map((row) => ({
    device: row.keys?.[0] || '',
    clicks: row.clicks || 0,
    impressions: row.impressions || 0,
    ctr: row.ctr || 0,
    position: row.position || 0,
  }));

  return {
    siteUrl,
    dateRange,
    overall,
    topQueries,
    topPages,
    byDevice,
  };
}

/**
 * Print performance result to console
 */
export function printPerformanceResult(result: PerformanceResult): void {
  console.log(`\n📊 GSC Performance Report`);
  console.log(`Site: ${result.siteUrl}`);
  console.log(`Period: ${result.dateRange.startDate} → ${result.dateRange.endDate}\n`);

  // Overall metrics
  console.log('📈 Overall Performance');
  console.log('─'.repeat(50));
  console.log(`Clicks: ${result.overall.clicks.toLocaleString()}`);
  console.log(`Impressions: ${result.overall.impressions.toLocaleString()}`);
  console.log(`CTR: ${(result.overall.ctr * 100).toFixed(2)}%`);
  console.log(`Avg Position: ${result.overall.position.toFixed(1)}`);

  // Top queries
  console.log('\n🔍 Top Queries');
  console.log('─'.repeat(50));
  result.topQueries.forEach((row, i) => {
    console.log(`${(i + 1).toString().padStart(2)}. "${row.query}"`);
    console.log(
      `    Clicks: ${row.clicks} | Imp: ${row.impressions} | CTR: ${(row.ctr * 100).toFixed(1)}% | Pos: ${row.position.toFixed(1)}`
    );
  });

  // Top pages
  console.log('\n📄 Top Pages');
  console.log('─'.repeat(50));
  result.topPages.forEach((row, i) => {
    console.log(`${(i + 1).toString().padStart(2)}. ${row.path}`);
    console.log(
      `    Clicks: ${row.clicks} | Imp: ${row.impressions} | CTR: ${(row.ctr * 100).toFixed(1)}% | Pos: ${row.position.toFixed(1)}`
    );
  });

  // By device
  console.log('\n📱 By Device');
  console.log('─'.repeat(50));
  result.byDevice.forEach((row) => {
    console.log(
      `${row.device.padEnd(10)} Clicks: ${row.clicks} | Imp: ${row.impressions} | CTR: ${(row.ctr * 100).toFixed(1)}%`
    );
  });
}
