from django.core.mail import send_mail
from .models import SiteSettings


def send_order_confirmation_email(order):
    """Send order confirmation email to customer and admin."""
    try:
        subject = f'Order Confirmation - #{order.order_number}'
        
        items_html = ''
        for item in order.items.all():
            items_html += f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 12px; text-align: left;">{item.product_name}</td>
                <td style="padding: 12px; text-align: center;">{item.quantity}</td>
                <td style="padding: 12px; text-align: right;">Rs. {item.unit_price}</td>
                <td style="padding: 12px; text-align: right;">Rs. {item.subtotal}</td>
            </tr>
            """
        
        customer_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; }}
                .order-details {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .order-details h3 {{ margin-top: 0; color: #059669; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background-color: #f3f4f6; padding: 12px; text-align: left; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .status-badge {{ display: inline-block; background-color: #fef3c7; color: #92400e; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Order Confirmed!</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Thank you for your order</p>
                </div>
                
                <div class="content">
                    <p>Hi <strong>{order.full_name}</strong>,</p>
                    <p>Your order has been successfully placed and is being processed. Here are your order details:</p>
                    
                    <div class="order-details">
                        <h3>Order Information</h3>
                        <p><strong>Order Number:</strong> #{order.order_number}</p>
                        <p><strong>Status:</strong> <span class="status-badge">{order.get_status_display()}</span></p>
                        <p><strong>Order Date:</strong> {order.created_at.strftime('%d %B %Y, %I:%M %p')}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Items Ordered</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Qty</th>
                                    <th>Price</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="order-details">
                        <h3>Delivery Details</h3>
                        <p><strong>Delivery Type:</strong> {order.get_delivery_type_display()}</p>
                        <p><strong>Name:</strong> {order.full_name}</p>
                        <p><strong>Phone:</strong> {order.phone}</p>
                        <p><strong>Address:</strong> {order.address}, {order.city}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Payment Summary</h3>
                        <table style="border: none;">
                            <tr style="border: none;">
                                <td style="padding: 8px; text-align: left; border: none;"><strong>Subtotal:</strong></td>
                                <td style="padding: 8px; text-align: right; border: none;">Rs. {order.subtotal}</td>
                            </tr>
                            <tr style="border: none;">
                                <td style="padding: 8px; text-align: left; border: none;"><strong>Delivery Charge:</strong></td>
                                <td style="padding: 8px; text-align: right; border: none;">Rs. {order.delivery_charge}</td>
                            </tr>
                            <tr style="border-top: 2px solid #059669;">
                                <td style="padding: 12px; text-align: left; font-weight: bold; font-size: 16px;"><strong>Total Amount:</strong></td>
                                <td style="padding: 12px; text-align: right; font-weight: bold; font-size: 16px; color: #059669;">Rs. {order.total}</td>
                            </tr>
                        </table>
                        <p><strong>Payment Method:</strong> {order.get_payment_method_display()}</p>
                    </div>
                    
                    <p>You can track your order status anytime by visiting your account on our website.</p>
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                </div>
                
                <div class="footer">
                    <p>Thank you for shopping with us!</p>
                    <p>© Aarambha Foundation. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        settings = SiteSettings.get()
        from_email = f'Aarambha Foundation <{settings.email or "suraj20001123@gmail.com"}>'
        
        send_mail(
            subject=subject,
            message=f'Order #{order.order_number} has been placed successfully.',
            from_email=from_email,
            recipient_list=[order.email],
            html_message=customer_html,
            fail_silently=False,
        )
        print(f'Order confirmation email sent to customer: {order.email}')
        
        admin_subject = f'New Order Received - #{order.order_number}'
        admin_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; }}
                .order-details {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .order-details h3 {{ margin-top: 0; color: #dc2626; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background-color: #f3f4f6; padding: 12px; text-align: left; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .alert {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">New Order Alert</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Order #{order.order_number}</p>
                </div>
                
                <div class="content">
                    <div class="alert">
                        <strong>A new order has been placed!</strong>
                    </div>
                    
                    <div class="order-details">
                        <h3>Customer Information</h3>
                        <p><strong>Name:</strong> {order.full_name}</p>
                        <p><strong>Email:</strong> {order.email}</p>
                        <p><strong>Phone:</strong> {order.phone}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Order Details</h3>
                        <p><strong>Order Number:</strong> #{order.order_number}</p>
                        <p><strong>Order Date:</strong> {order.created_at.strftime('%d %B %Y, %I:%M %p')}</p>
                        <p><strong>Delivery Type:</strong> {order.get_delivery_type_display()}</p>
                        <p><strong>Payment Method:</strong> {order.get_payment_method_display()}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Items Ordered</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Qty</th>
                                    <th>Price</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="order-details">
                        <h3>Delivery Address</h3>
                        <p>{order.full_name}</p>
                        <p>{order.address}</p>
                        <p>{order.city}</p>
                        <p>Phone: {order.phone}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Payment Summary</h3>
                        <table style="border: none;">
                            <tr style="border: none;">
                                <td style="padding: 8px; text-align: left; border: none;"><strong>Subtotal:</strong></td>
                                <td style="padding: 8px; text-align: right; border: none;">Rs. {order.subtotal}</td>
                            </tr>
                            <tr style="border: none;">
                                <td style="padding: 8px; text-align: left; border: none;"><strong>Delivery Charge:</strong></td>
                                <td style="padding: 8px; text-align: right; border: none;">Rs. {order.delivery_charge}</td>
                            </tr>
                            <tr style="border-top: 2px solid #dc2626;">
                                <td style="padding: 12px; text-align: left; font-weight: bold; font-size: 16px;"><strong>Total Amount:</strong></td>
                                <td style="padding: 12px; text-align: right; font-weight: bold; font-size: 16px; color: #dc2626;">Rs. {order.total}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        if settings.email:
            send_mail(
                subject=admin_subject,
                message=f'New order #{order.order_number} received from {order.full_name}',
                from_email=from_email,
                recipient_list=[settings.email],
                html_message=admin_html,
                fail_silently=False,
            )
            print(f'Order notification email sent to admin: {settings.email}')
        
    except Exception as e:
        print(f'Error sending order emails: {e}')
        import traceback
        traceback.print_exc()


def send_order_status_update_email(order, old_status, new_status):
    """Send order status update email to customer."""
    try:
        status_messages = {
            'pending': 'Your order is pending confirmation',
            'confirmed': 'Your order has been confirmed',
            'processing': 'Your order is being processed',
            'shipped': 'Your order has been shipped',
            'delivered': 'Your order has been delivered',
            'cancelled': 'Your order has been cancelled',
        }
        
        status_colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'processing': '#8b5cf6',
            'shipped': '#06b6d4',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
        }
        
        status_message = status_messages.get(new_status, f'Status changed to {new_status}')
        status_color = status_colors.get(new_status, '#6b7280')
        
        items_html = ''
        for item in order.items.all():
            items_html += f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 12px; text-align: left;">{item.product_name}</td>
                <td style="padding: 12px; text-align: center;">{item.quantity}</td>
                <td style="padding: 12px; text-align: right;">Rs. {item.unit_price}</td>
                <td style="padding: 12px; text-align: right;">Rs. {item.subtotal}</td>
            </tr>
            """
        
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {status_color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; }}
                .status-box {{ background-color: white; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid {status_color}; }}
                .order-details {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .order-details h3 {{ margin-top: 0; color: {status_color}; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background-color: #f3f4f6; padding: 12px; text-align: left; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .status-badge {{ display: inline-block; background-color: {status_color}; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Order Status Update</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Order #{order.order_number}</p>
                </div>
                
                <div class="content">
                    <p>Hi <strong>{order.full_name}</strong>,</p>
                    
                    <div class="status-box">
                        <h2 style="margin-top: 0; color: {status_color};">{status_message}</h2>
                        <p style="margin: 10px 0; font-size: 16px;">
                            <span class="status-badge">{new_status.upper()}</span>
                        </p>
                        <p style="margin: 10px 0; color: #6b7280; font-size: 14px;">
                            Updated on {order.updated_at.strftime('%d %B %Y at %I:%M %p')}
                        </p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Order Information</h3>
                        <p><strong>Order Number:</strong> #{order.order_number}</p>
                        <p><strong>Order Date:</strong> {order.created_at.strftime('%d %B %Y, %I:%M %p')}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Items Ordered</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Qty</th>
                                    <th>Price</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="order-details">
                        <h3>Delivery Details</h3>
                        <p><strong>Delivery Type:</strong> {order.get_delivery_type_display()}</p>
                        <p><strong>Name:</strong> {order.full_name}</p>
                        <p><strong>Phone:</strong> {order.phone}</p>
                        <p><strong>Address:</strong> {order.address}, {order.city}</p>
                    </div>
                    
                    <div class="order-details">
                        <h3>Payment Summary</h3>
                        <table style="border: none;">
                            <tr style="border: none;">
                                <td style="padding: 8px; text-align: left; border: none;"><strong>Subtotal:</strong></td>
                                <td style="padding: 8px; text-align: right; border: none;">Rs. {order.subtotal}</td>
                            </tr>
                            <tr style="border: none;">
                                <td style="padding: 8px; text-align: left; border: none;"><strong>Delivery Charge:</strong></td>
                                <td style="padding: 8px; text-align: right; border: none;">Rs. {order.delivery_charge}</td>
                            </tr>
                            <tr style="border-top: 2px solid {status_color};">
                                <td style="padding: 12px; text-align: left; font-weight: bold; font-size: 16px;"><strong>Total Amount:</strong></td>
                                <td style="padding: 12px; text-align: right; font-weight: bold; font-size: 16px; color: {status_color};">Rs. {order.total}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p>You can track your order status anytime by visiting your account on our website.</p>
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                </div>
                
                <div class="footer">
                    <p>Thank you for shopping with us!</p>
                    <p>© Aarambha Foundation. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        settings = SiteSettings.get()
        from_email = f'Aarambha Foundation <{settings.email or "suraj20001123@gmail.com"}>'
        
        send_mail(
            subject=f'Order Status Update - #{order.order_number}',
            message=f'Your order #{order.order_number} status has been updated to {new_status}.',
            from_email=from_email,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f'Order status update email sent to {order.email}: {old_status} -> {new_status}')
        
    except Exception as e:
        print(f'Error sending order status update email: {e}')
        import traceback
        traceback.print_exc()
