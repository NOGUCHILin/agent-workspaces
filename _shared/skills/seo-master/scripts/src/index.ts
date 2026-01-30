#!/usr/bin/env node
import 'dotenv/config';
import { Command } from 'commander';
import chalk from 'chalk';
import { runLighthouseAudit } from './auditors/lighthouse.js';
import { runSchemaAudit, SchemaValidationResult } from './auditors/schema.js';
import { runMetaAudit, MetaAuditResult } from './auditors/meta.js';
import { runLinksAudit, LinksAuditResult } from './auditors/links.js';
import { calculateScore, ScoringResult, Recommendation } from './scoring/calculator.js';
import { generateMarkdownReport } from './reports/markdown.js';
import { fetchPerformance, printPerformanceResult } from './analytics/performance.js';
import { trackRankings, printRankingsResult } from './analytics/rankings.js';
import { findOpportunities, printOpportunitiesResult } from './analytics/opportunities.js';
import { analyzeSerpResults, printSerpResult } from './analytics/serp.js';
import {
  searchSEOFramework,
  detectPageType,
  detectSearchIntent,
  findLLMTactics,
  SearchResult,
} from './search/engine.js';
import {
  loadPageTypes,
  loadSearchIntents,
  loadLLMTactics,
  PageType,
  SearchIntent,
  LLMTactic,
  DatasetType,
} from './search/datasets.js';

const program = new Command();

program
  .name('seo-audit')
  .description('SEO audit automation tools')
  .version('1.0.0');

// Lighthouse audit command
program
  .command('lighthouse')
  .description('Run Lighthouse audit (Core Web Vitals, SEO, Accessibility)')
  .argument('<url>', 'URL to audit')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Starting Lighthouse audit...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      const result = await runLighthouseAudit(url);

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printLighthouseResult(result);
      }
    } catch (error) {
      console.error(chalk.red('Audit failed:'), error);
      process.exit(1);
    }
  });

// Schema validation command
program
  .command('schema')
  .description('Validate structured data (JSON-LD)')
  .argument('<url>', 'URL to audit')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Starting schema validation...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      const result = await runSchemaAudit(url);

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printSchemaResult(result);
      }
    } catch (error) {
      console.error(chalk.red('Schema validation failed:'), error);
      process.exit(1);
    }
  });

// Meta tags audit command
program
  .command('meta')
  .description('Audit meta tags (title, description, OG, etc.)')
  .argument('<url>', 'URL to audit')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Starting meta tags audit...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      const result = await runMetaAudit(url);

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printMetaResult(result);
      }
    } catch (error) {
      console.error(chalk.red('Meta audit failed:'), error);
      process.exit(1);
    }
  });

// Links audit command
program
  .command('links')
  .description('Audit internal and external links')
  .argument('<url>', 'URL to audit')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Starting links audit...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      const result = await runLinksAudit(url);

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printLinksResult(result);
      }
    } catch (error) {
      console.error(chalk.red('Links audit failed:'), error);
      process.exit(1);
    }
  });

// Score command (quick scoring without Lighthouse)
program
  .command('score')
  .description('Calculate SEO score (fast, no Lighthouse)')
  .argument('<url>', 'URL to audit')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Calculating SEO score...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      const [schemaResult, metaResult, linksResult] = await Promise.all([
        runSchemaAudit(url),
        runMetaAudit(url),
        runLinksAudit(url),
      ]);

      const scoreResult = calculateScore(null, schemaResult, metaResult, linksResult);

      if (options.format === 'json') {
        const output = JSON.stringify(scoreResult, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printScoreResult(scoreResult);
      }
    } catch (error) {
      console.error(chalk.red('Scoring failed:'), error);
      process.exit(1);
    }
  });

// Full audit command (default)
program
  .command('full', { isDefault: true })
  .description('Run full SEO audit (Lighthouse + Schema + Meta + Links)')
  .argument('<url>', 'URL to audit')
  .option('-f, --format <type>', 'Output format (json, md, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .option('--sitemap', 'Treat URL as sitemap and audit all pages')
  .option('--skip-lighthouse', 'Skip Lighthouse audit (faster)')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Starting full SEO audit...'));
    console.log(chalk.gray(`Target: ${url}`));

    if (options.sitemap) {
      console.log(chalk.yellow('Sitemap mode not yet implemented'));
      process.exit(1);
    }

    try {
      // Run audits in parallel with proper typing
      const [schemaResult, metaResult, linksResult] = await Promise.all([
        runSchemaAudit(url),
        runMetaAudit(url),
        runLinksAudit(url),
      ]);

      // Lighthouse is optional (slow)
      const lighthouseResult = options.skipLighthouse
        ? null
        : await runLighthouseAudit(url);

      // Calculate score
      const scoreResult = calculateScore(lighthouseResult, schemaResult, metaResult, linksResult);

      const fullResult = {
        url,
        timestamp: new Date().toISOString(),
        lighthouse: lighthouseResult,
        schema: schemaResult,
        meta: metaResult,
        links: linksResult,
        score: scoreResult,
      };

      if (options.format === 'json') {
        const output = JSON.stringify(fullResult, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else if (options.format === 'md') {
        const mdReport = generateMarkdownReport(fullResult);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, mdReport);
          console.log(chalk.green(`Markdown report saved to ${options.output}`));
        } else {
          console.log(mdReport);
        }
      } else {
        // Print score summary first
        printScoreResult(scoreResult);
        console.log('');

        if (lighthouseResult) {
          printLighthouseResult(lighthouseResult);
          console.log('');
        }
        printSchemaResult(schemaResult);
        console.log('');
        printMetaResult(metaResult);
        console.log('');
        printLinksResult(linksResult);
      }
    } catch (error) {
      console.error(chalk.red('Audit failed:'), error);
      process.exit(1);
    }
  });

// ============================================
// GSC Analytics Commands
// ============================================

// GSC Performance command
program
  .command('gsc:performance')
  .description('Fetch GSC performance data (clicks, impressions, CTR)')
  .argument('<site-url>', 'Site URL (e.g., https://example.com)')
  .option('-d, --days <number>', 'Number of days to fetch', '30')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (siteUrl: string, options) => {
    console.log(chalk.blue('Fetching GSC performance data...'));

    try {
      const result = await fetchPerformance(siteUrl, parseInt(options.days));

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printPerformanceResult(result);
      }
    } catch (error) {
      console.error(chalk.red('GSC fetch failed:'), error);
      process.exit(1);
    }
  });

// GSC Rankings command
program
  .command('gsc:rankings')
  .description('Track keyword ranking changes over time')
  .argument('<site-url>', 'Site URL (e.g., https://example.com)')
  .argument('[keywords...]', 'Specific keywords to track (optional)')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (siteUrl: string, keywords: string[], options) => {
    console.log(chalk.blue('Tracking keyword rankings...'));

    try {
      const result = await trackRankings(siteUrl, keywords);

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printRankingsResult(result);
      }
    } catch (error) {
      console.error(chalk.red('Rankings tracking failed:'), error);
      process.exit(1);
    }
  });

// GSC Opportunities command
program
  .command('gsc:opportunities')
  .description('Find SEO opportunities (low CTR, striking distance, etc.)')
  .argument('<site-url>', 'Site URL (e.g., https://example.com)')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (siteUrl: string, options) => {
    console.log(chalk.blue('Finding SEO opportunities...'));

    try {
      const result = await findOpportunities(siteUrl);

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printOpportunitiesResult(result);
      }
    } catch (error) {
      console.error(chalk.red('Opportunity analysis failed:'), error);
      process.exit(1);
    }
  });

// ============================================
// SERP Analysis Commands
// ============================================

// SERP Analysis command
program
  .command('serp:analyze')
  .description('Analyze Google SERP for a keyword and compare with competitors')
  .argument('<keyword>', 'Keyword to search')
  .option('-d, --domain <domain>', 'Your domain to track (default: applebuyers.jp)', 'applebuyers.jp')
  .option('-p, --pages <number>', 'Number of pages to analyze in detail', '5')
  .option('--no-analyze', 'Skip detailed page analysis (faster)')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .option('-o, --output <file>', 'Output file path')
  .action(async (keyword: string, options) => {
    console.log(chalk.blue(`Starting SERP analysis for: "${keyword}"...`));

    try {
      const result = await analyzeSerpResults(
        keyword,
        options.domain,
        options.analyze !== false,
        parseInt(options.pages)
      );

      if (options.format === 'json') {
        const output = JSON.stringify(result, null, 2);
        if (options.output) {
          const fs = await import('fs/promises');
          await fs.writeFile(options.output, output);
          console.log(chalk.green(`Report saved to ${options.output}`));
        } else {
          console.log(output);
        }
      } else {
        printSerpResult(result);
      }
    } catch (error) {
      console.error(chalk.red('SERP analysis failed:'), error);
      process.exit(1);
    }
  });

function formatScore(score: number): string {
  const percentage = Math.round(score * 100);
  if (percentage >= 90) return chalk.green(`${percentage}`);
  if (percentage >= 50) return chalk.yellow(`${percentage}`);
  return chalk.red(`${percentage}`);
}

function printLighthouseResult(result: Awaited<ReturnType<typeof runLighthouseAudit>>): void {
  console.log('\n' + chalk.bold('=== Lighthouse Results ===\n'));
  console.log(chalk.cyan('Performance:'), formatScore(result.performance));
  console.log(chalk.cyan('SEO:'), formatScore(result.seo));
  console.log(chalk.cyan('Accessibility:'), formatScore(result.accessibility));
  console.log(chalk.cyan('Best Practices:'), formatScore(result.bestPractices));

  console.log('\n' + chalk.bold('Core Web Vitals:'));
  console.log(chalk.gray('  LCP:'), result.coreWebVitals.lcp);
  console.log(chalk.gray('  INP:'), result.coreWebVitals.inp);
  console.log(chalk.gray('  CLS:'), result.coreWebVitals.cls);

  if (result.seoAudits.length > 0) {
    console.log('\n' + chalk.bold('SEO Audits:'));
    result.seoAudits.forEach(audit => {
      const icon = audit.passed ? chalk.green('✓') : chalk.red('✗');
      console.log(`  ${icon} ${audit.title}`);
    });
  }
}

function printSchemaResult(result: Awaited<ReturnType<typeof runSchemaAudit>>): void {
  console.log(chalk.bold('=== Structured Data Results ===\n'));
  console.log(chalk.cyan('Schemas found:'), result.schemasFound);
  console.log(chalk.green('Valid:'), result.summary.valid);
  console.log(chalk.red('Invalid:'), result.summary.invalid);
  console.log(chalk.yellow('Warnings:'), result.summary.warnings);

  if (result.schemas.length > 0) {
    console.log('\n' + chalk.bold('Schema Details:'));
    result.schemas.forEach((schema: SchemaValidationResult, index: number) => {
      const statusIcon = schema.valid ? chalk.green('✓') : chalk.red('✗');
      console.log(`\n  ${statusIcon} ${chalk.bold(schema.type)}`);

      if (schema.errors.length > 0) {
        schema.errors.forEach(err => {
          console.log(chalk.red(`    ✗ ${err}`));
        });
      }

      if (schema.warnings.length > 0) {
        schema.warnings.forEach(warn => {
          console.log(chalk.yellow(`    ⚠ ${warn}`));
        });
      }
    });
  }
}

function printMetaResult(result: MetaAuditResult): void {
  console.log(chalk.bold('=== Meta Tags Results ===\n'));

  // Title
  const titleIcon = result.title.status === 'good' ? chalk.green('✓') : chalk.red('✗');
  console.log(`${titleIcon} ${chalk.cyan('Title:')} ${result.title.value || '[missing]'}`);
  console.log(chalk.gray(`   Length: ${result.title.length} chars (${result.title.status})`));

  // Description
  const descIcon = result.description.status === 'good' ? chalk.green('✓') : chalk.red('✗');
  console.log(`${descIcon} ${chalk.cyan('Description:')} ${result.description.value?.substring(0, 60) || '[missing]'}...`);
  console.log(chalk.gray(`   Length: ${result.description.length} chars (${result.description.status})`));

  // Robots
  const robotsIcon = result.robots.isIndexable ? chalk.green('✓') : chalk.yellow('⚠');
  console.log(`${robotsIcon} ${chalk.cyan('Robots:')} ${result.robots.value || '[not set]'}`);

  // Canonical
  const canonicalIcon = result.canonical.value ? chalk.green('✓') : chalk.yellow('⚠');
  console.log(`${canonicalIcon} ${chalk.cyan('Canonical:')} ${result.canonical.value || '[not set]'}`);

  // H1
  const h1Icon = result.h1.status === 'good' ? chalk.green('✓') : chalk.red('✗');
  console.log(`${h1Icon} ${chalk.cyan('H1:')} ${result.h1.values[0] || '[missing]'} (${result.h1.count} found)`);

  // Open Graph
  const ogIcon = result.openGraph.complete ? chalk.green('✓') : chalk.yellow('⚠');
  console.log(`${ogIcon} ${chalk.cyan('Open Graph:')} ${result.openGraph.complete ? 'Complete' : 'Incomplete'}`);

  // Viewport
  const vpIcon = result.viewport.isMobileFriendly ? chalk.green('✓') : chalk.red('✗');
  console.log(`${vpIcon} ${chalk.cyan('Viewport:')} ${result.viewport.isMobileFriendly ? 'Mobile-friendly' : 'Not mobile-friendly'}`);

  // Issues and warnings
  if (result.issues.length > 0) {
    console.log('\n' + chalk.bold('Issues:'));
    result.issues.forEach(issue => {
      console.log(chalk.red(`  ✗ ${issue}`));
    });
  }

  if (result.warnings.length > 0) {
    console.log('\n' + chalk.bold('Warnings:'));
    result.warnings.forEach(warn => {
      console.log(chalk.yellow(`  ⚠ ${warn}`));
    });
  }
}

function printLinksResult(result: LinksAuditResult): void {
  console.log(chalk.bold('=== Links Analysis ===\n'));

  console.log(chalk.cyan('Total links:'), result.summary.total);
  console.log(chalk.cyan('Internal:'), result.summary.internal);
  console.log(chalk.cyan('External:'), result.summary.external);
  console.log(chalk.cyan('NoFollow:'), result.summary.noFollow);
  console.log(chalk.cyan('Empty text:'), result.summary.emptyText);

  // Top internal links
  if (result.internalLinks.length > 0) {
    console.log('\n' + chalk.bold('Top Internal Links (first 10):'));
    result.internalLinks.slice(0, 10).forEach(link => {
      const text = link.text.length > 40 ? link.text.substring(0, 40) + '...' : link.text;
      console.log(chalk.gray(`  → ${text}`));
    });
  }

  // External links
  if (result.externalLinks.length > 0) {
    console.log('\n' + chalk.bold('External Links:'));
    result.externalLinks.slice(0, 5).forEach(link => {
      const domain = new URL(link.href).hostname;
      const nfTag = link.isNoFollow ? chalk.yellow(' [nofollow]') : '';
      console.log(chalk.gray(`  → ${domain}${nfTag}`));
    });
  }

  // Warnings
  if (result.warnings.length > 0) {
    console.log('\n' + chalk.bold('Warnings:'));
    result.warnings.forEach(warn => {
      console.log(chalk.yellow(`  ⚠ ${warn}`));
    });
  }
}

function printScoreResult(result: ScoringResult): void {
  console.log(chalk.bold('\n╔══════════════════════════════════════╗'));
  console.log(chalk.bold('║       SEO AUDIT SCORE SUMMARY        ║'));
  console.log(chalk.bold('╚══════════════════════════════════════╝\n'));

  // Overall score with color coding
  const scoreColor =
    result.percentage >= 80
      ? chalk.green
      : result.percentage >= 60
        ? chalk.yellow
        : chalk.red;

  console.log(
    chalk.bold('Overall Score: ') +
      scoreColor(`${result.overallScore}/${result.maxScore} (${result.percentage}%)`)
  );

  // Category breakdown
  console.log('\n' + chalk.bold('Category Scores:'));

  const categories = [result.categories.technical, result.categories.internal];
  categories.forEach((cat) => {
    const catColor =
      cat.percentage >= 80 ? chalk.green : cat.percentage >= 60 ? chalk.yellow : chalk.red;
    const bar = '█'.repeat(Math.floor(cat.percentage / 10)) + '░'.repeat(10 - Math.floor(cat.percentage / 10));
    console.log(`  ${chalk.cyan(cat.name.padEnd(15))} ${bar} ${catColor(`${cat.percentage}%`)}`);
  });

  // Top recommendations
  if (result.recommendations.length > 0) {
    console.log('\n' + chalk.bold('Priority Recommendations:'));

    const topRecs = result.recommendations.slice(0, 5);
    topRecs.forEach((rec) => {
      const quadrantColor =
        rec.quadrant === 'quick-win'
          ? chalk.green
          : rec.quadrant === 'strategic'
            ? chalk.blue
            : rec.quadrant === 'fill-in'
              ? chalk.gray
              : chalk.dim;

      const quadrantLabel = {
        'quick-win': '⚡ Quick Win',
        strategic: '📋 Strategic',
        'fill-in': '📝 Fill-in',
        'low-priority': '⏳ Low Priority',
      }[rec.quadrant];

      console.log(`  ${chalk.yellow(`#${rec.priority}`)} ${rec.issue}`);
      console.log(chalk.gray(`     → ${rec.action}`));
      console.log(`     ${quadrantColor(quadrantLabel)}`);
    });
  }

  // Score grade
  console.log('\n' + chalk.bold('Grade: ') + getGrade(result.percentage));
}

function getGrade(percentage: number): string {
  if (percentage >= 90) return chalk.green.bold('A+ Excellent');
  if (percentage >= 80) return chalk.green('A Good');
  if (percentage >= 70) return chalk.yellow('B Above Average');
  if (percentage >= 60) return chalk.yellow('C Average');
  if (percentage >= 50) return chalk.red('D Below Average');
  return chalk.red.bold('F Needs Improvement');
}

// ============================================
// SEO Framework Search Commands
// ============================================

// Search command
program
  .command('search')
  .description('Search SEO framework (page-types, intents, llm-tactics)')
  .argument('<query>', 'Search query')
  .option('-d, --domain <type>', 'Filter by domain (page-type, intent, llm)', '')
  .option('-l, --limit <number>', 'Number of results', '5')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .action(async (query: string, options) => {
    const domain = options.domain as DatasetType | undefined;
    const limit = parseInt(options.limit);

    const results = searchSEOFramework(query, {
      dataset: domain || undefined,
      limit,
    });

    if (options.format === 'json') {
      console.log(JSON.stringify(results, null, 2));
    } else {
      printSearchResults(query, results);
    }
  });

// Analyze page command
program
  .command('analyze:page')
  .description('Analyze page type and search intent from URL')
  .argument('<url>', 'URL to analyze')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Analyzing page...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      // Fetch page title
      const puppeteer = await import('puppeteer');
      const browser = await puppeteer.launch({ headless: true });
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

      const title = await page.title();
      const h1 = await page.$eval('h1', el => el.textContent).catch(() => '');
      const h2List = await page.$$eval('h2', els => els.map(el => el.textContent || '').slice(0, 5));
      const faqCount = await page.$$eval('[itemtype*="FAQPage"], [itemtype*="Question"]', els => els.length);
      const schemaScripts = await page.$$eval('script[type="application/ld+json"]', els => els.length);

      await browser.close();

      // Detect page type and intent
      const searchText = [url, title, h1].filter(Boolean).join(' ');
      const pageTypeResults = detectPageType(url, title);
      const intentResults = detectSearchIntent(searchText);
      const llmTactics = findLLMTactics(searchText);

      const analysis = {
        url,
        title,
        h1,
        h2Count: h2List.length,
        faqCount,
        schemaCount: schemaScripts,
        pageType: pageTypeResults[0]?.document.data as PageType | undefined,
        searchIntent: intentResults[0]?.document.data as SearchIntent | undefined,
        relevantLLMTactics: llmTactics.slice(0, 3).map(r => r.document.data as LLMTactic),
      };

      if (options.format === 'json') {
        console.log(JSON.stringify(analysis, null, 2));
      } else {
        printPageAnalysis(analysis);
      }
    } catch (error) {
      console.error(chalk.red('Analysis failed:'), error);
      process.exit(1);
    }
  });

// Generate page comment command
program
  .command('generate:comment')
  .description('Generate SEO meta comment for page header')
  .argument('<url>', 'URL to analyze')
  .option('-k, --keywords <keywords>', 'Target keywords (comma-separated)', '')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Generating SEO comment...'));

    try {
      const puppeteer = await import('puppeteer');
      const browser = await puppeteer.launch({ headless: true });
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

      const title = await page.title();
      await browser.close();

      const searchText = [url, title].filter(Boolean).join(' ');
      const pageTypeResults = detectPageType(url, title);
      const intentResults = detectSearchIntent(searchText);

      const pageType = pageTypeResults[0]?.document.data as PageType | undefined;
      const intent = intentResults[0]?.document.data as SearchIntent | undefined;

      const keywords = options.keywords
        ? options.keywords.split(',').map((k: string) => k.trim())
        : [];

      const comment = generateSEOComment({
        pageType: pageType?.page_type || 'unknown',
        searchIntent: intent?.intent || 'unknown',
        targetKeywords: keywords,
        llmStrategy: pageType?.llm_focus === 'high' ? 'structured-answer' : 'basic',
        schemaRequired: pageType?.optimal_schema || [],
      });

      console.log('\n' + chalk.bold('Generated SEO Comment:'));
      console.log(chalk.gray('─'.repeat(50)));
      console.log(comment);
      console.log(chalk.gray('─'.repeat(50)));
    } catch (error) {
      console.error(chalk.red('Comment generation failed:'), error);
      process.exit(1);
    }
  });

// Check LLM optimization command
program
  .command('check:llm')
  .description('Check LLM optimization status of a page')
  .argument('<url>', 'URL to check')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .action(async (url: string, options) => {
    console.log(chalk.blue('Checking LLM optimization...'));
    console.log(chalk.gray(`Target: ${url}`));

    try {
      const puppeteer = await import('puppeteer');
      const browser = await puppeteer.launch({ headless: true });
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

      // Check various LLM optimization factors
      const checks = {
        faqSchema: await page.$('[itemtype*="FAQPage"]') !== null ||
          await page.$$eval('script[type="application/ld+json"]', els =>
            els.some(el => el.textContent?.includes('FAQPage'))
          ),
        structuredAnswers: await page.$$eval('h2', els =>
          els.some(el => /\?|とは|方法|やり方/.test(el.textContent || ''))
        ),
        authorSchema: await page.$$eval('script[type="application/ld+json"]', els =>
          els.some(el => el.textContent?.includes('Person') && el.textContent?.includes('author'))
        ),
        citations: await page.$$eval('cite, blockquote, [class*="citation"], [class*="source"]', els => els.length),
        dateModified: await page.$('meta[property="article:modified_time"]') !== null ||
          await page.$('time[datetime]') !== null,
        tldr: await page.$$eval('*', els =>
          els.some(el => /TL;DR|要約|まとめ|ポイント/.test(el.textContent || ''))
        ),
        tables: await page.$$eval('table', els => els.length),
        lists: await page.$$eval('ul, ol', els => els.length),
      };

      await browser.close();

      const tactics = loadLLMTactics();
      const results = tactics.map(tactic => {
        let passed = false;
        switch (tactic.tactic) {
          case 'structured-answer': passed = checks.structuredAnswers; break;
          case 'faq-schema': passed = checks.faqSchema; break;
          case 'author-schema': passed = checks.authorSchema; break;
          case 'citation-markup': passed = checks.citations > 0; break;
          case 'date-freshness': passed = checks.dateModified; break;
          case 'tl-dr': passed = checks.tldr; break;
          case 'table-data': passed = checks.tables > 0; break;
          case 'list-format': passed = checks.lists >= 3; break;
          default: passed = false;
        }
        return { tactic, passed };
      });

      const score = Math.round((results.filter(r => r.passed).length / results.length) * 100);

      if (options.format === 'json') {
        console.log(JSON.stringify({ url, score, checks: results }, null, 2));
      } else {
        printLLMCheck(url, score, results);
      }
    } catch (error) {
      console.error(chalk.red('LLM check failed:'), error);
      process.exit(1);
    }
  });

// List all page types/intents/tactics
program
  .command('list')
  .description('List all page types, search intents, or LLM tactics')
  .argument('<type>', 'Type to list (page-types, intents, llm-tactics)')
  .option('-f, --format <type>', 'Output format (json, console)', 'console')
  .action(async (type: string, options) => {
    let data: unknown[];

    switch (type) {
      case 'page-types':
        data = loadPageTypes();
        break;
      case 'intents':
        data = loadSearchIntents();
        break;
      case 'llm-tactics':
        data = loadLLMTactics();
        break;
      default:
        console.error(chalk.red(`Unknown type: ${type}. Use: page-types, intents, llm-tactics`));
        process.exit(1);
    }

    if (options.format === 'json') {
      console.log(JSON.stringify(data, null, 2));
    } else {
      printListResults(type, data);
    }
  });

// Helper functions for new commands
function printSearchResults(query: string, results: SearchResult[]): void {
  console.log(chalk.bold(`\n=== Search Results for "${query}" ===\n`));

  if (results.length === 0) {
    console.log(chalk.yellow('No results found.'));
    return;
  }

  results.forEach((result, index) => {
    const { document, score, matchedTerms } = result;
    const datasetColor = {
      'page-type': chalk.blue,
      'intent': chalk.green,
      'llm': chalk.magenta,
    }[document.dataset];

    console.log(`${chalk.bold(`#${index + 1}`)} ${datasetColor(`[${document.dataset}]`)} ${chalk.cyan(document.id.split(':')[1])}`);
    console.log(chalk.gray(`   Score: ${score.toFixed(2)} | Matched: ${matchedTerms.join(', ')}`));

    // Print summary based on type
    if (document.dataset === 'page-type') {
      const pt = document.data as PageType;
      console.log(`   ${pt.description}`);
      console.log(chalk.gray(`   LLM Focus: ${pt.llm_focus} | CTA: ${pt.cta_style}`));
    } else if (document.dataset === 'intent') {
      const si = document.data as SearchIntent;
      console.log(`   ${si.description}`);
      console.log(chalk.gray(`   AI Priority: ${si.ai_priority} | Type: ${si.content_type}`));
    } else {
      const lt = document.data as LLMTactic;
      console.log(`   ${lt.description}`);
      console.log(chalk.gray(`   Priority: ${lt.priority} | Platforms: ${lt.ai_platforms.join(', ')}`));
    }
    console.log('');
  });
}

function printPageAnalysis(analysis: {
  url: string;
  title: string;
  h1: string;
  h2Count: number;
  faqCount: number;
  schemaCount: number;
  pageType?: PageType;
  searchIntent?: SearchIntent;
  relevantLLMTactics: LLMTactic[];
}): void {
  console.log(chalk.bold('\n╔══════════════════════════════════════╗'));
  console.log(chalk.bold('║         PAGE ANALYSIS REPORT         ║'));
  console.log(chalk.bold('╚══════════════════════════════════════╝\n'));

  console.log(chalk.cyan('URL:'), analysis.url);
  console.log(chalk.cyan('Title:'), analysis.title);
  console.log(chalk.cyan('H1:'), analysis.h1 || '(none)');
  console.log(chalk.cyan('H2 Count:'), analysis.h2Count);
  console.log(chalk.cyan('FAQ Elements:'), analysis.faqCount);
  console.log(chalk.cyan('Schema Scripts:'), analysis.schemaCount);

  console.log('\n' + chalk.bold('Detected Page Type:'));
  if (analysis.pageType) {
    console.log(`  ${chalk.green(analysis.pageType.page_type)}`);
    console.log(chalk.gray(`  ${analysis.pageType.description}`));
    console.log(`  LLM Focus: ${analysis.pageType.llm_focus} | CTA Style: ${analysis.pageType.cta_style}`);
    console.log(`  Required: ${analysis.pageType.required_elements.join(', ')}`);
  } else {
    console.log(chalk.yellow('  Unable to detect page type'));
  }

  console.log('\n' + chalk.bold('Detected Search Intent:'));
  if (analysis.searchIntent) {
    console.log(`  ${chalk.green(analysis.searchIntent.intent)} (${analysis.searchIntent.google_intent})`);
    console.log(chalk.gray(`  ${analysis.searchIntent.description}`));
    console.log(`  Content Type: ${analysis.searchIntent.content_type} | AI Priority: ${analysis.searchIntent.ai_priority}`);
  } else {
    console.log(chalk.yellow('  Unable to detect search intent'));
  }

  console.log('\n' + chalk.bold('Relevant LLM Tactics:'));
  analysis.relevantLLMTactics.forEach((tactic, i) => {
    const priorityColor = {
      'p0': chalk.red,
      'p1': chalk.yellow,
      'p2': chalk.blue,
      'p3': chalk.gray,
    }[tactic.priority];
    console.log(`  ${i + 1}. ${priorityColor(`[${tactic.priority}]`)} ${tactic.tactic}`);
    console.log(chalk.gray(`     ${tactic.implementation.substring(0, 60)}...`));
  });
}

function generateSEOComment(config: {
  pageType: string;
  searchIntent: string;
  targetKeywords: string[];
  llmStrategy: string;
  schemaRequired: string[];
}): string {
  const today = new Date().toISOString().split('T')[0];
  return `/**
 * @seo-meta
 * page-type: ${config.pageType}
 * search-intent: ${config.searchIntent}
 * target-keywords: [${config.targetKeywords.map(k => `"${k}"`).join(', ')}]
 * llm-strategy: ${config.llmStrategy}
 * schema-required: [${config.schemaRequired.join(', ')}]
 * last-audit: ${today}
 */`;
}

function printLLMCheck(url: string, score: number, results: { tactic: LLMTactic; passed: boolean }[]): void {
  console.log(chalk.bold('\n=== LLM Optimization Check ===\n'));
  console.log(chalk.cyan('URL:'), url);

  const scoreColor = score >= 70 ? chalk.green : score >= 40 ? chalk.yellow : chalk.red;
  console.log(chalk.bold('Score:'), scoreColor(`${score}/100`));

  console.log('\n' + chalk.bold('Tactics Status:'));
  results.forEach(({ tactic, passed }) => {
    const icon = passed ? chalk.green('✓') : chalk.red('✗');
    const priorityColor = {
      'p0': chalk.red,
      'p1': chalk.yellow,
      'p2': chalk.blue,
      'p3': chalk.gray,
    }[tactic.priority];

    console.log(`  ${icon} ${priorityColor(`[${tactic.priority}]`)} ${tactic.tactic}`);
    if (!passed) {
      console.log(chalk.gray(`     → ${tactic.implementation.substring(0, 60)}...`));
    }
  });

  // Priority recommendations
  const missing = results.filter(r => !r.passed && (r.tactic.priority === 'p0' || r.tactic.priority === 'p1'));
  if (missing.length > 0) {
    console.log('\n' + chalk.bold.red('Priority Recommendations:'));
    missing.forEach(({ tactic }) => {
      console.log(`  • ${tactic.tactic}: ${tactic.implementation}`);
    });
  }
}

function printListResults(type: string, data: unknown[]): void {
  console.log(chalk.bold(`\n=== ${type} (${data.length} items) ===\n`));

  if (type === 'page-types') {
    (data as PageType[]).forEach(pt => {
      console.log(chalk.cyan.bold(pt.page_type));
      console.log(chalk.gray(`  ${pt.description}`));
      console.log(`  Keywords: ${pt.keywords.slice(0, 5).join(', ')}...`);
      console.log(`  LLM: ${pt.llm_focus} | CTA: ${pt.cta_style}`);
      console.log('');
    });
  } else if (type === 'intents') {
    (data as SearchIntent[]).forEach(si => {
      console.log(chalk.green.bold(`${si.intent} (${si.google_intent})`));
      console.log(chalk.gray(`  ${si.description}`));
      console.log(`  Keywords: ${si.keywords.slice(0, 5).join(', ')}...`);
      console.log(`  AI Priority: ${si.ai_priority}`);
      console.log('');
    });
  } else if (type === 'llm-tactics') {
    (data as LLMTactic[]).forEach(lt => {
      const priorityColor = { 'p0': chalk.red, 'p1': chalk.yellow, 'p2': chalk.blue, 'p3': chalk.gray }[lt.priority];
      console.log(`${priorityColor(`[${lt.priority}]`)} ${chalk.magenta.bold(lt.tactic)}`);
      console.log(chalk.gray(`  ${lt.description}`));
      console.log(`  Implementation: ${lt.implementation.substring(0, 80)}...`);
      console.log('');
    });
  }
}

program.parse();
