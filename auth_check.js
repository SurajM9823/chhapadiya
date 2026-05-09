async function checkAuthAndAddCart() {
    try {
        const res = await fetch('/api/wishlist/');
        if (res.ok) {
            const data = await res.json();
            if (data.wishlisted_ids !== undefined) {
                const pendingCart = sessionStorage.getItem('pending_cart_product');
                if (pendingCart) {
                    sessionStorage.removeItem('pending_cart_product');
                    await new Promise(r => setTimeout(r, 100));
                    addToCart(pendingCart);
                }
            }
        }
    } catch(e) {}
}
checkAuthAndAddCart();
