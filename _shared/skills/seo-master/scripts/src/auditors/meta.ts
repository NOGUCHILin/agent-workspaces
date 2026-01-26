import * as cheerio from 'cheerio';

export interface MetaAuditResult {
  url: string;
  timestamp: string;
  title: {
    value: string | null;
    length: number;
    status: 'good' | 'too_short' | 'too_long' | 'missing';
  };
  description: {
    value: string | null;
    length: number;
    status: 'good' | 'too_short' | 'too_long' | 'missing';
  };
  robots: {
    value: string | null;
    isIndexable: boolean;
    isFollowable: boolean;
  };
  canonical: {
    value: string | null;
    isSelfReferencing: boolean;
  };
  openGraph: {
    title: string | null;
    description: string | null;
    image: string | null;
    type: string | null;
    complete: boolean;
  };
  viewport: {
    value: string | null;
    isMobileFriendly: boolean;
  };
  h1: {
    count: number;
    values: string[];
    status: 'good' | 'missing' | 'multiple';
  };
  issues: string[];
  warnings: string[];
}

// SEO best practice thresholds
const TITLE_MIN = 30;
const TITLE_MAX = 60;
const DESC_MIN = 70;
const DESC_MAX = 160;

/**
 * Run meta tag audit on a URL
 */
export async function runMetaAudit(url: string): Promise<MetaAuditResult> {
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

  // Title analysis
  const titleValue = $('title').first().text().trim() || null;
  const titleLength = titleValue?.length || 0;
  let titleStatus: 'good' | 'too_short' | 'too_long' | 'missing' = 'good';

  if (!titleValue) {
    titleStatus = 'missing';
    issues.push('Missing title tag');
  } else if (titleLength < TITLE_MIN) {
    titleStatus = 'too_short';
    warnings.push(`Title too short (${titleLength} chars, recommended ${TITLE_MIN}-${TITLE_MAX})`);
  } else if (titleLength > TITLE_MAX) {
    titleStatus = 'too_long';
    warnings.push(`Title too long (${titleLength} chars, recommended ${TITLE_MIN}-${TITLE_MAX})`);
  }

  // Description analysis
  const descValue = $('meta[name="description"]').attr('content')?.trim() || null;
  const descLength = descValue?.length || 0;
  let descStatus: 'good' | 'too_short' | 'too_long' | 'missing' = 'good';

  if (!descValue) {
    descStatus = 'missing';
    issues.push('Missing meta description');
  } else if (descLength < DESC_MIN) {
    descStatus = 'too_short';
    warnings.push(`Description too short (${descLength} chars, recommended ${DESC_MIN}-${DESC_MAX})`);
  } else if (descLength > DESC_MAX) {
    descStatus = 'too_long';
    warnings.push(`Description too long (${descLength} chars, recommended ${DESC_MIN}-${DESC_MAX})`);
  }

  // Robots meta
  const robotsValue = $('meta[name="robots"]').attr('content')?.trim() || null;
  const isIndexable = !robotsValue?.toLowerCase().includes('noindex');
  const isFollowable = !robotsValue?.toLowerCase().includes('nofollow');

  if (!isIndexable) {
    warnings.push('Page is set to noindex');
  }

  // Canonical URL
  const canonicalValue = $('link[rel="canonical"]').attr('href')?.trim() || null;
  const isSelfReferencing = canonicalValue === url || canonicalValue === url.replace(/\/$/, '');

  if (!canonicalValue) {
    warnings.push('Missing canonical URL');
  }

  // Open Graph tags
  const ogTitle = $('meta[property="og:title"]').attr('content')?.trim() || null;
  const ogDescription = $('meta[property="og:description"]').attr('content')?.trim() || null;
  const ogImage = $('meta[property="og:image"]').attr('content')?.trim() || null;
  const ogType = $('meta[property="og:type"]').attr('content')?.trim() || null;
  const ogComplete = !!(ogTitle && ogDescription && ogImage);

  if (!ogComplete) {
    warnings.push('Incomplete Open Graph tags (missing: ' +
      [!ogTitle && 'og:title', !ogDescription && 'og:description', !ogImage && 'og:image']
        .filter(Boolean).join(', ') + ')');
  }

  // Viewport
  const viewportValue = $('meta[name="viewport"]').attr('content')?.trim() || null;
  const isMobileFriendly = !!viewportValue?.includes('width=device-width');

  if (!viewportValue) {
    issues.push('Missing viewport meta tag');
  } else if (!isMobileFriendly) {
    warnings.push('Viewport not mobile-friendly (missing width=device-width)');
  }

  // H1 analysis
  const h1Elements = $('h1');
  const h1Values: string[] = [];
  h1Elements.each((_, el) => {
    const text = $(el).text().trim();
    if (text) h1Values.push(text);
  });

  let h1Status: 'good' | 'missing' | 'multiple' = 'good';
  if (h1Values.length === 0) {
    h1Status = 'missing';
    issues.push('Missing H1 heading');
  } else if (h1Values.length > 1) {
    h1Status = 'multiple';
    warnings.push(`Multiple H1 headings found (${h1Values.length})`);
  }

  return {
    url,
    timestamp: new Date().toISOString(),
    title: {
      value: titleValue,
      length: titleLength,
      status: titleStatus,
    },
    description: {
      value: descValue,
      length: descLength,
      status: descStatus,
    },
    robots: {
      value: robotsValue,
      isIndexable,
      isFollowable,
    },
    canonical: {
      value: canonicalValue,
      isSelfReferencing,
    },
    openGraph: {
      title: ogTitle,
      description: ogDescription,
      image: ogImage,
      type: ogType,
      complete: ogComplete,
    },
    viewport: {
      value: viewportValue,
      isMobileFriendly,
    },
    h1: {
      count: h1Values.length,
      values: h1Values,
      status: h1Status,
    },
    issues,
    warnings,
  };
}
