# Frontend Changes

## Features Added

### 1. Copy Button on Assistant Messages
- A clipboard icon button appears below each AI response when the user hovers over the message
- Clicking it copies the raw markdown text to the clipboard using the `navigator.clipboard` API (with a `document.execCommand` fallback for older browsers)
- The button icon switches to a checkmark for 2 seconds to confirm the copy, then reverts
- Not shown on the welcome message (only on real AI responses)

**Files changed:**
- `frontend/index.html` — no structural change needed (button is injected by JS)
- `frontend/style.css` — added `.message-actions`, `.copy-btn`, and `.copy-btn.copied` styles; added `position: relative` to `.chat-container`
- `frontend/script.js` — added `CLIPBOARD_ICON` / `CHECK_ICON` SVG constants; modified `addMessage()` to inject copy button and attach click handler for assistant messages

### 2. Scroll-to-Bottom Button
- A floating pill button ("↓ Scroll to bottom") appears centered above the chat input when the user has scrolled more than 200px from the bottom
- Clicking it smoothly scrolls the chat back to the latest message
- Automatically hides when the user is already near the bottom

**Files changed:**
- `frontend/index.html` — added `<button id="scrollToBottomBtn">` inside `.chat-container`
- `frontend/style.css` — added `.scroll-to-bottom-btn` and `.scroll-to-bottom-btn.visible` styles
- `frontend/script.js` — added `scrollToBottomBtn` DOM reference, scroll event listener on `#chatMessages` to toggle `.visible`, and click handler to smooth-scroll to bottom
