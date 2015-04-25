.PHONY: dev
dev:
	@tox -e pre-commit -- install -f --install-hooks

.PHONY: test
test: dev
	@tox
