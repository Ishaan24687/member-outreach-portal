from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/members/", include("apps.members.urls")),
    path("api/predictions/", include("apps.predictions.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    # template views
    path("", TemplateView.as_view(template_name="dashboard.html"), name="dashboard"),
    path("members/", TemplateView.as_view(template_name="member_list.html"), name="member-list"),
]

admin.site.site_header = "Member Outreach Portal"
admin.site.site_title = "Outreach Admin"
admin.site.index_title = "Outreach Management"
