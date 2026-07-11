/**
 * Analysis history store.
 * Uses Supabase when authenticated, with localStorage as offline fallback.
 */

import { createClient } from "@/utils/supabase/client";

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

function saveToLocalStorage(entry: HistoryEntry): void {
  if (typeof window === "undefined") return;
  try {
    const existing = loadFromLocalStorage();
    const filtered = existing.filter((e) => e.analysis_id !== entry.analysis_id);
    const updated = [entry, ...filtered].slice(0, MAX);
    localStorage.setItem(KEY, JSON.stringify(updated));
    window.dispatchEvent(new Event("prism_history_updated"));
  } catch {
    /* storage full or private browsing */
  }
}

function loadFromLocalStorage(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function clearLocalStorage(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
  window.dispatchEvent(new Event("prism_history_updated"));
}

export async function saveToHistory(entry: HistoryEntry): Promise<void> {
  saveToLocalStorage(entry);

  if (typeof window === "undefined") return;

  try {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) return;

    await supabase.from("analysis_history").upsert(
      {
        user_id: user.id,
        analysis_id: entry.analysis_id,
        pr_url: entry.pr_url,
        pr_title: entry.pr_title,
        repo: entry.repo,
        verdict: entry.verdict,
        confidence: entry.confidence,
        latency_seconds: entry.latency_seconds,
        analysed_at: entry.analysed_at,
        agent_count: entry.agent_count,
        blocking_issues: entry.blocking_issues,
      },
      { onConflict: "user_id,analysis_id" }
    );
  } catch {
    /* Supabase unavailable — localStorage already saved */
  }
}

export async function loadHistory(): Promise<HistoryEntry[]> {
  if (typeof window === "undefined") return [];

  try {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (user) {
      const { data, error } = await supabase
        .from("analysis_history")
        .select(
          "analysis_id, pr_url, pr_title, repo, verdict, confidence, latency_seconds, analysed_at, agent_count, blocking_issues"
        )
        .eq("user_id", user.id)
        .order("analysed_at", { ascending: false })
        .limit(MAX);

      if (!error && data) {
        return data as HistoryEntry[];
      }
    }
  } catch {
    /* fall through to localStorage */
  }

  return loadFromLocalStorage();
}

export async function clearHistory(): Promise<void> {
  clearLocalStorage();

  if (typeof window === "undefined") return;

  try {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) return;

    await supabase.from("analysis_history").delete().eq("user_id", user.id);
  } catch {
    /* localStorage already cleared */
  }
}
