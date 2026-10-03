# BillSense — Makefile
# Run `make help` to see all available commands

.PHONY: help setup pipeline extract chunk embed summarize serve frontend dev clean

help: ## Show this help
	@echo ""
	@echo "  BillSense Commands"
	@echo "  ──────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## First-time setup: install all dependencies
	pip3 install -r requirements.txt
	cd frontend && npm install

pipeline: ## Run full pipeline: extract → chunk → embed → summarize
	python3 run_pipeline.py

extract: ## Stage 1: Extract text from PDFs
	python3 run_pipeline.py --stage 1

chunk: ## Stage 2: Chunk extracted texts into sections
	python3 run_pipeline.py --stage 2

embed: ## Stage 3: Embed chunks into Chroma vector DB
	python3 run_pipeline.py --stage 3

summarize: ## Stage 4: Generate summaries via Groq LLM
	python3 run_pipeline.py --stage 4

serve: ## Start backend API server (port 8000)
	python3 backend/api.py

frontend: ## Start frontend dev server (port 3000)
	cd frontend && npm run dev

dev: ## Start both backend and frontend together
	@echo "Starting BillSense..."
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:3000"
	@echo ""
	@python3 backend/api.py & echo $$! > .backend.pid
	@cd frontend && npm run dev & echo $$! > .frontend.pid
	@wait

stop: ## Stop running backend and frontend
	@if [ -f .backend.pid ]; then kill $$(cat .backend.pid) 2>/dev/null; rm .backend.pid; echo "Backend stopped"; fi
	@if [ -f .frontend.pid ]; then kill $$(cat .frontend.pid) 2>/dev/null; rm .frontend.pid; echo "Frontend stopped"; fi

clean: ## Remove generated data (keeps PDFs)
	rm -rf data/extracted/* data/chunks/* data/summaries/* chroma_db/
	@echo "Cleaned all generated data. PDFs preserved."
