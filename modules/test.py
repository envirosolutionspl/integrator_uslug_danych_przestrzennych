from dataclasses import dataclass

@dataclass
class _LayerDefinition:
    uri: str
    display_name: str
    provider: str
    layer_type: str
    layer_id: str
    title: str