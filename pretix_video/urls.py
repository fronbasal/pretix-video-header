from django.urls import re_path

from .views import SettingsView

urlpatterns = [
    re_path(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/settings/video/$",
        SettingsView.as_view(),
        name="settings",
    ),
]
