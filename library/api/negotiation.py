"""Always answer JSON, whatever the Accept header asks for (DRF would answer 406)."""

from rest_framework.negotiation import DefaultContentNegotiation


class JsonOnly(DefaultContentNegotiation):
    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type
