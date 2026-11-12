class I18n {
  constructor() {
    this.locale = localStorage.getItem('ds1_lang') || 'ar';
    this.translations = {};
    this.subscribers = [];
  }

  async init() {
    await this.loadTranslations(this.locale);
    this.updateDOM();
  }

  async loadTranslations(lang) {
    try {
      const res = await fetch(`/assets/i18n/${lang}.json`);
      if (!res.ok) throw new Error('Failed to load translations');
      this.translations = await res.json();
    } catch (e) {
      console.error(e);
      this.translations = {}; // fallback empty
    }
  }

  async setLocale(lang) {
    if (this.locale === lang) return;
    this.locale = lang;
    localStorage.setItem('ds1_lang', lang);
    await this.loadTranslations(lang);
    this.updateDOM();
    this.subscribers.forEach(cb => cb());
  }

  t(key, params = {}) {
    let text = this.translations[key] || key;
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(new RegExp(`{${k}}`, 'g'), v);
    }
    return text;
  }

  updateDOM() {
    document.documentElement.lang = this.locale;
    document.documentElement.dir = this.locale === 'ar' ? 'rtl' : 'ltr';

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (this.translations[key]) {
        el.innerHTML = this.translations[key];
      }
    });
  }

  subscribe(cb) {
    this.subscribers.push(cb);
  }
}

window.i18n = new I18n();
