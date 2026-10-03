"use client";
import { useMemo } from "react";
import { marked } from "marked";

interface AnswerSectionProps {
  answer: string;
  processingTime?: number;
  isVisible: boolean;
}

export function AnswerSection({ answer, processingTime, isVisible }: AnswerSectionProps) {
  if (!isVisible) return null;

  const htmlContent = useMemo(() => {
    if (!answer) return "";
    return marked.parse(answer, { async: false }) as string;
  }, [answer]);

  return (
    <div className="fade-in">
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-pulse-dot" />
            <h3 className="text-sm font-semibold text-gray-700">Answer</h3>
          </div>
          {processingTime && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
              {processingTime}s
            </span>
          )}
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
