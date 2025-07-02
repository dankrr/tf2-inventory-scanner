# Pull Request Checklist

Use this checklist when submitting the modal refactor PR.

- [ ] **Backend → UI**: verify `/retry/<id>` returns the expected HTML with `data-item` payloads described in `docs/ENRICHMENT_PIPELINE.md`.
- [ ] **UI → Backend**: clicking a retry pill triggers a POST request and the updated card renders correctly.
- [ ] Unit tests cover `modal.js` and updated `retry.js` logic.
- [ ] Integration test demonstrates the modal loading then displaying item details.
- [ ] CI pipeline and `pre-commit` pass on the branch.
