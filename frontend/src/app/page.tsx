"use client";

import { useState, useEffect } from "react";
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
}

type Tab = "ask" | "summary";

export default function Home() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [selectedBill, setSelectedBill] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("ask");
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);

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
        setBills(data.bills || []);
        if (data.bills?.length > 0) {
          setSelectedBill(data.bills[0].id);
        }
      })
      .catch(() => {
        // Fallback bills if API is not running
        const fallback = [
          { id: "Bharatiya_Nyaya_Sanhita_2023", name: "Bharatiya Nyaya Sanhita 2023" },
          { id: "Digital_Personal_Data_Protection_Bill_2023", name: "Digital Personal Data Protection Bill 2023" },
          { id: "Personal_Data_Protection_Bill_2019", name: "Personal Data Protection Bill 2019" },
        ];
        setBills(fallback);
        setSelectedBill(fallback[0].id);
      });
  }, []);

  // Fetch summary when bill or tab changes
  useEffect(() => {
    if (activeTab !== "summary" || !selectedBill) return;
    setSummaryLoading(true);
    setSummary("");
    fetch(`${API_URL}/api/bills/${selectedBill}/summary`)
      .then((res) => res.json())
      .then((data) => setSummary(data.summary || ""))
      .catch(() => setSummary("Summary not available yet. Run the summarization pipeline first."))
      .finally(() => setSummaryLoading(false));
  }, [activeTab, selectedBill]);

  const handleQuerySubmit = (query: string, topK: number) => {
    reset();
    streamQuery(query, selectedBill, topK);
  };

  const handleBillChange = (billId: string) => {
    setSelectedBill(billId);
    reset();
    setSummary("");
  };

  return (
    <main className="bg-grid-square bg-white text-gray-900 min-h-screen flex flex-col">
      <div className="container mx-auto px-4 py-8 md:py-16 max-w-4xl flex-grow flex flex-col">
        <div className="flex-grow">
          {/* Title */}
          <div className="text-center mb-10 md:mb-14">
            <h1 className="text-3xl md:text-5xl font-semibold text-gray-900 tracking-tight">
              BillSense
            </h1>
            <p className="text-gray-500 mt-2 text-sm md:text-base">
              AI-powered search and summary for Indian government bills
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex items-center justify-center mb-8">
            <div className="bg-gray-100 rounded-xl p-1 flex gap-1">
              <button
                onClick={() => setActiveTab("ask")}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                  activeTab === "ask"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Ask a Question
              </button>
              <button
                onClick={() => setActiveTab("summary")}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                  activeTab === "summary"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Bill Summary
              </button>
            </div>
          </div>

          {/* Ask tab */}
          {activeTab === "ask" && (
            <>
              <div className="mb-8">
                <QueryForm
                  bills={bills}
                  selectedBill={selectedBill}
                  onBillChange={handleBillChange}
                  onSubmit={handleQuerySubmit}
                  isLoading={isLoading}
                  hasAnswer={!!answer}
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
                  answer={answer}
                  processingTime={processingTime || undefined}
                  isVisible={!!answer}
                />
              </div>

              <div className="mb-6">
                <SourcesSection
                  sources={sources}
                  isVisible={!!answer && sources.length > 0}
                />
              </div>
            </>
          )}

          {/* Summary tab */}
          {activeTab === "summary" && (
            <>
              {/* Bill selector */}
              <div className="flex items-center justify-center gap-2 mb-6 flex-wrap">
                {bills.map((bill) => (
                  <button
                    key={bill.id}
                    onClick={() => handleBillChange(bill.id)}
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
                  billName={bills.find((b) => b.id === selectedBill)?.name || ""}
                  isVisible={!!summary}
                />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-gray-200 text-center text-gray-400 text-xs md:text-sm">
          <p className="mb-2">
            Built by{" "}
            <a
              href="https://github.com/JaiprakashSahu"
              className="text-sky-600 hover:text-sky-700 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Jaiprakash Sahu
            </a>
          </p>
          <p>
            Powered by Groq + ChromaDB + Next.js
          </p>
        </div>
      </div>
    </main>
  );
}
