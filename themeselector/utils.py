"""Utility functions for the ThemeSelector plugin."""


def get_current_visibility(root) -> set:
    """Return a set of layer IDs currently visible in the layer tree.

    Args:
        root: QgsLayerTreeGroup (usually project.layerTreeRoot())

    Returns:
        Set of visible layer ID strings.
    """
    if not root:
        return set()

    # findLayers() returns all QgsLayerTreeLayer nodes in the tree
    return {node.layerId() for node in root.findLayers() if node.isVisible()}


def theme_matches_map(theme_record, current_vis_set: set) -> bool:
    """Check if the theme's visibility state matches the current map state.

    This avoids calling C++ methods that trigger Qt enums, ensuring stability.
    """
    if not theme_record:
        return False

    try:
        theme_vis_ids = set()
        for lr in theme_record.layerRecords():
            # Get layer ID safely for cross-version compatibility
            layer_id_attr = getattr(lr, 'layerId', None)
            lid = (
                layer_id_attr()
                if callable(layer_id_attr)
                else layer_id_attr
            )
            if not lid:
                layer_obj = (
                    lr.layer()
                    if callable(getattr(lr, 'layer', None))
                    else getattr(lr, 'layer', None)
                )
                if layer_obj:
                    lid = layer_obj.id()

            if lid:
                is_vis_attr = getattr(lr, 'isVisible', False)
                is_vis = (
                    is_vis_attr()
                    if callable(is_vis_attr)
                    else bool(is_vis_attr)
                )
                if is_vis:
                    theme_vis_ids.add(lid)

        return theme_vis_ids == current_vis_set

    except (AttributeError, RuntimeError):
        return False
