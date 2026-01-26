/**
 * SERP (Search Engine Results Page) Analysis
 * Serper APIを使用してGoogle検索結果を取得・分析
 */

import puppeteer, { Browser, Page } from 'puppeteer';
import * as cheerio from 'cheerio';
import chalk from 'chalk';

// Serper API設定
const SERPER_API_URL = 'https://google.serper.dev/search';
const SERPER_API_KEY = process.env.SERPER_API_KEY || '';

export interface SerpResult {
  position: number;
  title: string;
  url: string;
  description: string;
  domain: string;
}

export interface PageAnalysis {
  url: string;
  title: string;
  h1: string;
  headings: { h2: string[]; h3: string[] };
  wordCount: number;
  hasSchema: boolean;
  schemaTypes: string[];
}

export interface SerpAnalysisResult {
  keyword: string;
  searchedAt: string;
  results: SerpResult[];
  pageAnalyses: PageAnalysis[];
  ownSitePosition: number | null;
  ownSiteDomain: string;
}

interface SerperOrganicResult {
  title: string;
  link: string;
  snippet?: string;
  position: number;
}

interface SerperResponse {
  organic?: SerperOrganicResult[];
  searchParameters?: {
    q: string;
    gl: string;
    hl: string;
  };
}

/**
 * Serper APIで検索結果を取得
 */
async function fetchSerpResultsViaSerper(keyword: string): Promise<SerpResult[]> {
  if (!SERPER_API_KEY) {
    throw new Error('SERPER_API_KEY environment variable is not set');
  }

  const response = await fetch(SERPER_API_URL, {
    method: 'POST',
    headers: {
      'X-API-KEY': SERPER_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      q: keyword,
      gl: 'jp',
      hl: 'ja',
      num: 10,
    }),
  });

  if (!response.ok) {
    throw new Error(`Serper API error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as SerperResponse;
  const results: SerpResult[] = [];

  if (data.organic) {
    for (const item of data.organic.slice(0, 10)) {
      try {
        const domain = new URL(item.link).hostname;
        results.push({
          position: item.position,
          title: item.title,
          url: item.link,
          description: item.snippet || '',
          domain,
        });
      } catch {
        // 無効なURLはスキップ
      }
    }
  }

  return results;
}

/**
 * 個別ページを分析（Puppeteer使用）
 */
async function analyzePage(page: Page, url: string): Promise<PageAnalysis | null> {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    const html = await page.content();
    const $ = cheerio.load(html);

    // タイトル
    const title = $('title').text().trim();

    // H1
    const h1 = $('h1').first().text().trim();

    // 見出し構造
    const h2s: string[] = [];
    const h3s: string[] = [];
    $('h2').each((_, el) => { h2s.push($(el).text().trim()); });
    $('h3').each((_, el) => { h3s.push($(el).text().trim()); });

    // 本文の文字数（大まかな推定）
    const bodyText = $('body').text().replace(/\s+/g, '');
    const wordCount = bodyText.length;

    // 構造化データ
    const schemaTypes: string[] = [];
    $('script[type="application/ld+json"]').each((_, el) => {
      try {
        const json = JSON.parse($(el).html() || '{}');
        if (json['@type']) {
          schemaTypes.push(json['@type']);
        } else if (Array.isArray(json['@graph'])) {
          json['@graph'].forEach((item: { '@type'?: string }) => {
            if (item['@type']) schemaTypes.push(item['@type']);
          });
        }
      } catch {
        // パースエラーは無視
      }
    });

    return {
      url,
      title,
      h1,
      headings: { h2: h2s.slice(0, 10), h3: h3s.slice(0, 10) },
      wordCount,
      hasSchema: schemaTypes.length > 0,
      schemaTypes,
    };
  } catch (error) {
    console.error(chalk.yellow(`  ⚠ Failed to analyze: ${url}`));
    return null;
  }
}

/**
 * SERP分析を実行
 */
export async function analyzeSerpResults(
  keyword: string,
  ownDomain: string,
  analyzePages: boolean = true,
  maxPages: number = 5
): Promise<SerpAnalysisResult> {
  console.log(chalk.blue(`Fetching SERP via Serper API: "${keyword}"...`));

  // Serper APIで検索結果を取得
  const results = await fetchSerpResultsViaSerper(keyword);

  console.log(chalk.green(`  ✓ Found ${results.length} results`));

  // 自サイトの順位を確認
  const ownSiteResult = results.find(r => r.domain.includes(ownDomain));
  const ownSitePosition = ownSiteResult ? ownSiteResult.position : null;

  // ページ分析（オプション）
  const pageAnalyses: PageAnalysis[] = [];
  if (analyzePages && results.length > 0) {
    console.log(chalk.blue(`Analyzing top ${Math.min(maxPages, results.length)} pages...`));

    let browser: Browser | null = null;
    try {
      browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--lang=ja'],
      });
      const page = await browser.newPage();
      await page.setUserAgent(
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      );

      for (let i = 0; i < Math.min(maxPages, results.length); i++) {
        console.log(chalk.gray(`  [${i + 1}/${maxPages}] ${results[i].domain}`));
        const analysis = await analyzePage(page, results[i].url);
        if (analysis) {
          pageAnalyses.push(analysis);
        }
      }
    } finally {
      if (browser) {
        await browser.close();
      }
    }
  }

  return {
    keyword,
    searchedAt: new Date().toISOString(),
    results,
    pageAnalyses,
    ownSitePosition,
    ownSiteDomain: ownDomain,
  };
}

/**
 * SERP分析結果を表示
 */
export function printSerpResult(result: SerpAnalysisResult): void {
  console.log('\n');
  console.log(chalk.bold.cyan('╔══════════════════════════════════════╗'));
  console.log(chalk.bold.cyan('║       SERP ANALYSIS REPORT           ║'));
  console.log(chalk.bold.cyan('╚══════════════════════════════════════╝'));
  console.log();

  console.log(chalk.bold(`Keyword: "${result.keyword}"`));
  console.log(chalk.gray(`Searched at: ${result.searchedAt}`));
  console.log();

  // 自サイトの順位
  if (result.ownSitePosition) {
    console.log(chalk.green(`✓ Your site (${result.ownSiteDomain}): Position #${result.ownSitePosition}`));
  } else {
    console.log(chalk.yellow(`⚠ Your site (${result.ownSiteDomain}): Not in top 10`));
  }
  console.log();

  // 検索結果一覧
  console.log(chalk.bold('🔍 Search Results (Top 10)'));
  console.log('─'.repeat(70));

  for (const r of result.results) {
    const isOwn = r.domain.includes(result.ownSiteDomain);
    const prefix = isOwn ? chalk.green('★') : ' ';
    console.log(`${prefix}${chalk.bold(`#${r.position}`)} ${chalk.blue(r.domain)}`);
    console.log(`   ${r.title.slice(0, 60)}${r.title.length > 60 ? '...' : ''}`);
    console.log(chalk.gray(`   ${r.description.slice(0, 80)}${r.description.length > 80 ? '...' : ''}`));
    console.log();
  }

  // ページ分析
  if (result.pageAnalyses.length > 0) {
    console.log(chalk.bold('\n📊 Content Analysis (Top Pages)'));
    console.log('─'.repeat(70));

    console.log(chalk.gray('Pos  Domain                    WordCount  H2s  Schema'));
    console.log('─'.repeat(70));

    result.pageAnalyses.forEach((analysis, i) => {
      const domain = new URL(analysis.url).hostname.slice(0, 24).padEnd(25);
      const wordCount = analysis.wordCount.toLocaleString().padStart(8);
      const h2Count = analysis.headings.h2.length.toString().padStart(4);
      const schema = analysis.hasSchema ? analysis.schemaTypes.slice(0, 2).join(', ') : '-';

      console.log(`#${(i + 1).toString().padEnd(3)} ${domain} ${wordCount}  ${h2Count}  ${schema}`);
    });

    // 見出し構造の比較
    console.log(chalk.bold('\n📝 H2 Headings Comparison'));
    console.log('─'.repeat(70));

    result.pageAnalyses.slice(0, 3).forEach((analysis, i) => {
      const domain = new URL(analysis.url).hostname;
      console.log(chalk.blue(`\n#${i + 1} ${domain}`));
      console.log(chalk.gray(`   H1: ${analysis.h1.slice(0, 50)}${analysis.h1.length > 50 ? '...' : ''}`));
      analysis.headings.h2.slice(0, 5).forEach(h2 => {
        console.log(`   • ${h2.slice(0, 50)}${h2.length > 50 ? '...' : ''}`);
      });
    });
  }

  // 改善提案
  console.log(chalk.bold('\n💡 Recommendations'));
  console.log('─'.repeat(70));

  if (!result.ownSitePosition) {
    console.log(chalk.yellow('• Your site is not ranking in top 10. Consider:'));
    console.log('  - Creating dedicated content for this keyword');
    console.log('  - Analyzing top 3 competitors\' content structure');
    console.log('  - Building topical authority with related content');
  } else if (result.ownSitePosition > 3) {
    console.log(chalk.yellow(`• Your site is at position #${result.ownSitePosition}. To improve:`));

    // 上位との比較
    if (result.pageAnalyses.length > 0) {
      const topPage = result.pageAnalyses[0];
      const ownAnalysis = result.pageAnalyses.find(p =>
        p.url.includes(result.ownSiteDomain)
      );

      if (topPage && ownAnalysis) {
        if (topPage.wordCount > ownAnalysis.wordCount * 1.5) {
          console.log(`  - Top page has ${topPage.wordCount.toLocaleString()} chars vs your ${ownAnalysis.wordCount.toLocaleString()}. Consider expanding content.`);
        }
        if (topPage.headings.h2.length > ownAnalysis.headings.h2.length) {
          console.log(`  - Top page has ${topPage.headings.h2.length} H2s vs your ${ownAnalysis.headings.h2.length}. Consider adding sections.`);
        }
      }
    }
  } else {
    console.log(chalk.green('✓ Your site is in top 3! Focus on:'));
    console.log('  - Maintaining content freshness');
    console.log('  - Improving CTR with better title/description');
  }
}
