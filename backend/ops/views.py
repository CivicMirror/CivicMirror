from django.contrib import admin
from django.template.response import TemplateResponse


def commands_view(request):
    context = admin.site.each_context(request)
    context['title'] = 'Cloud Run Commands'
    return TemplateResponse(request, 'admin/commands.html', context)
