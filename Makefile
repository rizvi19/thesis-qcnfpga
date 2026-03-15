PYTHON ?= python
MODEL  ?= reference_model.py
OUT    ?= results/phase0

.PHONY: init audit phase0 clean

init:
	$(PYTHON) init_repo_structure.py --root .

audit:
	$(PYTHON) audit_reference_model.py --model $(MODEL) --out $(OUT)

phase0: init audit

clean:
	@echo "Nothing destructive is removed automatically."
