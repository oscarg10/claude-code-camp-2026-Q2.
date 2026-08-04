class RunDSL:
    """The object `block` is called with inside `run()`. Exposes only
    `tool`, keeping the DSL surface intentionally small."""

    def __init__(self, registry):
        self.registry = registry

    def tool(self, name, description, parameters=None, block=None):
        return self.registry.tool(name, description=description, parameters=parameters, block=block)
