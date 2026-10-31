"""Routing factory for channel adapters."""

from app.channels.base_adapter import ChannelAdapter
from app.channels.simulator_adapter import SimulatorAdapter
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.channels.meta_cloud_whatsapp_adapter import MetaCloudWhatsAppAdapter


def get_adapter(channel: str) -> ChannelAdapter:
    """Returns the registered ChannelAdapter for the given channel name."""
    channel_norm = (channel or "SIMULATOR").upper().strip()

    if channel_norm in ["WHATSAPP", "WHATSAPP_EVOLUTION", "EVOLUTION"]:
        return EvolutionWhatsAppAdapter()
    elif channel_norm in ["WHATSAPP_META", "META"]:
        return MetaCloudWhatsAppAdapter()
    else:
        return SimulatorAdapter()
