export type BenchmarkConfirmation = {
  measurementMode: string;
  model: string;
  promptCount: number;
  expectedAiRuns: number;
  webSearchEnabled: boolean;
};


export function benchmarkConfirmation(
  mode: "memory" | "web_search" | "site_rag",
  model: string,
  promptCount: number,
): BenchmarkConfirmation {
  return {
    measurementMode:
      mode === "site_rag"
        ? "Site RAG"
        : mode === "web_search"
          ? "Web Search"
          : "Memory",
    model,
    promptCount,
    expectedAiRuns: promptCount,
    webSearchEnabled: mode === "web_search",
  };
}
