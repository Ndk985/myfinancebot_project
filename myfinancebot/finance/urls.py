from django.urls import path
from .views import ExpenseView

urlpatterns = [
    path('expense/', ExpenseView.as_view(), name='expense'),
]
