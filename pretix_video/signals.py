import secrets
from base64 import b64encode

from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy
from urllib3.util import parse_url

from pretix.base.middleware import _parse_csp, _merge_csp, _render_csp
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import html_footer, process_response



@receiver(nav_event_settings, dispatch_uid="video_nav_event_settings")
def navbar_event_settings(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            "label": gettext_lazy("Video Header"),
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

    script_content = f"""(function() {{
        const i = document.querySelector('.page-header.pager-header-with-logo.logo-large img.event-logo');
        if (!i) return;
        const r = i.naturalHeight / i.naturalWidth * 100,
        p = i.parentElement;
        p.style.cssText = 'display:block;position:relative;padding-bottom:' + r + '%;width:100%';
        const v = document.createElement('video');
        v.poster = i.src;
        v.src = '{video_url}';
        v.setAttribute('playsinline', '');
        v.autoplay = !0;
        v.muted = !0;
        v.loop = !0;
        v.className = 'event-logo';
        v.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;object-fit:contain';
        i.replaceWith(v);
    }})();"""
    nonce = b64encode(secrets.token_bytes(16)).decode("utf-8")
    request._video_nonce = nonce
    return f'<script nonce="{nonce}">{script_content}</script>'


@receiver(process_response, dispatch_uid="video_process_response")
def process_response_video_csp(sender, request, response, **kwargs):
    video_url = sender.settings.get("video_url")
    if not video_url:
        return response

    # Get stored hash from request
    nonce = getattr(request, "_video_nonce", None)

    # Parse existing CSP
    headers = {}
    if "Content-Security-Policy" in response:
        headers = _parse_csp(response.get("Content-Security-Policy", ""))

    # Update media-src with video domain
    video_netloc = parse_url(video_url).netloc

    _merge_csp(headers, {"media-src": [video_netloc]})

    # Add script hash to CSP if exists
    if nonce:
        _merge_csp(headers, {"script-src": [f"'nonce-{nonce}'"]})

    # Apply updated CSP
    if headers:
        response["Content-Security-Policy"] = _render_csp(headers)

    return response
