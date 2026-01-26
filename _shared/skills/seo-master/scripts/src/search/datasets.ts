/**
 * SEO Framework Datasets - CSV Data Loader
 * Loads page-types, search-intents, and llm-tactics from CSV files
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DATA_DIR = join(__dirname, '../../../data');

// Type definitions
export interface PageType {
  page_type: string;
  keywords: string[];
  patterns: string[];
  optimal_schema: string[];
  required_elements: string[];
  llm_focus: 'high' | 'medium' | 'low';
  cta_style: 'strong' | 'medium' | 'soft' | 'navigation';
  description: string;
}

export interface SearchIntent {
  intent: string;
  keywords: string[];
  triggers: string[];
  content_type: string;
  cta_type: string;
  ai_priority: 'high' | 'medium' | 'low';
  google_intent: string;
  description: string;
}

export interface LLMTactic {
  tactic: string;
  priority: 'p0' | 'p1' | 'p2' | 'p3';
  implementation: string;
  check_method: string;
  ai_platforms: string[];
  description: string;
}

// CSV parsing with proper quote handling
function parseCSV(content: string): Record<string, string>[] {
  const lines = content.trim().split('\n');
  if (lines.length < 2) return [];

  const headers = parseCSVLine(lines[0]);
  const results: Record<string, string>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const values = parseCSVLine(line);
    if (values.length !== headers.length) continue;

    const record: Record<string, string> = {};
    headers.forEach((header, idx) => {
      record[header] = values[idx] || '';
    });
    results.push(record);
  }

  return results;
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());

  return result;
}

// Data loaders
let pageTypesCache: PageType[] | null = null;
let searchIntentsCache: SearchIntent[] | null = null;
let llmTacticsCache: LLMTactic[] | null = null;

export function loadPageTypes(): PageType[] {
  if (pageTypesCache) return pageTypesCache;

  const content = readFileSync(join(DATA_DIR, 'page-types.csv'), 'utf-8');
  const records = parseCSV(content);

  pageTypesCache = records
    .filter(r => r.page_type)
    .map(r => ({
      page_type: r.page_type,
      keywords: r.keywords?.split(',').map(s => s.trim()) || [],
      patterns: r.patterns?.split(',').map(s => s.trim()) || [],
      optimal_schema: r.optimal_schema?.split('+').map(s => s.trim()) || [],
      required_elements: r.required_elements?.split(',').map(s => s.trim()) || [],
      llm_focus: (r.llm_focus as PageType['llm_focus']) || 'medium',
      cta_style: (r.cta_style as PageType['cta_style']) || 'medium',
      description: r.description || '',
    }));

  return pageTypesCache;
}

export function loadSearchIntents(): SearchIntent[] {
  if (searchIntentsCache) return searchIntentsCache;

  const content = readFileSync(join(DATA_DIR, 'search-intents.csv'), 'utf-8');
  const records = parseCSV(content);

  searchIntentsCache = records
    .filter(r => r.intent)
    .map(r => ({
      intent: r.intent,
      keywords: r.keywords?.split(',').map(s => s.trim()) || [],
      triggers: r.triggers?.split(',').map(s => s.trim()) || [],
      content_type: r.content_type || '',
      cta_type: r.cta_type || '',
      ai_priority: (r.ai_priority as SearchIntent['ai_priority']) || 'medium',
      google_intent: r.google_intent || '',
      description: r.description || '',
    }));

  return searchIntentsCache;
}

export function loadLLMTactics(): LLMTactic[] {
  if (llmTacticsCache) return llmTacticsCache;

  const content = readFileSync(join(DATA_DIR, 'llm-tactics.csv'), 'utf-8');
  const records = parseCSV(content);

  llmTacticsCache = records
    .filter(r => r.tactic)
    .map(r => ({
      tactic: r.tactic,
      priority: (r.priority as LLMTactic['priority']) || 'p2',
      implementation: r.implementation || '',
      check_method: r.check_method || '',
      ai_platforms: r.ai_platforms?.split(',').map(s => s.trim()) || [],
      description: r.description || '',
    }));

  return llmTacticsCache;
}

// Get all searchable text for BM25 indexing
export type DatasetType = 'page-type' | 'intent' | 'llm';

export interface SearchableDocument {
  id: string;
  dataset: DatasetType;
  text: string;
  data: PageType | SearchIntent | LLMTactic;
}

export function getAllDocuments(): SearchableDocument[] {
  const documents: SearchableDocument[] = [];

  // Page types
  loadPageTypes().forEach(pt => {
    documents.push({
      id: `page-type:${pt.page_type}`,
      dataset: 'page-type',
      text: [
        pt.page_type,
        ...pt.keywords,
        ...pt.patterns,
        pt.description,
      ].join(' '),
      data: pt,
    });
  });

  // Search intents
  loadSearchIntents().forEach(si => {
    documents.push({
      id: `intent:${si.intent}`,
      dataset: 'intent',
      text: [
        si.intent,
        ...si.keywords,
        ...si.triggers,
        si.content_type,
        si.google_intent,
        si.description,
      ].join(' '),
      data: si,
    });
  });

  // LLM tactics
  loadLLMTactics().forEach(lt => {
    documents.push({
      id: `llm:${lt.tactic}`,
      dataset: 'llm',
      text: [
        lt.tactic,
        lt.implementation,
        lt.check_method,
        ...lt.ai_platforms,
        lt.description,
      ].join(' '),
      data: lt,
    });
  });

  return documents;
}
