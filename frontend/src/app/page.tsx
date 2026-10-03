"use client";

import { useState, useEffect, useCallback } from "react";
import { QueryForm } from "@/components/rag/QueryForm";
import { AnswerSection } from "@/components/rag/AnswerSection";
import { SourcesSection } from "@/components/rag/SourcesSection";
import { SummarySection } from "@/components/rag/SummarySection";
import { StatusLine } from "@/components/rag/StatusLine";
import { useRAGStream } from "@/hooks/useRAGStream";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Bill {
  id: string;
  name: string;
  year: string;
}

interface BillQACache {
  answer: string;
  sources: Source[];
  processingTime: number | null;
}

interface Source {
  section_header: string;
  chunk_id: string;
  content: string;
  distance: number;
}

type Tab = "ask" | "summary";

// Bill-specific example queries based on bill keywords
function getExampleQueries(billName: string): string[] {
  const name = billName.toLowerCase();

  if (name.includes("data protection") || name.includes("dpdp") || name.includes("personal data")) {
    return [
      "What are the penalties for data breaches?",
      "How is consent defined and obtained?",
      "What rights do data principals have?",
      "What are the exemptions for government agencies?",
      "Who is the Data Protection Board?",
      "What are the rules for processing children's data?",
    ];
  }
  if (name.includes("nyaya") || name.includes("penal") || name.includes("criminal")) {
    return [
      "What is the punishment for murder?",
      "How are sexual offenses defined?",
      "What are the penalties for organized crime?",
      "What rights does the accused have?",
      "How is self-defense defined?",
      "What are the penalties for cybercrime?",
    ];
  }
  if (name.includes("tax") || name.includes("income")) {
    return [
      "What are the income tax slabs?",
      "What deductions are available for individuals?",
      "How are capital gains taxed?",
      "What are the penalties for tax evasion?",
      "What is the TDS provision?",
      "How are business incomes computed?",
    ];
  }
  if (name.includes("telecom")) {
    return [
      "What are the licensing requirements?",
      "How is spectrum allocated?",
      "What are the penalties for violations?",
      "What powers does the government have?",
      "How are user rights protected?",
      "What are the rules for interception?",
    ];
  }
  if (name.includes("competition")) {
    return [
      "What is considered anti-competitive behavior?",
      "What are the penalties for cartels?",
      "How are mergers regulated?",
      "What powers does the CCI have?",
      "How are dominant positions defined?",
      "What are the settlement provisions?",
    ];
  }
  if (name.includes("waqf")) {
    return [
      "How is waqf property defined?",
      "What are the powers of the Waqf Board?",
      "How are disputes resolved?",
      "What changes does this amendment make?",
      "How is registration of waqf handled?",
      "What are the audit requirements?",
    ];
  }
  if (name.includes("farm") || name.includes("agriculture") || name.includes("produce")) {
    return [
      "What freedom do farmers get under this bill?",
      "How is trade outside APMC regulated?",
      "What are the dispute resolution mechanisms?",
      "Are there price protections for farmers?",
      "What electronic trading provisions exist?",
      "What penalties apply for violations?",
    ];
  }
  if (name.includes("banking") || name.includes("insurance") || name.includes("financial")) {
    return [
      "What regulatory changes are introduced?",
      "How are depositors protected?",
      "What powers does RBI get?",
      "What are the capital requirements?",
      "How is governance structured?",
      "What penalties exist for non-compliance?",
    ];
  }
  if (name.includes("energy") || name.includes("conservation")) {
    return [
      "What energy efficiency standards are set?",
      "How is carbon trading regulated?",
      "What are the penalties for non-compliance?",
      "What obligations do industries have?",
      "How are renewable energy targets set?",
      "What incentives are provided?",
    ];
  }
  if (name.includes("vayuyan") || name.includes("aviation")) {
    return [
      "How are airlines regulated?",
      "What safety standards are mandated?",
      "What are passengers' rights?",
      "How are airports governed?",
      "What penalties exist for violations?",
      "How is air traffic managed?",
    ];
  }
  if (name.includes("tribunal")) {
    return [
      "Which tribunals are affected?",
      "How are tribunal members appointed?",
      "What qualifications are required?",
      "What is the tenure of members?",
      "How are appeals handled?",
      "What are the key reforms introduced?",
    ];
  }
  if (name.includes("delimitation")) {
    return [
      "How are constituency boundaries redrawn?",
      "What is the basis for delimitation?",
      "How are reserved seats allocated?",
      "What role does the commission play?",
      "How are objections handled?",
      "When does the new delimitation take effect?",
    ];
  }
  if (name.includes("mines") || name.includes("mineral") || name.includes("mmdr")) {
    return [
      "How are mining licenses granted?",
      "What environmental protections exist?",
      "How are mineral rights auctioned?",
      "What royalties apply?",
      "What changes does this amendment make?",
      "What penalties exist for illegal mining?",
    ];
  }
  // Generic fallback
  return [
    "What is the main purpose of this bill?",
    "What are the key provisions?",
    "What penalties are defined?",
    "What rights does this bill create?",
    "What exceptions or exemptions exist?",
    "How is this bill enforced?",
  ];
}

export default function Home() {
  const [billsByYear, setBillsByYear] = useState<Record<string, Bill[]>>({});
  const [expandedYears, setExpandedYears] = useState<Set<string>>(new Set());
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("ask");
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Cache Q&A results per bill
  const [qaCache, setQaCache] = useState<Record<string, BillQACache>>({});

  const {
    answer,
    sources,
    processingTime,
    statusMessage,
    currentStage,
    isActive,
    isLoading,
    streamQuery,
    reset,
  } = useRAGStream();

  // Fetch bills on mount
  useEffect(() => {
    fetch(`${API_URL}/api/bills`)
      .then((res) => res.json())
      .then((data) => {
        const byYear = data.by_year || {};
        setBillsByYear(byYear);
        setExpandedYears(new Set(Object.keys(byYear)));
        const allBills = data.bills || [];
        if (allBills.length > 0) {
          setSelectedBill(allBills[0]);
        }
      })
      .catch(() => {
        const fallback: Record<string, Bill[]> = {
          "2023": [
            { id: "Bharatiya_Nyaya_Sanhita_2023", name: "Bharatiya Nyaya Sanhita 2023", year: "2023" },
            { id: "Digital_Personal_Data_Protection_Bill_2023", name: "Digital Personal Data Protection Bill 2023", year: "2023" },
          ],
          "2019": [
            { id: "Personal_Data_Protection_Bill_2019", name: "Personal Data Protection Bill 2019", year: "2019" },
          ],
        };
        setBillsByYear(fallback);
        setExpandedYears(new Set(["2023", "2019"]));
        setSelectedBill(fallback["2023"][0]);
      });
  }, []);

  // Save current Q&A to cache when answer changes
  useEffect(() => {
    if (selectedBill && answer && !isActive) {
      setQaCache((prev) => ({
        ...prev,
        [selectedBill.id]: { answer, sources, processingTime },
      }));
    }
  }, [answer, sources, processingTime, isActive, selectedBill]);

  // Fetch summary when bill or tab changes
  useEffect(() => {
    if (activeTab !== "summary" || !selectedBill) return;
    setSummaryLoading(true);
    setSummary("");
    fetch(`${API_URL}/api/bills/${selectedBill.id}/summary`)
      .then((res) => res.json())
      .then((data) => setSummary(data.summary || ""))
      .catch(() => setSummary("Summary not available yet. Run the summarization pipeline first."))
      .finally(() => setSummaryLoading(false));
  }, [activeTab, selectedBill]);

  const handleQuerySubmit = (query: string, topK: number) => {
    if (!selectedBill) return;
    reset();
    streamQuery(query, selectedBill.id, topK);
  };

  const handleBillSelect = useCallback((bill: Bill) => {
    setSelectedBill(bill);
    reset();
    setSummary("");
  }, [reset]);

  const toggleYear = (year: string) => {
    setExpandedYears((prev) => {
      const next = new Set(prev);
      if (next.has(year)) next.delete(year);
      else next.add(year);
      return next;
    });
  };

  // Get current display data — show cached Q&A if available and no active query
  const cachedQA = selectedBill ? qaCache[selectedBill.id] : null;
  const displayAnswer = answer || cachedQA?.answer || "";
  const displaySources = sources.length > 0 ? sources : cachedQA?.sources || [];
  const displayProcessingTime = processingTime || cachedQA?.processingTime || null;

  const years = Object.keys(billsByYear);

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      {/* Sidebar — independent scroll */}
      <aside
        className={`${
          sidebarOpen ? "w-72" : "w-0"
        } flex-shrink-0 border-r border-gray-200 bg-gray-50 transition-all duration-300 flex flex-col h-screen overflow-hidden`}
      >
        {/* Sidebar header — fixed */}
        <div className="px-5 py-5 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-lg font-semibold text-gray-900 tracking-tight">
            BillSense
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">Indian Legislative Bills</p>
        </div>

        {/* Year list — scrollable */}
        <nav className="flex-1 overflow-y-auto py-3">
          {years.map((year) => (
            <div key={year}>
              <button
                onClick={() => toggleYear(year)}
                className="w-full flex items-center justify-between px-5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {year}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 bg-gray-200 px-1.5 py-0.5 rounded-full">
                    {billsByYear[year].length}
                  </span>
                  <svg
                    className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-200 ${
                      expandedYears.has(year) ? "rotate-90" : ""
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>

              {expandedYears.has(year) && (
                <div className="pb-1">
                  {billsByYear[year].map((bill) => (
                    <button
                      key={bill.id}
                      onClick={() => handleBillSelect(bill)}
                      className={`w-full text-left px-5 pl-10 py-2 text-sm transition-all duration-150 cursor-pointer ${
                        selectedBill?.id === bill.id
                          ? "bg-sky-50 text-sky-700 font-medium border-r-2 border-sky-500"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="truncate">{bill.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {years.length === 0 && (
            <div className="px-5 py-8 text-center text-gray-400 text-sm">
              No bills processed yet.
              <br />
              Run <code className="text-xs bg-gray-200 px-1 py-0.5 rounded">make pipeline</code>
            </div>
          )}
        </nav>

        {/* Sidebar footer — fixed */}
        <div className="px-5 py-3 border-t border-gray-200 text-xs text-gray-400 flex-shrink-0">
          <a
            href="https://github.com/JaiprakashSahu/BillSense"
            className="hover:text-sky-600 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
          <span className="mx-1.5">·</span>
          Powered by Groq + ChromaDB
        </div>
      </aside>

      {/* Main content — independent scroll */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top bar — fixed */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-gray-200 bg-white/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
            >
              <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            {selectedBill && (
              <h2 className="text-sm font-medium text-gray-700 truncate max-w-md">
                {selectedBill.name}
              </h2>
            )}
          </div>

          <div className="bg-gray-100 rounded-xl p-1 flex gap-1">
            <button
              onClick={() => setActiveTab("ask")}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === "ask"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Ask a Question
            </button>
            <button
              onClick={() => setActiveTab("summary")}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === "summary"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Bill Summary
            </button>
          </div>
        </header>

        {/* Content area — scrollable */}
        <div className="flex-1 overflow-y-auto bg-grid-square">
          <div className="max-w-3xl mx-auto px-6 py-8">
            {!selectedBill ? (
              <div className="text-center py-20 text-gray-400">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-lg font-medium text-gray-500">Select a bill from the sidebar</p>
                <p className="text-sm mt-1">Choose a year and then pick a bill to get started</p>
              </div>
            ) : activeTab === "ask" ? (
              <>
                <div className="mb-8">
                  <QueryForm
                    bills={[]}
                    selectedBill={selectedBill.id}
                    onBillChange={() => {}}
                    onSubmit={handleQuerySubmit}
                    isLoading={isLoading}
                    hasAnswer={!!displayAnswer}
                    exampleQueries={getExampleQueries(selectedBill.name)}
                  />
                </div>

                {(isActive || statusMessage) && (
                  <div className="mb-6">
                    <StatusLine
                      message={statusMessage}
                      isActive={isActive}
                      currentStage={currentStage}
                    />
                  </div>
                )}

                <div className="mb-6">
                  <AnswerSection
                    answer={displayAnswer}
                    processingTime={displayProcessingTime || undefined}
                    isVisible={!!displayAnswer}
                  />
                </div>

                <div className="mb-6">
                  <SourcesSection
                    sources={displaySources}
                    isVisible={!!displayAnswer && displaySources.length > 0}
                  />
                </div>
              </>
            ) : (
              <>
                {summaryLoading ? (
                  <div className="flex items-center justify-center py-16">
                    <svg className="w-6 h-6 text-sky-500 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span className="ml-3 text-gray-500 text-sm">Loading summary...</span>
                  </div>
                ) : (
                  <SummarySection
                    summary={summary}
                    billName={selectedBill.name}
                    isVisible={!!summary}
                  />
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
