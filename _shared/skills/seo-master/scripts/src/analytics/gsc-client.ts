/**
 * Google Search Console API Client
 *
 * Shared authentication and client for GSC API operations.
 *
 * Prerequisites:
 *   1. Create Google Cloud project
 *   2. Enable Search Console API
 *   3. Create service account and download JSON key
 *   4. Add service account email to GSC property as user
 *
 * Usage:
 *   Set GSC_KEY_FILE environment variable to your service account JSON key file path
 */

import { google, searchconsole_v1 } from 'googleapis';
import { existsSync } from 'fs';

export interface GSCConfig {
  keyFile: string;
  siteUrl: string;
}

export interface DateRange {
  startDate: string;
  endDate: string;
}

/**
 * Validate GSC configuration
 */
export function validateConfig(): { keyFile: string } {
  const keyFile = process.env.GSC_KEY_FILE;

  if (!keyFile) {
    console.error('GSC_KEY_FILE environment variable not set');
    console.error('\nSetup steps:');
    console.error('1. Go to Google Cloud Console');
    console.error('2. Create project and enable Search Console API');
    console.error('3. Create service account, download JSON key');
    console.error('4. Add service account email to GSC property');
    throw new Error('GSC_KEY_FILE not set');
  }

  if (!existsSync(keyFile)) {
    throw new Error(`GSC key file not found: ${keyFile}`);
  }

  return { keyFile };
}

/**
 * Create authenticated GSC client
 */
export async function createGSCClient(keyFile: string): Promise<searchconsole_v1.Searchconsole> {
  const auth = new google.auth.GoogleAuth({
    keyFile,
    scopes: ['https://www.googleapis.com/auth/webmasters.readonly'],
  });

  return google.searchconsole({ version: 'v1', auth });
}

/**
 * Format date to YYYY-MM-DD string
 */
export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * Calculate date range for GSC queries
 * Note: GSC data has a 3-day lag
 */
export function getDateRange(days: number): DateRange {
  const endDate = new Date();
  endDate.setDate(endDate.getDate() - 3); // GSC data lag

  const startDate = new Date(endDate);
  startDate.setDate(startDate.getDate() - days);

  return {
    startDate: formatDate(startDate),
    endDate: formatDate(endDate),
  };
}

/**
 * Get comparison date ranges (current vs previous period)
 */
export function getComparisonRanges(days: number = 7): {
  current: DateRange;
  previous: DateRange;
} {
  const currentEnd = new Date();
  currentEnd.setDate(currentEnd.getDate() - 3);

  const currentStart = new Date(currentEnd);
  currentStart.setDate(currentStart.getDate() - days);

  const prevEnd = new Date(currentStart);
  prevEnd.setDate(prevEnd.getDate() - 1);

  const prevStart = new Date(prevEnd);
  prevStart.setDate(prevStart.getDate() - days);

  return {
    current: {
      startDate: formatDate(currentStart),
      endDate: formatDate(currentEnd),
    },
    previous: {
      startDate: formatDate(prevStart),
      endDate: formatDate(prevEnd),
    },
  };
}
