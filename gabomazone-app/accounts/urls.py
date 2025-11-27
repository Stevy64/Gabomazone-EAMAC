from django.urls import path
from . import views
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
    path('dashboard/', views.dashboard_customer, name='dashboard_customer'),
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
    path('download-list/', views.download_list, name="download-list"),
    path('download_file/<int:order_id>/<str:filename>/',
         views.download_file, name="download-file"),


]
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
