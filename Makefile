# Makefile for the HalluScope replication
#
# Single-command reproduction targets:
#   make data        validate the committed datasets, build the unified prompt file
#   make aggregate   rebuild results/tables + results/figures from committed outputs
#   make all         data + aggregate
#   make tests       run tests/ (12 sanity tests + stage-contract fixtures)
#   make smoke       tiny end-to-end pipeline test (downloads Qwen2-0.5B, CPU-ok)
#   make clean       remove __pycache__ and .pyc files
#
# On Windows without GNU Make, the equivalent Python entry point is run_all.py.
# The full GPU model runs are documented in integration/COLAB_GUIDE.md.

PYTHON ?= python

.PHONY: all data aggregate tests smoke clean help

help:
	@echo "Targets: data | aggregate | all | tests | smoke | clean"

data:
	$(PYTHON) data/fetch_datasets.py

aggregate:
	$(PYTHON) run_all.py --only aggregate

all: data aggregate
	@echo "Tables and figures rebuilt under results/."

tests:
	$(PYTHON) -m pytest tests/ -v

smoke: data
	$(PYTHON) integration/run_pipeline.py --model Qwen/Qwen2-0.5B-Instruct --alias smoke --limit 2 --max-new-tokens 64

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Removed __pycache__ directories and .pyc files."
