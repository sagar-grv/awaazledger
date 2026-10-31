from app.channels.base_adapter import ChannelAdapter
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.channels.meta_cloud_whatsapp_adapter import MetaCloudWhatsAppAdapter
from app.channels.simulator_adapter import SimulatorAdapter
from app.channels.channel_router import get_adapter

__all__ = [
    "ChannelAdapter",
    "EvolutionWhatsAppAdapter",
    "MetaCloudWhatsAppAdapter",
    "SimulatorAdapter",
    "get_adapter",
]
