/**
 * Adjust vertical alignment for item names inside cards.
 * If text uses fewer than 3 lines, push it down to align visually.
 */
function adjustItemNamePadding() {
  const items = document.querySelectorAll('.item-name');
  items.forEach(el => {
    const computedStyle = getComputedStyle(el);
    const lineHeight = parseFloat(computedStyle.lineHeight);
    const height = el.scrollHeight;
    const lines = Math.round(height / lineHeight);
    const maxLines = 3;
    const reservedHeight = lineHeight * maxLines;

    if (lines < maxLines) {
      const extraSpace = reservedHeight - height;
      el.style.paddingTop = `${extraSpace}px`;
    } else {
      el.style.paddingTop = '0';
    }
  });
}

// Run on page load and resize
document.addEventListener('DOMContentLoaded', adjustItemNamePadding);
window.addEventListener('resize', adjustItemNamePadding);
