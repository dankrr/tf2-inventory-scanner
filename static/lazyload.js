// lazyload.js
// Basic image lazy loading using IntersectionObserver
// Applies to images with a `data-src` attribute.

let observer;

function loadImage(img) {
  img.src = img.dataset.src;
  img.removeAttribute('data-src');
}

function initLazyLoad() {
  const images = document.querySelectorAll('img[data-src]');
  if (!images.length) return;

  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            loadImage(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '50px' }
    );

    images.forEach(img => observer.observe(img));
  } else {
    // Fallback: load all images immediately
    images.forEach(loadImage);
  }
}

window.refreshLazyLoad = function () {
  if (!observer && 'IntersectionObserver' in window) {
    initLazyLoad();
    return;
  }
  document.querySelectorAll('img[data-src]').forEach(img => {
    if (observer) {
      observer.observe(img);
    } else {
      loadImage(img);
    }
  });
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLazyLoad);
} else {
  initLazyLoad();
}
