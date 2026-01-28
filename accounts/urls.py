from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from .views import welcome, login_view, logout_view, register_view, profile_view
from .forms import SMTPPasswordResetForm

app_name = 'accounts'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('', welcome, name='welcome'),

    # Password reset flow
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             form_class=SMTPPasswordResetForm,
             success_url=reverse_lazy('accounts:password_reset_done')
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:login')
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
        path('profile/',
            # simple profile view for users
            # implemented in accounts.views
            # replaced placeholder with actual view
            # and protected via @login_required
            # (view imported from .views)
            # see accounts.views.profile_view
            # uses ProfileForm
            #
            # import here to avoid circular import at module load
            profile_view,
            name='profile'),

    # Password change (for logged in users)
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change_form.html',
             success_url=reverse_lazy('accounts:password_change_done')
         ),
         name='password_change'),

    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html'
         ),
         name='password_change_done'),
]