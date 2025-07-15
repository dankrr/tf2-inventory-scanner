// lazyload.js
// Basic image lazy loading using IntersectionObserver
// Applies to images with a `data-src` attribute.

let lazyObserver;

function loadImage(img) {
  img.src = img.dataset.src;
  img.removeAttribute('data-src');
}

function initLazyLoad() {
  const images = document.querySelectorAll('img[data-src]');
  if (!images.length) return;

  if ('IntersectionObserver' in window) {
    lazyObserver = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            loadImage(entry.target);
            lazyObserver.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '50px' }
    );

    images.forEach(img => lazyObserver.observe(img));
  } else {
    // Fallback: load all images immediately
    images.forEach(loadImage);
  }
}

window.refreshLazyLoad = function () {
  document
    .querySelectorAll('img[data-src]')
    .forEach(img => lazyObserver && lazyObserver.observe(img));
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLazyLoad);
} else {
  initLazyLoad();
}
