"use client";

interface StatusLineProps {
  message: string;
  isActive: boolean;
  currentStage: string;
}

const STAGE_ICONS: Record<string, string> = {
  connecting: "🔗",
  searching: "🔍",
  generating: "🤖",
  writing: "✍️",
  complete: "✅",
  error: "❌",
};

export function StatusLine({ message, isActive, currentStage }: StatusLineProps) {
  if (!message) return null;

  const icon = STAGE_ICONS[currentStage] || "⏳";

  return (
    <div className="fade-in">
      <div className="flex items-center gap-3 px-4 py-3 bg-white rounded-xl border border-gray-200">
        {isActive && (
          <svg className="w-4 h-4 text-sky-500 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        <span className="text-base flex-shrink-0">{icon}</span>
        <span className="text-sm text-gray-600">{message}</span>
      </div>
    </div>
  );
}
