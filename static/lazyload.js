// lazyload.js
// Basic image lazy loading using IntersectionObserver
// Applies to images with a `data-src` attribute.

function initLazyLoad() {
  const images = document.querySelectorAll('img[data-src]');
  if (!images.length) return;

  const loadImage = img => {
    img.src = img.dataset.src;
    img.removeAttribute('data-src');
  };

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          loadImage(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '50px' });

    images.forEach(img => observer.observe(img));
  } else {
    // Fallback: load all images immediately
    images.forEach(loadImage);
  }
}

document.addEventListener('DOMContentLoaded', initLazyLoad);
