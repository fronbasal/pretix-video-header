from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_video"
    verbose_name = "Pretix Video Header"

    class PretixPluginMeta:
        name = gettext_lazy("Pretix Video Header")
        author = "Daniel Malik"
        description = gettext_lazy("Replace the image / gif with a HTML5 video element")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA
