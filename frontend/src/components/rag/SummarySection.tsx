"use client";
import { useMemo } from "react";
import { marked } from "marked";

interface SummarySectionProps {
  summary: string;
  billName: string;
  isVisible: boolean;
}

export function SummarySection({ summary, billName, isVisible }: SummarySectionProps) {
  if (!isVisible) return null;

  const htmlContent = useMemo(() => {
    if (!summary) return "";
    return marked.parse(summary, { async: false }) as string;
  }, [summary]);

  return (
    <div className="fade-in">
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <h3 className="text-sm font-semibold text-gray-700">
              Summary — {billName}
            </h3>
          </div>
        </div>

        {/* Content */}
        <div className="px-5 py-4">
          <div
            className="prose text-gray-800 text-[15px] leading-relaxed max-w-none"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        </div>
      </div>
    </div>
  );
}
