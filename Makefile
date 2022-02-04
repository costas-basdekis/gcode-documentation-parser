clean: clean-caches
.PHONY: clean

clean-caches:
	$(RM) -r .tox .mypy_cache .pytest_cache
	find -name __pycache__ -prune -exec rm -r '{}' \;
	find -name '*.py[co]' -delete
.PHONY: caches

install:
	poetry install
.PHONY: install

lint:
	pre-commit run --all-files
.PHONY: lint

test:
	pytest "$(ARGS)"
.PHONY: test
