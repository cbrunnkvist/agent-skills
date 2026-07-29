UPSTREAM_REPO ?= git@github.com:portainer/portainer-api-docs.git
UPSTREAM_DIR  := upstream
SPEC_DIR       = references/spec

.PHONY: specs

# Refresh references/spec/ from upstream (EE — the edition the skill bundles)
# Usage: make specs VERSION=2.42.0
specs:
	@if [ -z "$(VERSION)" ]; then \
		echo "VERSION is required, e.g. make specs VERSION=2.42.0" >&2; \
		exit 1; \
	fi
	@if [ -d $(UPSTREAM_DIR)/.git ]; then \
		git -C $(UPSTREAM_DIR) fetch --depth=1 origin HEAD && \
		git -C $(UPSTREAM_DIR) reset --hard FETCH_HEAD; \
	else \
		git clone --depth=1 --filter=blob:none --no-checkout \
			$(UPSTREAM_REPO) $(UPSTREAM_DIR); \
	fi
	git -C $(UPSTREAM_DIR) sparse-checkout set --no-cone /versions/ee/$(VERSION)/
	git -C $(UPSTREAM_DIR) checkout
	@stage_dir=$$(mktemp -d "$$(dirname "$(SPEC_DIR)")/.spec-stage.XXXXXX"); \
	backup_dir=$$(mktemp -d "$$(dirname "$(SPEC_DIR)")/.spec-backup.XXXXXX"); \
	rmdir "$$backup_dir"; \
	cleanup() { rm -rf "$$stage_dir" "$$backup_dir"; }; \
	trap cleanup EXIT; \
	cp $(UPSTREAM_DIR)/versions/ee/$(VERSION)/*.yaml "$$stage_dir"/; \
	uv run --with pyyaml scripts/postprocess_specs.py "$$stage_dir" \
		--version $(VERSION); \
	test -f "$$stage_dir/openapi.yaml" && test -f "$$stage_dir/INDEX.md"; \
	if [ -d "$(SPEC_DIR)" ]; then mv "$(SPEC_DIR)" "$$backup_dir"; fi; \
	if ! mv "$$stage_dir" "$(SPEC_DIR)"; then \
		if [ -d "$$backup_dir" ]; then mv "$$backup_dir" "$(SPEC_DIR)"; fi; \
		exit 1; \
	fi; \
	stage_dir=; rm -rf "$$backup_dir"; trap - EXIT
