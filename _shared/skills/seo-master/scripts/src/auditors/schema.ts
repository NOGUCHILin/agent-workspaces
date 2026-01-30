import * as cheerio from 'cheerio';

export interface SchemaValidationResult {
  type: string;
  valid: boolean;
  errors: string[];
  warnings: string[];
  data: Record<string, unknown>;
}

export interface SchemaAuditResult {
  url: string;
  timestamp: string;
  schemasFound: number;
  schemas: SchemaValidationResult[];
  summary: {
    valid: number;
    invalid: number;
    warnings: number;
  };
}

// Schema.org required/recommended properties
const SCHEMA_REQUIREMENTS: Record<string, { required: string[]; recommended: string[] }> = {
  Article: {
    required: ['headline', 'author', 'datePublished'],
    recommended: ['image', 'dateModified', 'publisher', 'description'],
  },
  NewsArticle: {
    required: ['headline', 'author', 'datePublished'],
    recommended: ['image', 'dateModified', 'publisher', 'description'],
  },
  Product: {
    required: ['name'],
    recommended: ['image', 'description', 'offers', 'brand', 'sku'],
  },
  LocalBusiness: {
    required: ['name', 'address'],
    recommended: ['telephone', 'openingHours', 'image', 'priceRange', 'geo'],
  },
  Organization: {
    required: ['name'],
    recommended: ['logo', 'url', 'contactPoint', 'sameAs'],
  },
  FAQPage: {
    required: ['mainEntity'],
    recommended: [],
  },
  BreadcrumbList: {
    required: ['itemListElement'],
    recommended: [],
  },
  WebPage: {
    required: ['name'],
    recommended: ['description', 'url', 'breadcrumb'],
  },
  WebSite: {
    required: ['name', 'url'],
    recommended: ['potentialAction', 'publisher'],
  },
  Person: {
    required: ['name'],
    recommended: ['image', 'jobTitle', 'worksFor', 'sameAs'],
  },
  Review: {
    required: ['author', 'reviewRating', 'itemReviewed'],
    recommended: ['datePublished', 'reviewBody'],
  },
  AggregateRating: {
    required: ['ratingValue', 'reviewCount'],
    recommended: ['bestRating', 'worstRating'],
  },
  Offer: {
    required: ['price', 'priceCurrency'],
    recommended: ['availability', 'url', 'priceValidUntil'],
  },
  HowTo: {
    required: ['name', 'step'],
    recommended: ['image', 'totalTime', 'tool', 'supply'],
  },
  Recipe: {
    required: ['name', 'recipeIngredient', 'recipeInstructions'],
    recommended: ['image', 'author', 'prepTime', 'cookTime', 'nutrition'],
  },
  Event: {
    required: ['name', 'startDate', 'location'],
    recommended: ['endDate', 'image', 'description', 'performer', 'offers'],
  },
  VideoObject: {
    required: ['name', 'description', 'thumbnailUrl', 'uploadDate'],
    recommended: ['contentUrl', 'embedUrl', 'duration'],
  },
};

/**
 * Extract JSON-LD scripts from HTML
 */
function extractJsonLd(html: string): unknown[] {
  const $ = cheerio.load(html);
  const jsonLdScripts: unknown[] = [];

  $('script[type="application/ld+json"]').each((_, element) => {
    try {
      const content = $(element).html();
      if (content) {
        const parsed = JSON.parse(content);
        // Handle @graph structures
        if (parsed['@graph'] && Array.isArray(parsed['@graph'])) {
          jsonLdScripts.push(...parsed['@graph']);
        } else {
          jsonLdScripts.push(parsed);
        }
      }
    } catch {
      // Invalid JSON - will be reported as error
    }
  });

  return jsonLdScripts;
}

/**
 * Get schema type from JSON-LD object
 */
function getSchemaType(schema: Record<string, unknown>): string {
  const type = schema['@type'];
  if (Array.isArray(type)) {
    return type[0] as string;
  }
  return (type as string) || 'Unknown';
}

/**
 * Check if a property exists in schema (handles nested objects)
 */
function hasProperty(schema: Record<string, unknown>, prop: string): boolean {
  if (prop in schema) {
    const value = schema[prop];
    // Check if value is meaningful (not null, undefined, or empty)
    if (value === null || value === undefined) return false;
    if (typeof value === 'string' && value.trim() === '') return false;
    if (Array.isArray(value) && value.length === 0) return false;
    return true;
  }
  return false;
}

/**
 * Validate a single schema against requirements
 */
function validateSchema(schema: Record<string, unknown>): SchemaValidationResult {
  const type = getSchemaType(schema);
  const requirements = SCHEMA_REQUIREMENTS[type];
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!requirements) {
    // Unknown schema type - just validate basic structure
    if (!schema['@type']) {
      errors.push('Missing @type property');
    }
    return {
      type,
      valid: errors.length === 0,
      errors,
      warnings: [`Unknown schema type: ${type} - limited validation available`],
      data: schema,
    };
  }

  // Check required properties
  for (const prop of requirements.required) {
    if (!hasProperty(schema, prop)) {
      errors.push(`Missing required property: ${prop}`);
    }
  }

  // Check recommended properties
  for (const prop of requirements.recommended) {
    if (!hasProperty(schema, prop)) {
      warnings.push(`Missing recommended property: ${prop}`);
    }
  }

  // Additional type-specific validations
  if (type === 'FAQPage' && hasProperty(schema, 'mainEntity')) {
    const mainEntity = schema['mainEntity'] as unknown[];
    if (Array.isArray(mainEntity)) {
      mainEntity.forEach((item, index) => {
        const question = item as Record<string, unknown>;
        if (!hasProperty(question, 'name') && !hasProperty(question, 'text')) {
          errors.push(`FAQ item ${index + 1}: Missing question text`);
        }
        const acceptedAnswer = question['acceptedAnswer'] as Record<string, unknown>;
        if (!acceptedAnswer || (!hasProperty(acceptedAnswer, 'text') && !hasProperty(acceptedAnswer, 'name'))) {
          errors.push(`FAQ item ${index + 1}: Missing answer text`);
        }
      });
    }
  }

  if (type === 'BreadcrumbList' && hasProperty(schema, 'itemListElement')) {
    const items = schema['itemListElement'] as unknown[];
    if (Array.isArray(items)) {
      items.forEach((item, index) => {
        const listItem = item as Record<string, unknown>;
        if (!hasProperty(listItem, 'position')) {
          warnings.push(`Breadcrumb item ${index + 1}: Missing position`);
        }
        if (!hasProperty(listItem, 'name') && !hasProperty(listItem, 'item')) {
          errors.push(`Breadcrumb item ${index + 1}: Missing name or item`);
        }
      });
    }
  }

  // Validate Offer in Product
  if (type === 'Product' && hasProperty(schema, 'offers')) {
    const offers = schema['offers'];
    const offerArray = Array.isArray(offers) ? offers : [offers];
    offerArray.forEach((offer, index) => {
      const offerObj = offer as Record<string, unknown>;
      if (!hasProperty(offerObj, 'price')) {
        errors.push(`Offer ${index + 1}: Missing price`);
      }
      if (!hasProperty(offerObj, 'priceCurrency')) {
        errors.push(`Offer ${index + 1}: Missing priceCurrency`);
      }
    });
  }

  return {
    type,
    valid: errors.length === 0,
    errors,
    warnings,
    data: schema,
  };
}

/**
 * Run schema audit on a URL
 */
export async function runSchemaAudit(url: string): Promise<SchemaAuditResult> {
  // Fetch HTML
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; SEO-Audit-Bot/1.0)',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }

  const html = await response.text();
  const schemas = extractJsonLd(html);

  const validationResults: SchemaValidationResult[] = schemas.map((schema) =>
    validateSchema(schema as Record<string, unknown>)
  );

  const summary = {
    valid: validationResults.filter((r) => r.valid).length,
    invalid: validationResults.filter((r) => !r.valid).length,
    warnings: validationResults.reduce((acc, r) => acc + r.warnings.length, 0),
  };

  return {
    url,
    timestamp: new Date().toISOString(),
    schemasFound: schemas.length,
    schemas: validationResults,
    summary,
  };
}
