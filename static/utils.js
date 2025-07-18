/**
 * Adjust item name alignment dynamically.
 * If text uses fewer than 3 lines, keep bottom alignment.
 * If it uses full height (3 lines), align to top for natural reading.
 */
function adjustItemNameAlignment() {
  const items = document.querySelectorAll('.item-name');
  items.forEach(el => {
    const computed = getComputedStyle(el);
    const lineHeight = parseFloat(computed.lineHeight);
    const reservedHeight = lineHeight * 3;
    const textHeight = el.scrollHeight;

    if (textHeight >= reservedHeight) {
      el.style.alignItems = 'flex-start'; // Long names go top
    } else {
      el.style.alignItems = 'flex-end'; // Short names sit at bottom
    }
  });
}

document.addEventListener('DOMContentLoaded', adjustItemNameAlignment);
window.addEventListener('resize', adjustItemNameAlignment);
