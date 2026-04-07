# -*- coding: utf-8 -*-
"""Utility functions for the ThemeSelector plugin."""

from qgis.core import QgsMapThemeCollection

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
            lid = getattr(lr, 'layerId', lambda: None)() if callable(getattr(lr, 'layerId', None)) else getattr(lr, 'layerId', None)
            if not lid and lr.layer():
                lid = lr.layer().id()
                
            if lid:
                is_vis = lr.isVisible if isinstance(lr.isVisible, bool) else lr.isVisible()
                if is_vis:
                    theme_vis_ids.add(lid)
                    
        return theme_vis_ids == current_vis_set
        
    except (AttributeError, RuntimeError):
        return False
