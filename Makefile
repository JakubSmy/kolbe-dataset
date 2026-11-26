.PHONY: help build check lint zip clean

help:  ## Show the targets
	@grep -E '^[a-z]+:.*## ' Makefile | sed 's/:.*## /\t/'

build:  ## Rebuild CSVs, mail and answer key from tools/
	python3 -I tools/build_csv.py KOLBE
	python3 -I tools/build_mail.py KOLBE
	python3 -I tools/build_key.py KOLBE

check:  ## Validate against the brief, check the key, rebuild and compare
	python3 -I tools/validate.py KOLBE
	python3 -I tools/check_key.py KOLBE
	rm -rf dist/rebuild && mkdir -p dist/rebuild/KOLBE
	cp -r KOLBE/documents KOLBE/README.md dist/rebuild/KOLBE/
	python3 -I tools/build_csv.py dist/rebuild/KOLBE > /dev/null
	python3 -I tools/build_mail.py dist/rebuild/KOLBE > /dev/null
	python3 -I tools/build_key.py dist/rebuild/KOLBE > /dev/null
	diff -r KOLBE dist/rebuild/KOLBE && echo "rebuild: identical"

lint:  ## Lint and format check (needs ruff)
	ruff check tools/
	ruff format --check tools/

zip:  ## Build dist/KOLBE.zip, the submission
	mkdir -p dist && rm -f dist/KOLBE.zip && zip -qrX dist/KOLBE.zip KOLBE && echo "dist/KOLBE.zip"

clean:  ## Remove build output
	rm -rf dist
