.PHONY: install test lint demo pipeline sample

install:
	pip install -e ".[dev]"

sample:
	housing generate-sample --out data/sample/regional_price_index.csv --regions 12 --months 96

test:
	pytest

lint:
	ruff check src tests

demo: sample
	bash scripts/demo.sh

pipeline:
	bash scripts/pipeline.sh
