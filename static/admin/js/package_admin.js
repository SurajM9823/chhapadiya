// Package Admin Dynamic Calculations
(function($) {
    $(document).ready(function() {
        // Auto-calculate item totals when quantity or discount changes
        function calculateItemTotal(row) {
            const productSelect = row.find('select[name*="product"]');
            const quantityInput = row.find('input[name*="quantity"]');
            const discountInput = row.find('input[name*="item_discount"]');
            const totalField = row.find('.field-get_item_total');
            
            if (productSelect.length && quantityInput.length) {
                const productId = productSelect.val();
                const quantity = parseInt(quantityInput.val()) || 0;
                const discount = parseFloat(discountInput.val()) || 0;
                
                if (productId && quantity > 0) {
                    // Get product price via AJAX
                    $.ajax({
                        url: '/admin/web/product/' + productId + '/change/',
                        method: 'GET',
                        success: function(data) {
                            // Extract MRP from response (simplified)
                            // In production, create a dedicated API endpoint
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(data, 'text/html');
                            const mrpField = doc.querySelector('input[name="mrp"]');
                            if (mrpField) {
                                const mrp = parseFloat(mrpField.value) || 0;
                                const itemTotal = (mrp * quantity) - discount;
                                totalField.text('₹' + itemTotal.toFixed(2));
                            }
                        }
                    });
                }
            }
        }
        
        // Attach event listeners to inline forms
        $('#packageitem_set-group').on('change', 'select[name*="product"], input[name*="quantity"], input[name*="item_discount"]', function() {
            const row = $(this).closest('tr');
            calculateItemTotal(row);
        });
        
        // Calculate suggested selling price
        $('#id_overall_discount').on('input', function() {
            const totalMrp = parseFloat($('.field-total_mrp .readonly').text().replace('₹', '').replace(',', '')) || 0;
            const overallDiscount = parseFloat($(this).val()) || 0;
            const suggestedPrice = totalMrp - overallDiscount;
            
            if (suggestedPrice > 0 && !$('#id_selling_price').val()) {
                $('#id_selling_price').val(suggestedPrice.toFixed(2));
            }
        });
        
        // Highlight savings
        function updateSavings() {
            const totalMrp = parseFloat($('.field-total_mrp .readonly').text().replace('₹', '').replace(',', '')) || 0;
            const sellingPrice = parseFloat($('#id_selling_price').val()) || 0;
            const savings = totalMrp - sellingPrice;
            
            if (savings > 0) {
                const percent = (savings / totalMrp * 100).toFixed(1);
                const savingsHtml = `<span style="color: #28a745; font-weight: bold;">Savings: ₹${savings.toFixed(2)} (${percent}%)</span>`;
                $('.field-selling_price').append(`<div class="help">${savingsHtml}</div>`);
            }
        }
        
        $('#id_selling_price').on('blur', updateSavings);
    });
})(django.jQuery);
