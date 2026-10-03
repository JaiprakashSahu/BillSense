"use client";
import { useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Source {
  section_header: string;
  chunk_id: string;
  content: string;
  distance: number;
}

interface RAGStreamState {
  answer: string;
  sources: Source[];
  processingTime: number | null;
  statusMessage: string;
  currentStage: string;
  isActive: boolean;
  isLoading: boolean;
}

export function useRAGStream() {
  const [state, setState] = useState<RAGStreamState>({
    answer: "",
    sources: [],
    processingTime: null,
    statusMessage: "",
    currentStage: "",
    isActive: false,
    isLoading: false,
  });

  const reset = useCallback(() => {
    setState({
      answer: "",
      sources: [],
      processingTime: null,
      statusMessage: "",
      currentStage: "",
      isActive: false,
      isLoading: false,
    });
  }, []);

  const streamQuery = useCallback(
    async (query: string, billId: string, topK: number = 5) => {
      setState((prev) => ({
        ...prev,
        isActive: true,
        isLoading: true,
        statusMessage: "Connecting...",
        currentStage: "connecting",
        answer: "",
        sources: [],
        processingTime: null,
      }));

      try {
        const response = await fetch(`${API_URL}/api/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            bill_id: billId,
            top_k: topK,
          }),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const data = JSON.parse(jsonStr);

              if (data.type === "progress") {
                setState((prev) => ({
                  ...prev,
                  statusMessage: data.message,
                  currentStage: data.stage,
                }));
              } else if (data.type === "chunk") {
                setState((prev) => ({
                  ...prev,
                  answer: prev.answer + data.content,
                  isLoading: false,
                  currentStage: "writing",
                  statusMessage: "Generating answer...",
                }));
              } else if (data.type === "complete") {
                setState((prev) => ({
                  ...prev,
                  sources: data.sources || [],
                  processingTime: data.processing_time,
                  isActive: false,
                  isLoading: false,
                  statusMessage: "Complete",
                  currentStage: "complete",
                }));
              } else if (data.type === "error") {
                setState((prev) => ({
                  ...prev,
                  isActive: false,
                  isLoading: false,
                  statusMessage: `Error: ${data.message}`,
                  currentStage: "error",
                }));
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isActive: false,
          isLoading: false,
          statusMessage: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
          currentStage: "error",
        }));
      }
    },
    []
  );

  return { ...state, streamQuery, reset };
}
