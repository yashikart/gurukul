// Prevent flash of wrong theme (runs before app mounts)
(function () {
  try {
    var theme = localStorage.getItem('theme');
    var systemPrefersDark = false;
    try {
      systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    } catch (e) {}

    if (theme === 'dark' || (!theme && systemPrefersDark)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  } catch (e) {
    // Fail silently to avoid blocking render
  }
})();
