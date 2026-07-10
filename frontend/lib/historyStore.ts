/**
 * Client-side history store using localStorage.
 * Persists analysis results across page navigations and refreshes.
 */

export interface HistoryEntry {
  analysis_id:     string;
  pr_url:          string;
  pr_title:        string;
  repo:            string;
  verdict:         "READY_TO_MERGE" | "CAUTION" | "BLOCKED";
  confidence:      number;
  latency_seconds: number;
  analysed_at:     string;
  agent_count:     number;
  blocking_issues: number;
}

const KEY = "prism_analysis_history";
const MAX = 50;

export function saveToHistory(entry: HistoryEntry): void {
  if (typeof window === "undefined") return;
  try {
    const existing = loadHistory();
    // Deduplicate by analysis_id
    const filtered = existing.filter(e => e.analysis_id !== entry.analysis_id);
    const updated  = [entry, ...filtered].slice(0, MAX);
    localStorage.setItem(KEY, JSON.stringify(updated));
    // Dispatch event so history page can react without a refresh
    window.dispatchEvent(new Event("prism_history_updated"));
  } catch (_) { /* storage full or private browsing */ }
}

export function loadHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) { return []; }
}

export function clearHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
  window.dispatchEvent(new Event("prism_history_updated"));
}
