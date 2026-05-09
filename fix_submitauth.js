    async function submitAuth(e, type) {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.innerHTML = '<svg class="animate-spin w-4 h-4 mx-auto" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>';
        const data = new FormData(form);
        data.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        const url = type === 'login' ? '/auth/login/' : '/auth/register/';
        try {
            const res = await fetch(url, { method: 'POST', body: data });
            const json = await res.json();
            btn.disabled = false;
            btn.textContent = originalText;
            if (json.ok) {
                document.getElementById('authModal').style.display = 'none';
                document.body.style.overflow = '';
                const pendingCart = sessionStorage.getItem('pending_cart_product');
                if (pendingCart) {
                    sessionStorage.removeItem('pending_cart_product');
                    addToCart(pendingCart);
                } else if (window._pendingBuyUrl) {
                    const u = window._pendingBuyUrl; window._pendingBuyUrl = null;
                    window.location.href = u;
                } else if (window._pendingQuote) {
                    const p = window._pendingQuote; window._pendingQuote = null;
                    sessionStorage.setItem('openQuote', JSON.stringify(p));
                    window.location.reload();
                } else if (window._pendingFav) {
                    window._pendingFav = null;
                    sessionStorage.setItem('pendingFavAdded', '1');
                    window.location.reload();
                } else {
                    showCartToast();
                    window.location.reload();
                }
            } else {
                const err = document.getElementById('authError');
                err.textContent = json.error;
                err.classList.remove('hidden');
            }
        } catch (err) {
            btn.disabled = false;
            btn.textContent = originalText;
            document.getElementById('authError').textContent = 'An error occurred. Please try again.';
            document.getElementById('authError').classList.remove('hidden');
        }
    }
