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
	rm -rf /tmp/kolbe-rebuild && mkdir -p /tmp/kolbe-rebuild/KOLBE
	cp -r KOLBE/documents KOLBE/README.md /tmp/kolbe-rebuild/KOLBE/
	python3 -I tools/build_csv.py /tmp/kolbe-rebuild/KOLBE > /dev/null
	python3 -I tools/build_mail.py /tmp/kolbe-rebuild/KOLBE > /dev/null
	python3 -I tools/build_key.py /tmp/kolbe-rebuild/KOLBE > /dev/null
	diff -r KOLBE /tmp/kolbe-rebuild/KOLBE && echo "rebuild: identical"

lint:  ## Lint and format check (needs ruff)
	ruff check tools/
	ruff format --check tools/

zip:  ## Build dist/KOLBE.zip, the submission
	rm -rf dist && mkdir -p dist && zip -qrX dist/KOLBE.zip KOLBE && echo "dist/KOLBE.zip"

clean:  ## Remove build output
	rm -rf dist /tmp/kolbe-rebuild
