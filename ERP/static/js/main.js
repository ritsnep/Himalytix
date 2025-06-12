const overlay = document.getElementById('loading-overlay');

document.body.addEventListener('htmx:requestStart', () => overlay.classList.add('show'));
document.body.addEventListener('htmx:afterSwap',   () => overlay.classList.remove('show'));
document.body.addEventListener('htmx:responseError',() => overlay.classList.remove('show'));

document.addEventListener('DOMContentLoaded', () => {
    const stored = localStorage.getItem('theme');
    if (stored) {
        document.documentElement.setAttribute('data-layout-mode', stored);
    }
    const toggle = document.querySelector('.theme-toggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            const attr = document.documentElement.getAttribute('data-layout-mode');
            const next = attr === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-layout-mode', next);
            localStorage.setItem('theme', next);
            document.cookie = `theme=${next};path=/`;
        });
    }
});

htmx.on('htmx:beforeSwap', () => {
    document.documentElement.setAttribute('data-layout-mode', localStorage.getItem('theme') || 'light');
});