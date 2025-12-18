from django.urls import path
from . import views
from . import admin_notifications
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from .forms import CaptchaPasswordResetForm

app_name = 'accounts'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('mes-commandes/', views.dashboard_customer, name='dashboard_customer'),
    path('order-tracking/', views.order_tracking, name="order_tracking"),
    path('change-password/', views.change_password, name="change_password"),
    path('account_details/', views.dashboard_account_details, name="account_details"),
    path('orders-ajax/', views.MyOrdersJsonListView.as_view(),
         name='orders-ajax'),
    path('dashboard/order/<int:order_id>/', views.order, name='order'),


    path('password-reset/', auth_views.PasswordResetView.as_view(form_class=CaptchaPasswordResetForm, template_name='accounts/auth/password_reset.html', email_template_name='accounts/auth/password_reset_email.html',
                                                                 from_email=settings.EMAIL_SENDGRID,
                                                                 html_email_template_name='accounts/auth/password_reset_email.html',
                                                                 subject_template_name='accounts/auth/password_reset_subject.txt',
                                                                 success_url=reverse_lazy('accounts:password_reset_done')), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/auth/password_reset_done.html'), name='password_reset_done'),
    path('password-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/auth/password_reset_confirm.html',
                                                                                           post_reset_login=True, success_url=reverse_lazy('accounts:password_reset_complete')),   name='password_reset_confirm'),
    path('password-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/auth/password_reset_complete.html'), name='password_reset_complete'),
    path('sell-product/', views.sell_product, name="sell-product"),
    path('peer-orders/', views.peer_orders_list, name="peer-orders-list"),
    path('peer-orders/accept/<int:notification_id>/', views.accept_peer_order, name="accept-peer-order"),
    path('peer-orders/reject/<int:notification_id>/', views.reject_peer_order, name="reject-peer-order"),
    path('peer-orders/mark-read/<int:notification_id>/', views.mark_notification_read, name="mark-notification-read"),
    path('peer-product/<str:slug>/', views.peer_product_details, name="peer-product-details"),
    path('edit-peer-product/<int:product_id>/', views.edit_peer_product, name="edit-peer-product"),
    path('delete-peer-product/<int:product_id>/', views.delete_peer_product, name="delete-peer-product"),
    path('my-published-products/', views.my_published_products, name="my-published-products"),
    path('my-messages/', views.my_messages, name="my-messages"),
    path('product-conversations/<int:product_id>/', views.get_product_conversations, name="get-product-conversations"),
    path('send-product-message/<int:product_id>/', views.send_product_message, name="send-product-message"),
    path('mark-conversation-read/<int:conversation_id>/', views.mark_conversation_messages_read, name="mark-conversation-read"),
path('delete-product-message/<int:message_id>/', views.delete_product_message, name="delete-product-message"),
    path('archive-conversation/<int:conversation_id>/', views.archive_conversation, name="archive-conversation"),
    path('unarchive-conversation/<int:conversation_id>/', views.unarchive_conversation, name="unarchive-conversation"),
    path('download_file/<int:order_id>/<str:filename>/',
         views.download_file, name="download-file"),
    
    # URLs pour les notifications admin
    path('admin/notifications/', admin_notifications.get_admin_notifications, name="admin-notifications"),
    path('admin/notifications/<int:notification_id>/read/', admin_notifications.mark_notification_read, name="admin-notification-read"),
    path('admin/notifications/<int:notification_id>/resolve/', admin_notifications.mark_notification_resolved, name="admin-notification-resolve"),
    path('admin/notifications/read-all/', admin_notifications.mark_all_notifications_read, name="admin-notifications-read-all"),


]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
