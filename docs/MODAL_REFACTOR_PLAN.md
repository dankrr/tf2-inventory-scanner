# Modal Refactor Plan

This plan describes how to extract all modal related logic from `static/retry.js` into a new module `static/modal.js`.

## 1. Discovery & Mapping
- **File:** `static/retry.js`
- Functions interacting with the modal:
  - `attachItemModal()` – sets up event listeners and updates the modal contents.
  - Inline `closeModal()` within `attachItemModal()` handles fade out and `dialog.close()`.
  - `document.addEventListener('DOMContentLoaded', attachItemModal);` – initialises the modal.
- DOM queries involved: `#item-modal`, `#modal-title`, `#modal-effect`, `#modal-img`, `#modal-details`, `#modal-badges`.
- Responsibilities:
  - **Initialisation** – attaching click handlers to `.item-card` elements and the modal backdrop.
  - **State control** – calling `modal.showModal()`, setting opacity, and closing on backdrop click.
  - **Content population** – parsing `data-item` JSON and building DOM nodes for attributes, spells and badges.
- Backend dependency: the HTML snippet for each user embeds an item payload in `data-item` used to populate the modal. No separate modal fields are returned by the `/retry/<id>` endpoint.

## 2. New Interface
Expose a small API from `modal.js`:
```js
initModal();            // sets up close/backdrop listeners
openModal(html);        // injects HTML and opens the dialog
closeModal();           // hides the dialog
updateModal?(html);     // optional helper to replace existing content
```
`retry.js` will call `openModal()` whenever an item card is clicked and `closeModal()` from any close button or backdrop handler.

## 3. Separation Plan
- Move backdrop click and fade logic from `attachItemModal()` into `initModal()`.
- Replace direct DOM class toggles with `openModal` and `closeModal` calls.
- Keep the domain specific HTML assembly (`createItemDetailHTML` or equivalent) inside `retry.js` and pass the resulting markup to `modal.js`.
- Remaining references in `retry.js` will only build the HTML for item details.

## 4. Backend Verification
- Hitting `/retry/<id>` still returns the same user card HTML with `data-item` attributes. No JSON fields need to change.
- The expected item schema is documented in `docs/ENRICHMENT_PIPELINE.md` under **Modal Payload**.

## 5. Frontend Wiring
- Include `modal.js` before `retry.js` in `index.html`.
- `retry.js` should import the modal functions (via ES module import or global inclusion) and call `initModal()` on page load.
- Ensure no global name conflicts are introduced; use a module namespace if ES modules are supported.

## 6. Back-to-Front Checks
1. User clicks an item → `retry.js` calls `openModal('Loading…')`.
2. AJAX refresh resolves → `openModal(itemHtml)` replaces the modal content.
3. Clicking outside the dialog or a dedicated close button triggers `closeModal()`.

## 7. Automated Tests
- Add unit tests for the modal module using JSDOM:
  - `openModal` inserts HTML and adds the `.open` class.
  - `closeModal` removes the `.open` class and clears listeners.
- Add a browser test stub with Playwright or Selenium verifying that a retry action updates the modal from “Loading…” to populated details.
- Add a backend contract test asserting that `/retry/<id>` continues to embed all fields listed in **Modal Payload**.

## 8. CI and Pre-commit
- Extend the JS test runner and `pytest` steps in CI to execute the new tests.
- Ensure the pre-commit hook runs the JS linter for both `retry.js` and `modal.js`.

## 9. Documentation
- Update the README architecture section to note the flow `retry.js → modal.js`.
- Document the modal data path in `docs/ENRICHMENT_PIPELINE.md`.
- PR checklist:
  - [ ] Modal behaviour unchanged in the UI.
  - [ ] `/retry/<id>` payload includes all documented fields.
  - [ ] Unit and integration tests added.
  - [ ] CI and pre-commit pass.
