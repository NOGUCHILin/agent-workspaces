import lighthouse from 'lighthouse';
import puppeteer from 'puppeteer';

export interface LighthouseResult {
  url: string;
  timestamp: string;
  performance: number;
  seo: number;
  accessibility: number;
  bestPractices: number;
  coreWebVitals: {
    lcp: string;
    inp: string;
    cls: string;
  };
  seoAudits: Array<{
    id: string;
    title: string;
    description: string;
    passed: boolean;
  }>;
}

export async function runLighthouseAudit(url: string): Promise<LighthouseResult> {
  // Launch browser
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const endpoint = browser.wsEndpoint();
    const endpointURL = new URL(endpoint);

    // Run Lighthouse
    const result = await lighthouse(url, {
      port: parseInt(endpointURL.port),
      output: 'json',
      logLevel: 'error',
      onlyCategories: ['performance', 'seo', 'accessibility', 'best-practices'],
    });

    if (!result || !result.lhr) {
      throw new Error('Lighthouse audit failed to produce results');
    }

    const { lhr } = result;

    // Extract Core Web Vitals
    const lcpAudit = lhr.audits['largest-contentful-paint'];
    const clsAudit = lhr.audits['cumulative-layout-shift'];
    const inpAudit = lhr.audits['interaction-to-next-paint'] || lhr.audits['total-blocking-time'];

    // Extract SEO audits
    const seoCategory = lhr.categories['seo'];
    const seoAudits = seoCategory?.auditRefs
      ?.filter(ref => ref.weight > 0)
      .map(ref => {
        const audit = lhr.audits[ref.id];
        return {
          id: ref.id,
          title: audit?.title || ref.id,
          description: audit?.description || '',
          passed: audit?.score === 1,
        };
      }) || [];

    return {
      url,
      timestamp: new Date().toISOString(),
      performance: lhr.categories['performance']?.score || 0,
      seo: lhr.categories['seo']?.score || 0,
      accessibility: lhr.categories['accessibility']?.score || 0,
      bestPractices: lhr.categories['best-practices']?.score || 0,
      coreWebVitals: {
        lcp: lcpAudit?.displayValue || 'N/A',
        inp: inpAudit?.displayValue || 'N/A',
        cls: clsAudit?.displayValue || 'N/A',
      },
      seoAudits,
    };
  } finally {
    await browser.close();
  }
}
