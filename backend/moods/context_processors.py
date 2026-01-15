from django.conf import settings

from moods.providers import MockProvider, provider_from_settings


def settings_flags(request):
    demo_mode = isinstance(provider_from_settings(), MockProvider)
    return {
        "demo_mode": demo_mode,
        "enable_threejs": settings.ENABLE_THREEJS,
    }
