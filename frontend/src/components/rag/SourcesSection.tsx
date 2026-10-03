"use client";

interface Source {
  section_header: string;
  chunk_id: string;
  content: string;
  distance: number;
}

interface SourcesSectionProps {
  sources: Source[];
  isVisible: boolean;
}

export function SourcesSection({ sources, isVisible }: SourcesSectionProps) {
  if (!isVisible || sources.length === 0) return null;

  return (
    <div className="fade-in">
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-violet-500" />
            <h3 className="text-sm font-semibold text-gray-700">Sources</h3>
          </div>
          <span className="text-xs text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
            {sources.length} sections
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="px-5 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-10">
                  #
                </th>
                <th className="px-5 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Section
                </th>
                <th className="px-5 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Preview
                </th>
                <th className="px-5 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                  Relevance
                </th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-50 hover:bg-sky-50/50 transition-colors"
                >
                  <td className="px-5 py-3 text-gray-400 font-mono text-xs">
                    {idx + 1}
                  </td>
                  <td className="px-5 py-3">
                    <span className="font-medium text-gray-800 text-sm">
                      {source.section_header || `Chunk ${source.chunk_id}`}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-gray-600 text-xs max-w-md">
                    <p className="line-clamp-2">
                      {source.content.slice(0, 200)}...
                    </p>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        source.distance < 0.5
                          ? "bg-green-100 text-green-700"
                          : source.distance < 0.8
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {(1 - source.distance).toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
