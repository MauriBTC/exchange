from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login_user', views.login_user, name="login"),
    path('logout_user', views.logout_user, name='logout'),
    path('register_user', views.register_user, name='register_user'),
    path('buy_order', views.buy_order, name='buy_order'),
    path('sell_order', views.sell_order, name='sell_order'),
    path('active_orders', views.get_all_active_orders, name='active_orders'),
    path('profit_loss', views.get_user_total_profit_loss, name='profit_loss'),
]