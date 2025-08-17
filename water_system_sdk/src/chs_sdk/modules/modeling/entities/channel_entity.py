from chs_sdk.modeling.base_physical_entity import BasePhysicalEntity

class ChannelEntity(BasePhysicalEntity):
    """
    Physical entity representing a river or canal channel.

    This entity acts as a container for various fidelity models that simulate
    flow through the channel.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
