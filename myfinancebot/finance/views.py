from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Category, Expense
import json
from datetime import datetime
from django.db.models import Sum

@method_decorator(csrf_exempt, name='dispatch')
class ExpenseView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        category, created = Category.objects.get_or_create(name=data['category'])
        expense = Expense.objects.create(category=category, amount=data['amount'])
        return JsonResponse({'status': 'success', 'expense_id': expense.id})

    def get(self, request, *args, **kwargs):
        month = datetime.now().month
        expenses = Expense.objects.filter(date_added__month=month)
        total = sum(expense.amount for expense in expenses)
        # Добавляем информацию о расходах по категориям
        category_expenses = expenses.values('category__name').annotate(total_amount=Sum('amount'))
        category_expenses_dict = {item['category__name']: item['total_amount'] for item in category_expenses}
        
        return JsonResponse({
            'total_expenses': total,
            'category_expenses': category_expenses_dict
        })

