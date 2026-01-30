import type { LighthouseResult } from '../auditors/lighthouse.js';
import type { SchemaAuditResult } from '../auditors/schema.js';
import type { MetaAuditResult } from '../auditors/meta.js';
import type { LinksAuditResult } from '../auditors/links.js';

export interface CategoryScore {
  name: string;
  score: number;
  maxScore: number;
  percentage: number;
  items: ScoreItem[];
}

export interface ScoreItem {
  name: string;
  score: number;
  maxScore: number;
  status: 'good' | 'warning' | 'error';
  message: string;
}

export interface Recommendation {
  priority: number;
  issue: string;
  action: string;
  quadrant: 'quick-win' | 'strategic' | 'fill-in' | 'low-priority';
  impact: number;
  effort: number;
}

export interface ScoringResult {
  url: string;
  timestamp: string;
  overallScore: number;
  maxScore: number;
  percentage: number;
  categories: {
    technical: CategoryScore;
    internal: CategoryScore;
  };
  recommendations: Recommendation[];
}

/**
 * Calculate score from 1-5 scale
 */
function score1to5(value: boolean | number, thresholds?: { good: number; ok: number }): number {
  if (typeof value === 'boolean') {
    return value ? 5 : 1;
  }

  if (thresholds) {
    if (value >= thresholds.good) return 5;
    if (value >= thresholds.ok) return 3;
    return 1;
  }

  return value >= 0.9 ? 5 : value >= 0.5 ? 3 : 1;
}

/**
 * Calculate Technical SEO category score
 */
function calculateTechnicalScore(
  lighthouse: LighthouseResult | null,
  schema: SchemaAuditResult
): CategoryScore {
  const items: ScoreItem[] = [];

  // LCP (if Lighthouse available)
  if (lighthouse) {
    const lcpValue = parseFloat(lighthouse.coreWebVitals.lcp) || 0;
    const lcpScore = lcpValue <= 2.5 ? 5 : lcpValue <= 4 ? 3 : 1;
    items.push({
      name: 'LCP',
      score: lcpScore,
      maxScore: 5,
      status: lcpScore >= 4 ? 'good' : lcpScore >= 3 ? 'warning' : 'error',
      message: `${lighthouse.coreWebVitals.lcp} (target: <2.5s)`,
    });

    // CLS
    const clsValue = parseFloat(lighthouse.coreWebVitals.cls) || 0;
    const clsScore = clsValue <= 0.1 ? 5 : clsValue <= 0.25 ? 3 : 1;
    items.push({
      name: 'CLS',
      score: clsScore,
      maxScore: 5,
      status: clsScore >= 4 ? 'good' : clsScore >= 3 ? 'warning' : 'error',
      message: `${lighthouse.coreWebVitals.cls} (target: <0.1)`,
    });

    // Performance score
    const perfScore = score1to5(lighthouse.performance);
    items.push({
      name: 'Performance',
      score: perfScore,
      maxScore: 5,
      status: perfScore >= 4 ? 'good' : perfScore >= 3 ? 'warning' : 'error',
      message: `Lighthouse score: ${Math.round(lighthouse.performance * 100)}`,
    });

    // Accessibility score
    const a11yScore = score1to5(lighthouse.accessibility);
    items.push({
      name: 'Accessibility',
      score: a11yScore,
      maxScore: 5,
      status: a11yScore >= 4 ? 'good' : a11yScore >= 3 ? 'warning' : 'error',
      message: `Lighthouse score: ${Math.round(lighthouse.accessibility * 100)}`,
    });
  }

  // Structured data
  const schemaScore =
    schema.schemasFound === 0 ? 1 : schema.summary.invalid > 0 ? 3 : schema.summary.warnings > 2 ? 4 : 5;
  items.push({
    name: 'Structured Data',
    score: schemaScore,
    maxScore: 5,
    status: schemaScore >= 4 ? 'good' : schemaScore >= 3 ? 'warning' : 'error',
    message: `${schema.schemasFound} schemas found, ${schema.summary.invalid} invalid`,
  });

  const totalScore = items.reduce((sum, item) => sum + item.score, 0);
  const maxScore = items.reduce((sum, item) => sum + item.maxScore, 0);

  return {
    name: 'Technical SEO',
    score: totalScore,
    maxScore,
    percentage: Math.round((totalScore / maxScore) * 100),
    items,
  };
}

/**
 * Calculate Internal SEO category score
 */
function calculateInternalScore(meta: MetaAuditResult, links: LinksAuditResult): CategoryScore {
  const items: ScoreItem[] = [];

  // Title
  const titleScore = meta.title.status === 'good' ? 5 : meta.title.status === 'missing' ? 1 : 3;
  items.push({
    name: 'Title Tag',
    score: titleScore,
    maxScore: 5,
    status: titleScore >= 4 ? 'good' : titleScore >= 3 ? 'warning' : 'error',
    message: meta.title.status === 'missing' ? 'Missing' : `${meta.title.length} chars (${meta.title.status})`,
  });

  // Meta description
  const descScore =
    meta.description.status === 'good' ? 5 : meta.description.status === 'missing' ? 1 : 3;
  items.push({
    name: 'Meta Description',
    score: descScore,
    maxScore: 5,
    status: descScore >= 4 ? 'good' : descScore >= 3 ? 'warning' : 'error',
    message:
      meta.description.status === 'missing'
        ? 'Missing'
        : `${meta.description.length} chars (${meta.description.status})`,
  });

  // Canonical
  const canonicalScore = meta.canonical.value ? 5 : 1;
  items.push({
    name: 'Canonical URL',
    score: canonicalScore,
    maxScore: 5,
    status: canonicalScore >= 4 ? 'good' : 'error',
    message: meta.canonical.value ? 'Set' : 'Missing',
  });

  // H1
  const h1Score = meta.h1.status === 'good' ? 5 : meta.h1.status === 'multiple' ? 3 : 1;
  items.push({
    name: 'H1 Heading',
    score: h1Score,
    maxScore: 5,
    status: h1Score >= 4 ? 'good' : h1Score >= 3 ? 'warning' : 'error',
    message: `${meta.h1.count} found (${meta.h1.status})`,
  });

  // Mobile viewport
  const vpScore = meta.viewport.isMobileFriendly ? 5 : 1;
  items.push({
    name: 'Mobile Viewport',
    score: vpScore,
    maxScore: 5,
    status: vpScore >= 4 ? 'good' : 'error',
    message: meta.viewport.isMobileFriendly ? 'Mobile-friendly' : 'Not configured',
  });

  // Internal links
  const internalLinkScore =
    links.summary.internal >= 10 ? 5 : links.summary.internal >= 5 ? 4 : links.summary.internal >= 2 ? 3 : 1;
  items.push({
    name: 'Internal Links',
    score: internalLinkScore,
    maxScore: 5,
    status: internalLinkScore >= 4 ? 'good' : internalLinkScore >= 3 ? 'warning' : 'error',
    message: `${links.summary.internal} internal links`,
  });

  // Open Graph
  const ogScore = meta.openGraph.complete ? 5 : meta.openGraph.title ? 3 : 1;
  items.push({
    name: 'Open Graph',
    score: ogScore,
    maxScore: 5,
    status: ogScore >= 4 ? 'good' : ogScore >= 3 ? 'warning' : 'error',
    message: meta.openGraph.complete ? 'Complete' : 'Incomplete',
  });

  const totalScore = items.reduce((sum, item) => sum + item.score, 0);
  const maxScore = items.reduce((sum, item) => sum + item.maxScore, 0);

  return {
    name: 'Internal SEO',
    score: totalScore,
    maxScore,
    percentage: Math.round((totalScore / maxScore) * 100),
    items,
  };
}

/**
 * Determine quadrant based on impact and effort
 */
function getQuadrant(impact: number, effort: number): Recommendation['quadrant'] {
  if (impact >= 4 && effort <= 2) return 'quick-win';
  if (impact >= 4 && effort > 2) return 'strategic';
  if (impact < 4 && effort <= 2) return 'fill-in';
  return 'low-priority';
}

/**
 * Generate recommendations based on audit results
 */
function generateRecommendations(
  lighthouse: LighthouseResult | null,
  schema: SchemaAuditResult,
  meta: MetaAuditResult,
  links: LinksAuditResult
): Recommendation[] {
  const recommendations: Recommendation[] = [];

  // Meta tag issues
  if (meta.title.status === 'missing') {
    recommendations.push({
      priority: 0,
      issue: 'Missing title tag',
      action: 'Add title tag (30-60 chars)',
      quadrant: 'quick-win',
      impact: 5,
      effort: 1,
    });
  } else if (meta.title.status !== 'good') {
    recommendations.push({
      priority: 0,
      issue: `Title ${meta.title.status} (${meta.title.length} chars)`,
      action: 'Optimize title length (30-60 chars)',
      quadrant: 'quick-win',
      impact: 4,
      effort: 1,
    });
  }

  if (meta.description.status === 'missing') {
    recommendations.push({
      priority: 0,
      issue: 'Missing meta description',
      action: 'Add meta description (70-160 chars)',
      quadrant: 'quick-win',
      impact: 5,
      effort: 1,
    });
  } else if (meta.description.status !== 'good') {
    recommendations.push({
      priority: 0,
      issue: `Description ${meta.description.status} (${meta.description.length} chars)`,
      action: 'Optimize description length (70-160 chars)',
      quadrant: 'quick-win',
      impact: 3,
      effort: 1,
    });
  }

  if (!meta.canonical.value) {
    recommendations.push({
      priority: 0,
      issue: 'Missing canonical URL',
      action: 'Add canonical link tag',
      quadrant: 'quick-win',
      impact: 4,
      effort: 1,
    });
  }

  if (meta.h1.status === 'missing') {
    recommendations.push({
      priority: 0,
      issue: 'Missing H1 heading',
      action: 'Add H1 heading with main keyword',
      quadrant: 'quick-win',
      impact: 5,
      effort: 1,
    });
  } else if (meta.h1.status === 'multiple') {
    recommendations.push({
      priority: 0,
      issue: `Multiple H1 headings (${meta.h1.count})`,
      action: 'Use only one H1 per page',
      quadrant: 'quick-win',
      impact: 3,
      effort: 2,
    });
  }

  if (!meta.viewport.isMobileFriendly) {
    recommendations.push({
      priority: 0,
      issue: 'Not mobile-friendly',
      action: 'Add viewport meta tag with width=device-width',
      quadrant: 'quick-win',
      impact: 5,
      effort: 1,
    });
  }

  if (!meta.openGraph.complete) {
    recommendations.push({
      priority: 0,
      issue: 'Incomplete Open Graph tags',
      action: 'Add og:title, og:description, og:image',
      quadrant: 'fill-in',
      impact: 2,
      effort: 1,
    });
  }

  // Schema issues
  if (schema.schemasFound === 0) {
    recommendations.push({
      priority: 0,
      issue: 'No structured data found',
      action: 'Add JSON-LD structured data (Organization, WebPage)',
      quadrant: 'strategic',
      impact: 4,
      effort: 3,
    });
  } else if (schema.summary.invalid > 0) {
    recommendations.push({
      priority: 0,
      issue: `${schema.summary.invalid} invalid schema(s)`,
      action: 'Fix structured data validation errors',
      quadrant: 'quick-win',
      impact: 4,
      effort: 2,
    });
  }

  // Links issues
  if (links.summary.internal < 3) {
    recommendations.push({
      priority: 0,
      issue: `Low internal link count (${links.summary.internal})`,
      action: 'Add more internal links to related content',
      quadrant: 'fill-in',
      impact: 3,
      effort: 2,
    });
  }

  if (links.summary.emptyText > 0) {
    recommendations.push({
      priority: 0,
      issue: `${links.summary.emptyText} link(s) with empty text`,
      action: 'Add descriptive anchor text to links',
      quadrant: 'quick-win',
      impact: 3,
      effort: 1,
    });
  }

  // Lighthouse issues
  if (lighthouse) {
    const lcpValue = parseFloat(lighthouse.coreWebVitals.lcp) || 0;
    if (lcpValue > 2.5) {
      recommendations.push({
        priority: 0,
        issue: `Slow LCP (${lighthouse.coreWebVitals.lcp})`,
        action: 'Optimize largest content element loading',
        quadrant: 'strategic',
        impact: 5,
        effort: 4,
      });
    }

    const clsValue = parseFloat(lighthouse.coreWebVitals.cls) || 0;
    if (clsValue > 0.1) {
      recommendations.push({
        priority: 0,
        issue: `High CLS (${lighthouse.coreWebVitals.cls})`,
        action: 'Fix layout shifts (set image dimensions, reserve space)',
        quadrant: 'strategic',
        impact: 4,
        effort: 3,
      });
    }

    if (lighthouse.performance < 0.5) {
      recommendations.push({
        priority: 0,
        issue: `Low performance score (${Math.round(lighthouse.performance * 100)})`,
        action: 'Improve page speed (compress images, minify code)',
        quadrant: 'strategic',
        impact: 5,
        effort: 4,
      });
    }
  }

  // Calculate priority scores and sort
  recommendations.forEach((rec) => {
    rec.priority = rec.impact * 2 + 5 - rec.effort;
  });

  recommendations.sort((a, b) => b.priority - a.priority);

  // Re-number priorities
  recommendations.forEach((rec, index) => {
    rec.priority = index + 1;
  });

  return recommendations;
}

/**
 * Calculate overall SEO score from audit results
 */
export function calculateScore(
  lighthouse: LighthouseResult | null,
  schema: SchemaAuditResult,
  meta: MetaAuditResult,
  links: LinksAuditResult
): ScoringResult {
  const technical = calculateTechnicalScore(lighthouse, schema);
  const internal = calculateInternalScore(meta, links);

  const overallScore = technical.score + internal.score;
  const maxScore = technical.maxScore + internal.maxScore;

  const recommendations = generateRecommendations(lighthouse, schema, meta, links);

  return {
    url: meta.url,
    timestamp: new Date().toISOString(),
    overallScore,
    maxScore,
    percentage: Math.round((overallScore / maxScore) * 100),
    categories: {
      technical,
      internal,
    },
    recommendations,
  };
}
