/**
 * BM25 Search Engine for SEO Framework
 * TypeScript implementation optimized for Japanese text
 */

import { SearchableDocument, DatasetType, getAllDocuments } from './datasets.js';

// BM25 parameters (standard values)
const K1 = 1.2; // Term frequency saturation
const B = 0.75; // Length normalization

// Japanese tokenizer (simple but effective)
function tokenize(text: string): string[] {
  // Normalize text
  const normalized = text
    .toLowerCase()
    .replace(/[Ａ-Ｚａ-ｚ０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
    .replace(/[、。！？「」『』（）・]/g, ' ');

  // Split by whitespace and Japanese character boundaries
  const tokens: string[] = [];

  // Split by whitespace first
  const parts = normalized.split(/[\s\-_,]+/).filter(Boolean);

  for (const part of parts) {
    // For ASCII words, add as-is
    if (/^[a-z0-9]+$/.test(part)) {
      tokens.push(part);
      continue;
    }

    // For Japanese, use character n-grams (bi-grams for kanji, uni-grams for hiragana)
    let current = '';
    for (let i = 0; i < part.length; i++) {
      const char = part[i];

      if (/[a-z0-9]/.test(char)) {
        current += char;
      } else {
        if (current) {
          tokens.push(current);
          current = '';
        }

        // Hiragana/Katakana: unigram
        if (/[\u3040-\u309F\u30A0-\u30FF]/.test(char)) {
          tokens.push(char);
        }
        // Kanji: bigram with overlap
        else if (/[\u4E00-\u9FAF]/.test(char)) {
          tokens.push(char);
          if (i + 1 < part.length && /[\u4E00-\u9FAF]/.test(part[i + 1])) {
            tokens.push(char + part[i + 1]);
          }
        }
      }
    }
    if (current) {
      tokens.push(current);
    }
  }

  return tokens.filter(t => t.length > 0);
}

// BM25 Index
interface TermInfo {
  df: number; // Document frequency
  postings: Map<string, number>; // docId -> term frequency
}

export class BM25Index {
  private documents: Map<string, SearchableDocument> = new Map();
  private termIndex: Map<string, TermInfo> = new Map();
  private docLengths: Map<string, number> = new Map();
  private avgDocLength: number = 0;
  private docCount: number = 0;

  constructor(documents?: SearchableDocument[]) {
    if (documents) {
      this.index(documents);
    }
  }

  index(documents: SearchableDocument[]): void {
    this.documents.clear();
    this.termIndex.clear();
    this.docLengths.clear();

    let totalLength = 0;

    for (const doc of documents) {
      this.documents.set(doc.id, doc);
      const tokens = tokenize(doc.text);
      this.docLengths.set(doc.id, tokens.length);
      totalLength += tokens.length;

      // Count term frequencies
      const termFreqs = new Map<string, number>();
      for (const token of tokens) {
        termFreqs.set(token, (termFreqs.get(token) || 0) + 1);
      }

      // Update index
      for (const [term, freq] of termFreqs) {
        let termInfo = this.termIndex.get(term);
        if (!termInfo) {
          termInfo = { df: 0, postings: new Map() };
          this.termIndex.set(term, termInfo);
        }
        termInfo.df++;
        termInfo.postings.set(doc.id, freq);
      }
    }

    this.docCount = documents.length;
    this.avgDocLength = this.docCount > 0 ? totalLength / this.docCount : 0;
  }

  search(query: string, options?: {
    dataset?: DatasetType;
    limit?: number;
  }): SearchResult[] {
    const queryTokens = tokenize(query);
    if (queryTokens.length === 0) return [];

    const scores = new Map<string, number>();

    for (const token of queryTokens) {
      const termInfo = this.termIndex.get(token);
      if (!termInfo) continue;

      // IDF calculation
      const idf = Math.log((this.docCount - termInfo.df + 0.5) / (termInfo.df + 0.5) + 1);

      for (const [docId, tf] of termInfo.postings) {
        // Filter by dataset if specified
        if (options?.dataset) {
          const doc = this.documents.get(docId);
          if (doc && doc.dataset !== options.dataset) continue;
        }

        const docLength = this.docLengths.get(docId) || 0;
        const lengthNorm = 1 - B + B * (docLength / this.avgDocLength);

        // BM25 score
        const score = idf * ((tf * (K1 + 1)) / (tf + K1 * lengthNorm));

        scores.set(docId, (scores.get(docId) || 0) + score);
      }
    }

    // Sort by score and create results
    const results: SearchResult[] = [];
    const sortedDocs = [...scores.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, options?.limit || 10);

    for (const [docId, score] of sortedDocs) {
      const doc = this.documents.get(docId);
      if (doc) {
        results.push({
          document: doc,
          score,
          matchedTerms: queryTokens.filter(t => {
            const info = this.termIndex.get(t);
            return info?.postings.has(docId);
          }),
        });
      }
    }

    return results;
  }

  // Get document by ID
  getDocument(id: string): SearchableDocument | undefined {
    return this.documents.get(id);
  }

  // Get all documents of a type
  getByDataset(dataset: DatasetType): SearchableDocument[] {
    return [...this.documents.values()].filter(d => d.dataset === dataset);
  }
}

export interface SearchResult {
  document: SearchableDocument;
  score: number;
  matchedTerms: string[];
}

// Singleton index for the SEO framework data
let globalIndex: BM25Index | null = null;

export function getSearchIndex(): BM25Index {
  if (!globalIndex) {
    globalIndex = new BM25Index(getAllDocuments());
  }
  return globalIndex;
}

// Convenience search function
export function searchSEOFramework(
  query: string,
  options?: { dataset?: DatasetType; limit?: number }
): SearchResult[] {
  return getSearchIndex().search(query, options);
}

// Page type detection from URL/content
export function detectPageType(url: string, title?: string): SearchResult[] {
  const searchText = [url, title].filter(Boolean).join(' ');
  return searchSEOFramework(searchText, { dataset: 'page-type', limit: 3 });
}

// Search intent detection from query
export function detectSearchIntent(query: string): SearchResult[] {
  return searchSEOFramework(query, { dataset: 'intent', limit: 3 });
}

// Find relevant LLM tactics
export function findLLMTactics(context: string): SearchResult[] {
  return searchSEOFramework(context, { dataset: 'llm', limit: 5 });
}
