(function () {
    const storageKey = 'todo-sidebar-hidden';
    const body = document.body;
    const toggleButton = document.getElementById('sidebarToggle');
    const closeButton = document.getElementById('sidebarCloseButton');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (!body || !toggleButton) {
        return;
    }

    const isDesktop = () => window.matchMedia('(min-width: 992px)').matches;

    const syncExpandedState = () => {
        const isExpanded = isDesktop()
            ? !body.classList.contains('sidebar-hidden')
            : body.classList.contains('sidebar-mobile-open');

        toggleButton.setAttribute('aria-expanded', String(isExpanded));
    };

    const applySavedDesktopState = () => {
        if (!isDesktop()) {
            body.classList.remove('sidebar-hidden');
            syncExpandedState();
            return;
        }

        const shouldHide = localStorage.getItem(storageKey) === 'true';
        body.classList.toggle('sidebar-hidden', shouldHide);
        body.classList.remove('sidebar-mobile-open');
        syncExpandedState();
    };

    const toggleSidebar = () => {
        if (isDesktop()) {
            const hidden = body.classList.toggle('sidebar-hidden');
            localStorage.setItem(storageKey, String(hidden));
        } else {
            body.classList.toggle('sidebar-mobile-open');
        }

        syncExpandedState();
    };

    const closeMobileSidebar = () => {
        body.classList.remove('sidebar-mobile-open');
        syncExpandedState();
    };

    toggleButton.addEventListener('click', toggleSidebar);

    if (closeButton) {
        closeButton.addEventListener('click', closeMobileSidebar);
    }

    if (backdrop) {
        backdrop.addEventListener('click', closeMobileSidebar);
    }

    window.addEventListener('resize', applySavedDesktopState);
    applySavedDesktopState();
})();
