from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Dashboard
# @login_required
# class DashboardView(View):
#     def get(self, request):
#         return render(request, "dashboard.html")

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

class Settings(LoginRequiredMixin, View):
    template_name = "settings.html"

    def __init__(self, *args):
        super(Settings, self).__init__(*args)

    def get(self, request):
        return render(request, self.template_name)


