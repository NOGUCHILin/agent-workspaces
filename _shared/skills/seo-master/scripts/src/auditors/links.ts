import * as cheerio from 'cheerio';

export interface LinkInfo {
  href: string;
  text: string;
  isInternal: boolean;
  isNoFollow: boolean;
  hasEmptyText: boolean;
}

export interface LinksAuditResult {
  url: string;
  timestamp: string;
  summary: {
    total: number;
    internal: number;
    external: number;
    noFollow: number;
    emptyText: number;
  };
  internalLinks: LinkInfo[];
  externalLinks: LinkInfo[];
  issues: string[];
  warnings: string[];
}

/**
 * Parse URL to get base domain
 */
function getBaseDomain(urlString: string): string {
  try {
    const url = new URL(urlString);
    return url.hostname;
  } catch {
    return '';
  }
}

/**
 * Check if URL is internal relative to base URL
 */
function isInternalLink(href: string, baseUrl: string): boolean {
  if (!href) return false;

  // Skip non-http links
  if (href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) {
    return false;
  }

  // Relative URLs are internal
  if (href.startsWith('/') || href.startsWith('#') || href.startsWith('./') || href.startsWith('../')) {
    return true;
  }

  // Compare domains
  const baseDomain = getBaseDomain(baseUrl);
  const linkDomain = getBaseDomain(href);

  if (!linkDomain) return true; // Probably relative

  // Check if same domain or subdomain
  return linkDomain === baseDomain || linkDomain.endsWith('.' + baseDomain);
}

/**
 * Normalize link href to absolute URL
 */
function normalizeHref(href: string, baseUrl: string): string {
  if (!href) return '';

  try {
    // Already absolute
    if (href.startsWith('http://') || href.startsWith('https://')) {
      return href;
    }

    // Make absolute
    const base = new URL(baseUrl);

    if (href.startsWith('//')) {
      return base.protocol + href;
    }

    if (href.startsWith('/')) {
      return base.origin + href;
    }

    if (href.startsWith('#')) {
      return baseUrl + href;
    }

    // Relative path
    return new URL(href, baseUrl).href;
  } catch {
    return href;
  }
}

/**
 * Run links audit on a URL
 */
export async function runLinksAudit(url: string): Promise<LinksAuditResult> {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; SEO-Audit-Bot/1.0)',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }

  const html = await response.text();
  const $ = cheerio.load(html);
  const issues: string[] = [];
  const warnings: string[] = [];

  const internalLinks: LinkInfo[] = [];
  const externalLinks: LinkInfo[] = [];
  let noFollowCount = 0;
  let emptyTextCount = 0;

  // Analyze all anchor tags
  $('a[href]').each((_, el) => {
    const $el = $(el);
    const href = $el.attr('href')?.trim() || '';
    const text = $el.text().trim();
    const rel = $el.attr('rel')?.toLowerCase() || '';

    // Skip anchor links, mailto, tel, javascript
    if (!href || href === '#' || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) {
      return;
    }

    const normalizedHref = normalizeHref(href, url);
    const isInternal = isInternalLink(href, url);
    const isNoFollow = rel.includes('nofollow');
    const hasEmptyText = !text && !$el.find('img[alt]').length;

    if (isNoFollow) noFollowCount++;
    if (hasEmptyText) emptyTextCount++;

    const linkInfo: LinkInfo = {
      href: normalizedHref,
      text: text || $el.find('img').attr('alt') || '[no text]',
      isInternal,
      isNoFollow,
      hasEmptyText,
    };

    if (isInternal) {
      internalLinks.push(linkInfo);
    } else {
      externalLinks.push(linkInfo);
    }
  });

  // Generate issues and warnings
  if (internalLinks.length === 0) {
    warnings.push('No internal links found');
  }

  if (emptyTextCount > 0) {
    warnings.push(`${emptyTextCount} link(s) with empty anchor text`);
  }

  // Check for duplicate internal links (same href)
  const internalHrefs = internalLinks.map(l => l.href);
  const uniqueInternalHrefs = new Set(internalHrefs);
  if (internalHrefs.length > uniqueInternalHrefs.size) {
    const duplicateCount = internalHrefs.length - uniqueInternalHrefs.size;
    warnings.push(`${duplicateCount} duplicate internal link(s) found`);
  }

  // External link ratio warning
  const totalLinks = internalLinks.length + externalLinks.length;
  if (totalLinks > 0) {
    const externalRatio = externalLinks.length / totalLinks;
    if (externalRatio > 0.5) {
      warnings.push(`High external link ratio (${Math.round(externalRatio * 100)}%)`);
    }
  }

  return {
    url,
    timestamp: new Date().toISOString(),
    summary: {
      total: internalLinks.length + externalLinks.length,
      internal: internalLinks.length,
      external: externalLinks.length,
      noFollow: noFollowCount,
      emptyText: emptyTextCount,
    },
    internalLinks,
    externalLinks,
    issues,
    warnings,
  };
}
