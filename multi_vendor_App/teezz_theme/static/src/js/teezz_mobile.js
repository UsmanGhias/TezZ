/** @odoo-module **/

/**
 * TeZz Mobile Theme — Odoo 17 JS
 * Injects bottom nav, search bar, cart badge, toasts, and product sticky bar
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── Only run on mobile / small screens (or always, CSS handles hiding) ──
    const isMobile = () => window.innerWidth <= 768;

    // ── Inject Google Fonts ──────────────────────────────────────────────────
    if (!document.querySelector('#tz-font')) {
        const link = document.createElement('link');
        link.id = 'tz-font';
        link.rel = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap';
        document.head.appendChild(link);
    }

    // ── Loading bar ──────────────────────────────────────────────────────────
    const ptr = document.createElement('div');
    ptr.className = 'tz-ptr';
    document.body.prepend(ptr);

    // ── Inject bottom navigation ─────────────────────────────────────────────
    if (!document.getElementById('tz-bottom-nav')) {
        const nav = document.createElement('nav');
        nav.id = 'tz-bottom-nav';
        nav.innerHTML = `
            <a class="tz-nav-item" href="/" id="tz-nav-home">
                <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                Home
            </a>
            <a class="tz-nav-item" href="/shop" id="tz-nav-shop">
                <svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 001.95-1.57l1.65-7.43H6"/></svg>
                Shop
            </a>
            <a class="tz-nav-item" href="#" id="tz-nav-search">
                <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                Search
            </a>
            <a class="tz-nav-item" href="/web#action=website.action_website_pages_list" id="tz-nav-cart" style="position:relative">
                <svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 001.95-1.57l1.65-7.43H6"/></svg>
                <span class="tz-cart-badge" id="tz-cart-count">0</span>
                Cart
            </a>
            <a class="tz-nav-item" href="/my" id="tz-nav-account">
                <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                Account
            </a>
        `;
        document.body.appendChild(nav);

        // Correct cart link
        const cartLink = document.getElementById('tz-nav-cart');
        cartLink.href = '/shop/cart';

        // Mark active based on current path
        const path = window.location.pathname;
        if (path === '/') document.getElementById('tz-nav-home').classList.add('active');
        else if (path.startsWith('/shop/cart')) cartLink.classList.add('active');
        else if (path.startsWith('/shop')) document.getElementById('tz-nav-shop').classList.add('active');
        else if (path.startsWith('/my'))   document.getElementById('tz-nav-account').classList.add('active');

        // Search click opens search bar
        document.getElementById('tz-nav-search').addEventListener('click', function (e) {
            e.preventDefault();
            openSearch();
        });
    }

    // ── Search Bar ───────────────────────────────────────────────────────────
    if (!document.getElementById('tz-search-bar')) {
        const bar = document.createElement('div');
        bar.id = 'tz-search-bar';
        bar.innerHTML = `
            <input id="tz-search-input" type="text" placeholder="Search products, brands..." autocomplete="off"/>
            <button id="tz-search-close">✕</button>
        `;
        document.body.appendChild(bar);

        const input = document.getElementById('tz-search-input');
        document.getElementById('tz-search-close').addEventListener('click', closeSearch);

        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && input.value.trim()) {
                window.location.href = '/shop?search=' + encodeURIComponent(input.value.trim());
            }
        });
    }

    function openSearch() {
        document.getElementById('tz-search-bar').classList.add('active');
        setTimeout(() => document.getElementById('tz-search-input').focus(), 50);
    }
    function closeSearch() {
        document.getElementById('tz-search-bar').classList.remove('active');
    }

    // ── Cart badge count ─────────────────────────────────────────────────────
    function updateCartBadge() {
        try {
            // Try reading from Odoo's JS cart store if available
            const cartQty = document.querySelector('.my_cart_quantity');
            let count = 0;
            if (cartQty) {
                count = parseInt(cartQty.textContent.trim()) || 0;
            }
            const badge = document.getElementById('tz-cart-count');
            if (!badge) return;
            if (count > 0) {
                badge.textContent = count > 9 ? '9+' : count;
                badge.classList.add('visible');
            } else {
                badge.classList.remove('visible');
            }
        } catch (e) {}
    }

    // Poll cart qty from DOM (Odoo updates it dynamically)
    updateCartBadge();
    setInterval(updateCartBadge, 2000);

    // Also watch for Odoo ajax cart updates
    const cartQtyEl = document.querySelector('.my_cart_quantity');
    if (cartQtyEl) {
        const observer = new MutationObserver(updateCartBadge);
        observer.observe(cartQtyEl, { childList: true, characterData: true, subtree: true });
    }

    // ── Toast notification ───────────────────────────────────────────────────
    window.tezzToast = function (msg, type = 'info') {
        let toast = document.querySelector('.tz-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'tz-toast';
            document.body.appendChild(toast);
        }
        const icon = type === 'success' ? '✓ ' : type === 'error' ? '✕ ' : 'ℹ ';
        toast.textContent = icon + msg;
        toast.style.borderLeftColor = type === 'success' ? 'var(--tz-success)' : type === 'error' ? 'var(--tz-accent)' : 'var(--tz-gold)';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    };

    // Intercept Odoo "added to cart" alert and show toast instead
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn_add_cart, #add_to_cart, .a-submit');
        if (btn && btn.closest('form')) {
            setTimeout(() => {
                updateCartBadge();
                window.tezzToast('Added to cart!', 'success');
            }, 800);
        }
    }, true);

    // ── Product page sticky bar ──────────────────────────────────────────────
    const onProductPage = document.querySelector('#product_detail, .o_product_page, .product_detail_main');
    if (onProductPage && isMobile()) {
        buildProductStickyBar(onProductPage);
    }

    function buildProductStickyBar(page) {
        // Check if not already built
        if (document.querySelector('.tz-product-sticky-bar')) return;

        const originalForm = document.querySelector('form#cart_items, #product_detail form, .product_detail_main form');
        if (!originalForm) return;

        // Get original qty input and add-to-cart button
        const qtyInput   = originalForm.querySelector('input[name="add_qty"], input.js_quantity, input[name="qty"]');
        const cartBtn    = originalForm.querySelector('#add_to_cart, input[name="add_to_cart"], button.btn_add_cart');

        const bar = document.createElement('div');
        bar.className = 'tz-product-sticky-bar';

        const qty = (qtyInput ? parseInt(qtyInput.value) : 1);

        bar.innerHTML = `
            <div class="tz-qty-wrap">
                <button class="tz-qty-btn" id="tz-qty-minus">−</button>
                <input class="tz-qty-val" id="tz-qty-disp" type="number" value="${qty}" min="1" readonly/>
                <button class="tz-qty-btn" id="tz-qty-plus">+</button>
            </div>
            <button class="tz-add-cart-btn" id="tz-add-cart">
                🛒  Add to Cart
            </button>
        `;
        document.body.insertBefore(bar, document.getElementById('tz-bottom-nav'));

        let localQty = qty;

        document.getElementById('tz-qty-minus').addEventListener('click', function () {
            if (localQty > 1) {
                localQty--;
                document.getElementById('tz-qty-disp').value = localQty;
                if (qtyInput) qtyInput.value = localQty;
            }
        });
        document.getElementById('tz-qty-plus').addEventListener('click', function () {
            localQty++;
            document.getElementById('tz-qty-disp').value = localQty;
            if (qtyInput) qtyInput.value = localQty;
        });

        document.getElementById('tz-add-cart').addEventListener('click', function () {
            const btn = this;
            btn.innerHTML = '<span class="tz-loading"></span>';
            btn.disabled = true;
            if (qtyInput) qtyInput.value = localQty;
            if (cartBtn) cartBtn.click();
            setTimeout(() => {
                btn.innerHTML = '🛒  Add to Cart';
                btn.disabled = false;
                updateCartBadge();
                window.tezzToast('Added to cart!', 'success');
            }, 1200);
        });
    }

    // ── Fix Odoo shop search input on mobile ─────────────────────────────────
    const odooSearchInput = document.querySelector('input[name="search"], .oe_search_box input');
    if (odooSearchInput) {
        odooSearchInput.style.cssText = `
            background: var(--tz-card) !important;
            color: var(--tz-text) !important;
            border: 1.5px solid rgba(255,255,255,.1) !important;
            border-radius: 12px !important;
            padding: 10px 16px !important;
        `;
    }

    // ── Smooth page transitions ───────────────────────────────────────────────
    document.querySelectorAll('a[href]').forEach(function (link) {
        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript') || href.startsWith('mailto') || link.target === '_blank') return;
        link.addEventListener('click', function () {
            ptr.classList.add('loading');
        });
    });
    window.addEventListener('pageshow', function () {
        ptr.classList.remove('loading');
    });

    // ── Fix Odoo messages / flashes to use dark style ─────────────────────────
    document.querySelectorAll('.o_website_rating_card').forEach(el => {
        el.style.background = 'var(--tz-card)';
        el.style.borderRadius = 'var(--tz-radius)';
        el.style.border = '1px solid rgba(255,255,255,.06)';
    });

    // ── Homepage: inject hero if on homepage ──────────────────────────────────
    const isHome = (window.location.pathname === '/' || window.location.pathname === '/web');
    if (isHome && !document.querySelector('.tz-hero')) {
        const contentArea = document.querySelector('#wrap > .container, #wrap > .container-fluid, main#wrap .oe_structure');
        if (contentArea) {
            const hero = document.createElement('div');
            hero.className = 'tz-hero';
            hero.innerHTML = `
                <h1>Welcome to <span>Te</span><span style="color:var(--tz-accent)">Zz</span></h1>
                <p>Pakistan's fastest multi-vendor marketplace</p>
                <a href="/shop" class="tz-hero-btn">Shop Now</a>
            `;
            contentArea.insertBefore(hero, contentArea.firstChild);
        }
    }

    // ── Dark-mode meta (status bar color for WebView) ─────────────────────────
    let metaTheme = document.querySelector('meta[name="theme-color"]');
    if (!metaTheme) {
        metaTheme = document.createElement('meta');
        metaTheme.name = 'theme-color';
        document.head.appendChild(metaTheme);
    }
    metaTheme.content = '#1a1a2e';

    // ── Touch feedback ────────────────────────────────────────────────────────
    document.querySelectorAll('.oe_product_cart, .tz-product-card, .btn').forEach(function (el) {
        el.addEventListener('touchstart', () => el.style.opacity = '.85', { passive: true });
        el.addEventListener('touchend',   () => el.style.opacity = '1',   { passive: true });
    });

    // ── Pull to refresh ───────────────────────────────────────────────────────
    if (isMobile()) {
        let startY = 0;
        let pulling = false;
        document.addEventListener('touchstart', e => { startY = e.touches[0].pageY; }, { passive: true });
        document.addEventListener('touchmove', e => {
            if (document.documentElement.scrollTop === 0 && e.touches[0].pageY - startY > 80 && !pulling) {
                pulling = true;
                ptr.classList.add('loading');
            }
        }, { passive: true });
        document.addEventListener('touchend', () => {
            if (pulling) {
                pulling = false;
                setTimeout(() => { ptr.classList.remove('loading'); window.location.reload(); }, 600);
            }
        }, { passive: true });
    }

    console.log('[TeZz] Mobile theme loaded ✓');
});
