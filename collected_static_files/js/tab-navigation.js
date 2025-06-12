window.addEventListener('DOMContentLoaded', () => {
    const tabBar = document.getElementById('open-tabs');
    let contentArea = document.querySelector('.main-content');
    if (!tabBar || !contentArea) return;

    function getTabs() {
        return JSON.parse(sessionStorage.getItem('openTabs') || '[]');
    }
    function saveTabs(tabs) {
        sessionStorage.setItem('openTabs', JSON.stringify(tabs));
    }

    function addTab(title, url) {
        const tabs = getTabs();
        if (!tabs.find(t => t.url === url)) {
            tabs.push({ title, url });
            saveTabs(tabs);
        }
    }

    function renderTabs(activeUrl = window.location.pathname) {
        tabBar.innerHTML = '';
        getTabs().forEach(tab => {
            const li = document.createElement('li');
            li.className = 'nav-item';
            const a = document.createElement('a');
            a.className = 'nav-link' + (tab.url === activeUrl ? ' active' : '');
            a.textContent = tab.title;
            a.href = tab.url;
            li.appendChild(a);
            const closeBtn = document.createElement('button');
            closeBtn.textContent = '×';
            closeBtn.className = 'ms-1 btn-close';
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                closeTab(tab.url);
            });
            a.appendChild(closeBtn);
            tabBar.appendChild(li);
        });
    }

    function closeTab(url) {
        const tabs = getTabs().filter(t => t.url !== url);
        saveTabs(tabs);
        if (url === window.location.pathname) {
            const next = tabs[tabs.length - 1];
            if (next) navigate(next.url); else renderTabs();
        } else {
            renderTabs();
        }
    }

    function navigate(url, push = true) {
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(resp => resp.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('.main-content');
                if (!newContent) {
                    window.location.href = url;
                    return;
                }
                contentArea.replaceWith(newContent);
                contentArea = newContent;
                document.title = doc.title;
                const path = new URL(url).pathname;
                addTab(doc.title, path);
                renderTabs(path);
                if (push) history.pushState({}, '', path);
                if (window.feather) feather.replace();
            });
    }

    // Initial tab
    addTab(document.title, window.location.pathname);
    renderTabs();

    document.body.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (!link || link.target || link.hasAttribute('download') || link.getAttribute('href').startsWith('#')) return;
        if (link.origin !== location.origin) return;
        e.preventDefault();
        navigate(link.href);
    });

    window.addEventListener('popstate', () => {
        navigate(location.href, false);
    });

    // Global controls
    window.closeCurrentTab = () => closeTab(window.location.pathname);
    window.closeAllTabs = () => {
        saveTabs([]);
        renderTabs();
    };
    window.closeOtherTabs = () => {
        saveTabs([{ title: document.title, url: window.location.pathname }]);
        renderTabs(window.location.pathname);
    };
});