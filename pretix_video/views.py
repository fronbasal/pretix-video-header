from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pretix.base.forms import SettingsForm
from pretix.base.models import Event
from pretix.control.views.event import EventSettingsViewMixin, EventSettingsFormView


class VideoSettingsForm(SettingsForm):
    video_url = forms.URLField(
        label=_("Video URL"),
        required=True,
        help_text=_(
            "The URL of the video that should be displayed in the header. This currently only supports direct links to video files supported by the client's browser."
        ),
    )

    # TODO: hls.js, autoplay, loop, mute, etc...


class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = VideoSettingsForm
    template_name = "pretix_video/settings.html"
    permission = "can_change_event_settings"

    def get_success_url(self):
        return reverse(
            "plugins:pretix_video:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )
