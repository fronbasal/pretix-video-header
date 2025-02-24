from base64 import b64encode
from hashlib import sha384

from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.urls import resolve, reverse
from urllib3.util import parse_url

from pretix.base.middleware import _parse_csp, _merge_csp, _render_csp
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import html_footer, process_response

def _integrity(content):
    # generate a sha256 hash of the content for the integrity attribute of the script or style tag
    return "sha384-" + b64encode(sha384(content.encode()).digest()).decode()

@receiver(nav_event_settings, dispatch_uid="video_nav_event_settings")
def navbar_event_settings(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            "label": _("Video Header"),
            "url": reverse(
                "plugins:pretix_video:settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.namespace == "plugins:pretix_video"
                      and url.url_name.startswith("settings"),
        }
    ]


@receiver(html_footer, dispatch_uid="video_global_html_page_header")
def global_html_page_header(sender, request, **kwargs):
    video_url = sender.settings.get("video_url")
    if not video_url:
        return
    # Replace the <i> element with a <v> element using javascript
    script_content = f"""
    (function() {{
        const i = document.querySelector('.page-header.pager-header-with-logo.logo-large img');
        if (!i) {{ return; }}
        i.parentElement.style.cssText = 'display: block';
        const v = document.createElement('video');
        v.src = '{video_url}';
        v.setAttribute('playsinline', '');
        v.autoplay = true;
        v.muted = true;
        v.loop = true;
        v.className = 'event-logo';
        v.style.cssText = 'width: 100%; display: block; object-fit: contain;';
        i.replaceWith(v);
    }})();
    """.strip()
    return f"<script integrity=\"{_integrity(script_content)}\">{script_content}</script>"

@receiver(process_response, dispatch_uid="video_process_response")
def process_response_video_csp(sender, request, response, **kwargs):
    video_url = sender.settings.get("video_url")
    video_url = parse_url(video_url)
    if not video_url:
        return response
    if "Content-Security-Policy" in response:
        headers = _parse_csp(response["Content-Security-Policy"])
    else:
        headers = {}
    _merge_csp(
        headers,
        {
            "script-src": [
                "'self'",
                "'unsafe-inline'",
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",
            ],
            "media-src": [
                "'self'",
                "%s://%s" % (video_url.scheme, video_url.netloc),
            ],
        },
    )

    if headers:
        response["Content-Security-Policy"] = _render_csp(headers)
    return response
