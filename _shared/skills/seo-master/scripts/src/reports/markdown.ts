import type { LighthouseResult } from '../auditors/lighthouse.js';
import type { SchemaAuditResult } from '../auditors/schema.js';
import type { MetaAuditResult } from '../auditors/meta.js';
import type { LinksAuditResult } from '../auditors/links.js';
import type { ScoringResult } from '../scoring/calculator.js';

export interface FullAuditResult {
  url: string;
  timestamp: string;
  lighthouse: LighthouseResult | null;
  schema: SchemaAuditResult;
  meta: MetaAuditResult;
  links: LinksAuditResult;
  score: ScoringResult;
}

/**
 * Generate a Markdown report from full audit results
 */
export function generateMarkdownReport(result: FullAuditResult): string {
  const lines: string[] = [];
  const { score, lighthouse, schema, meta, links } = result;

  // Header
  lines.push(`# SEO Audit Report`);
  lines.push('');
  lines.push(`**URL**: ${result.url}`);
  lines.push(`**Date**: ${new Date(result.timestamp).toLocaleDateString('ja-JP')}`);
  lines.push(`**Time**: ${new Date(result.timestamp).toLocaleTimeString('ja-JP')}`);
  lines.push('');

  // Executive Summary
  lines.push('## Executive Summary');
  lines.push('');
  lines.push(`| Metric | Value |`);
  lines.push(`|--------|-------|`);
  lines.push(`| **Overall Score** | ${score.overallScore}/${score.maxScore} (${score.percentage}%) |`);
  lines.push(`| **Grade** | ${getGradeText(score.percentage)} |`);
  lines.push(`| **Technical SEO** | ${score.categories.technical.percentage}% |`);
  lines.push(`| **Internal SEO** | ${score.categories.internal.percentage}% |`);
  lines.push('');

  // Score Details
  lines.push('## Category Scores');
  lines.push('');

  // Technical SEO
  lines.push('### Technical SEO');
  lines.push('');
  lines.push(`| Item | Score | Status | Details |`);
  lines.push(`|------|-------|--------|---------|`);
  score.categories.technical.items.forEach((item) => {
    const statusEmoji = item.status === 'good' ? '✅' : item.status === 'warning' ? '⚠️' : '❌';
    lines.push(`| ${item.name} | ${item.score}/${item.maxScore} | ${statusEmoji} | ${item.message} |`);
  });
  lines.push('');

  // Internal SEO
  lines.push('### Internal SEO');
  lines.push('');
  lines.push(`| Item | Score | Status | Details |`);
  lines.push(`|------|-------|--------|---------|`);
  score.categories.internal.items.forEach((item) => {
    const statusEmoji = item.status === 'good' ? '✅' : item.status === 'warning' ? '⚠️' : '❌';
    lines.push(`| ${item.name} | ${item.score}/${item.maxScore} | ${statusEmoji} | ${item.message} |`);
  });
  lines.push('');

  // Lighthouse Results (if available)
  if (lighthouse) {
    lines.push('## Core Web Vitals');
    lines.push('');
    lines.push(`| Metric | Value | Target |`);
    lines.push(`|--------|-------|--------|`);
    lines.push(`| LCP | ${lighthouse.coreWebVitals.lcp} | < 2.5s |`);
    lines.push(`| INP | ${lighthouse.coreWebVitals.inp} | < 200ms |`);
    lines.push(`| CLS | ${lighthouse.coreWebVitals.cls} | < 0.1 |`);
    lines.push('');

    lines.push('### Lighthouse Scores');
    lines.push('');
    lines.push(`| Category | Score |`);
    lines.push(`|----------|-------|`);
    lines.push(`| Performance | ${Math.round(lighthouse.performance * 100)} |`);
    lines.push(`| SEO | ${Math.round(lighthouse.seo * 100)} |`);
    lines.push(`| Accessibility | ${Math.round(lighthouse.accessibility * 100)} |`);
    lines.push(`| Best Practices | ${Math.round(lighthouse.bestPractices * 100)} |`);
    lines.push('');
  }

  // Structured Data
  lines.push('## Structured Data');
  lines.push('');
  lines.push(`**Schemas Found**: ${schema.schemasFound}`);
  lines.push(`**Valid**: ${schema.summary.valid} | **Invalid**: ${schema.summary.invalid} | **Warnings**: ${schema.summary.warnings}`);
  lines.push('');

  if (schema.schemas.length > 0) {
    lines.push(`| Type | Status | Issues |`);
    lines.push(`|------|--------|--------|`);
    schema.schemas.forEach((s) => {
      const status = s.valid ? '✅ Valid' : '❌ Invalid';
      const issues = [...s.errors, ...s.warnings.map(w => `⚠️ ${w}`)].join(', ') || '-';
      lines.push(`| ${s.type} | ${status} | ${issues} |`);
    });
    lines.push('');
  }

  // Meta Tags
  lines.push('## Meta Tags');
  lines.push('');
  lines.push(`| Tag | Value | Status |`);
  lines.push(`|-----|-------|--------|`);
  lines.push(`| Title | ${meta.title.value || 'Missing'} | ${getStatusEmoji(meta.title.status)} ${meta.title.length} chars |`);
  lines.push(`| Description | ${meta.description.value?.substring(0, 50) || 'Missing'}... | ${getStatusEmoji(meta.description.status)} ${meta.description.length} chars |`);
  lines.push(`| Canonical | ${meta.canonical.value || 'Not set'} | ${meta.canonical.value ? '✅' : '⚠️'} |`);
  lines.push(`| H1 | ${meta.h1.values[0] || 'Missing'} | ${getStatusEmoji(meta.h1.status)} ${meta.h1.count} found |`);
  lines.push(`| Viewport | ${meta.viewport.isMobileFriendly ? 'Mobile-friendly' : 'Not configured'} | ${meta.viewport.isMobileFriendly ? '✅' : '❌'} |`);
  lines.push(`| Open Graph | ${meta.openGraph.complete ? 'Complete' : 'Incomplete'} | ${meta.openGraph.complete ? '✅' : '⚠️'} |`);
  lines.push('');

  // Links
  lines.push('## Links Analysis');
  lines.push('');
  lines.push(`| Metric | Count |`);
  lines.push(`|--------|-------|`);
  lines.push(`| Total Links | ${links.summary.total} |`);
  lines.push(`| Internal | ${links.summary.internal} |`);
  lines.push(`| External | ${links.summary.external} |`);
  lines.push(`| NoFollow | ${links.summary.noFollow} |`);
  lines.push(`| Empty Text | ${links.summary.emptyText} |`);
  lines.push('');

  // Recommendations
  if (score.recommendations.length > 0) {
    lines.push('## Recommendations');
    lines.push('');
    lines.push(`| Priority | Issue | Action | Type |`);
    lines.push(`|----------|-------|--------|------|`);
    score.recommendations.forEach((rec) => {
      const typeEmoji = {
        'quick-win': '⚡',
        strategic: '📋',
        'fill-in': '📝',
        'low-priority': '⏳',
      }[rec.quadrant];
      lines.push(`| #${rec.priority} | ${rec.issue} | ${rec.action} | ${typeEmoji} ${rec.quadrant} |`);
    });
    lines.push('');
  }

  // Issues and Warnings
  const allIssues = [...meta.issues, ...links.issues];
  const allWarnings = [...meta.warnings, ...links.warnings];

  if (allIssues.length > 0) {
    lines.push('## Issues');
    lines.push('');
    allIssues.forEach((issue) => {
      lines.push(`- ❌ ${issue}`);
    });
    lines.push('');
  }

  if (allWarnings.length > 0) {
    lines.push('## Warnings');
    lines.push('');
    allWarnings.forEach((warning) => {
      lines.push(`- ⚠️ ${warning}`);
    });
    lines.push('');
  }

  // Footer
  lines.push('---');
  lines.push('');
  lines.push('*Generated by SEO Audit Tool*');

  return lines.join('\n');
}

function getGradeText(percentage: number): string {
  if (percentage >= 90) return 'A+ Excellent';
  if (percentage >= 80) return 'A Good';
  if (percentage >= 70) return 'B Above Average';
  if (percentage >= 60) return 'C Average';
  if (percentage >= 50) return 'D Below Average';
  return 'F Needs Improvement';
}

function getStatusEmoji(status: string): string {
  switch (status) {
    case 'good':
      return '✅';
    case 'warning':
    case 'too_short':
    case 'too_long':
    case 'multiple':
      return '⚠️';
    case 'missing':
    case 'error':
      return '❌';
    default:
      return '❓';
  }
}
