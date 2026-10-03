"use client";
import { useState, FormEvent } from "react";

interface Bill {
  id: string;
  name: string;
}

interface QueryFormProps {
  bills: Bill[];
  selectedBill: string;
  onBillChange: (billId: string) => void;
  onSubmit: (query: string, topK: number) => void;
  isLoading: boolean;
  hasAnswer: boolean;
}

const EXAMPLE_QUERIES = [
  "What are the penalties for data breaches?",
  "What rights do citizens have under this bill?",
  "Who is the Data Protection Authority?",
  "What are the exceptions for government agencies?",
  "How is consent defined and obtained?",
  "What is the punishment for murder?",
];

export function QueryForm({
  bills,
  selectedBill,
  onBillChange,
  onSubmit,
  isLoading,
  hasAnswer,
}: QueryFormProps) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [showTopK, setShowTopK] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSubmit(query.trim(), topK);
  };

  const handleExample = (q: string) => {
    setQuery(q);
    onSubmit(q, topK);
  };

  return (
    <div>
      {/* Bill selector */}
      <div className="flex items-center justify-center gap-2 mb-6 flex-wrap">
        {bills.map((bill) => (
          <button
            key={bill.id}
            onClick={() => onBillChange(bill.id)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer ${
              selectedBill === bill.id
                ? "bg-gray-900 text-white shadow-md"
                : "bg-white text-gray-600 border border-gray-200 hover:border-gray-400 hover:text-gray-900"
            }`}
          >
            {bill.name}
          </button>
        ))}
      </div>

      {/* Search form */}
      <form onSubmit={handleSubmit}>
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md focus-within:shadow-md focus-within:border-gray-300 transition-all duration-200">
          <div className="flex items-center px-4 py-3">
            {/* Left controls */}
            <div className="flex items-center gap-1 mr-3">
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowTopK(!showTopK)}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <span className="bg-sky-100 text-sky-700 px-1.5 py-0.5 rounded-full text-[10px] font-bold">
                    {topK}
                  </span>
                </button>
                {showTopK && (
                  <div className="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                    {[3, 5, 8, 10].map((k) => (
                      <button
                        key={k}
                        type="button"
                        onClick={() => { setTopK(k); setShowTopK(false); }}
                        className={`block w-full px-4 py-1.5 text-left text-sm cursor-pointer ${
                          topK === k ? "bg-sky-50 text-sky-700 font-medium" : "text-gray-600 hover:bg-gray-50"
                        }`}
                      >
                        {k} sources
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Input */}
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about this bill..."
              className="flex-1 text-base text-gray-900 placeholder-gray-400 bg-transparent outline-none"
              disabled={isLoading}
            />

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="ml-3 bg-sky-500 hover:bg-sky-600 disabled:bg-gray-300 text-white rounded-xl px-4 py-2 font-medium text-sm transition-colors duration-200 flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              )}
              {isLoading ? "Searching" : "Search"}
            </button>
          </div>
        </div>
      </form>

      {/* Example queries */}
      {!hasAnswer && (
        <div className="mt-4 flex flex-wrap gap-2 justify-center fade-in">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => handleExample(q)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-500 bg-white border border-gray-200 rounded-full hover:border-gray-400 hover:text-gray-700 transition-all duration-200 cursor-pointer"
            >
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {q}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
