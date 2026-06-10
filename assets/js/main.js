/* ════════════════════════════════════════════
   PRAGUE'S BARREL — shared behaviour + i18n
   Each page defines `const I18N = {en:{},cs:{},de:{},fr:{},it:{}}`
   before loading this script. Elements opt in via data-i18n="key".
   ════════════════════════════════════════════ */

(function () {
  var SUPPORTED = ['en', 'cs', 'de', 'fr', 'it'];

  function applyLang(lang) {
    document.documentElement.lang = lang;
    try { localStorage.setItem('pb-lang', lang); } catch (e) {}
    var dict = (typeof I18N !== 'undefined' && I18N[lang]) || {};
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var v = dict[el.getAttribute('data-i18n')];
      if (v !== undefined) el.innerHTML = v;
    });
    if (dict['meta.title']) document.title = dict['meta.title'];
    var desc = document.querySelector('meta[name="description"]');
    if (desc && dict['meta.desc']) desc.setAttribute('content', dict['meta.desc']);
    document.querySelectorAll('.lang-switcher button').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-lang') === lang);
    });
  }

  function initialLang() {
    var fromUrl = new URLSearchParams(location.search).get('lang');
    if (fromUrl && SUPPORTED.indexOf(fromUrl) !== -1) return fromUrl;
    var saved = null;
    try { saved = localStorage.getItem('pb-lang'); } catch (e) {}
    if (saved && SUPPORTED.indexOf(saved) !== -1) return saved;
    var nav = (navigator.language || 'en').slice(0, 2).toLowerCase();
    return SUPPORTED.indexOf(nav) !== -1 ? nav : 'en';
  }

  document.querySelectorAll('.lang-switcher button').forEach(function (b) {
    b.addEventListener('click', function () { applyLang(b.getAttribute('data-lang')); });
  });
  applyLang(initialLang());

  // Sticky nav shadow
  var nav = document.getElementById('nav');
  if (nav) {
    window.addEventListener('scroll', function () {
      nav.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // Scroll reveal
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) e.target.classList.add('visible');
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.reveal').forEach(function (el) { observer.observe(el); });

  // FAQ accordion
  document.querySelectorAll('.faq-q').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.closest('.faq-item');
      var wasOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item.open').forEach(function (i) { i.classList.remove('open'); });
      if (!wasOpen) item.classList.add('open');
    });
  });

  // Mobile menu
  var menuBtn = document.getElementById('menuBtn');
  if (menuBtn) {
    menuBtn.addEventListener('click', function () {
      var links = document.querySelector('.nav-links');
      if (links) links.classList.toggle('open');
    });
  }
})();
