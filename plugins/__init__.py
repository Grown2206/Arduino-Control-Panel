# -*- coding: utf-8 -*-
"""
plugins/__init__.py
Plugin-System für das Arduino Control Panel
"""
from plugins.plugin_api import (
    PluginInterface,
    PluginMetadata,
    PluginType,
    PluginPriority,
    PluginCapability,
    ApplicationContext,
    PluginHook
)
from plugins.plugin_manager import PluginManager

__all__ = [
    'PluginInterface',
    'PluginMetadata',
    'PluginType',
    'PluginPriority',
    'PluginCapability',
    'ApplicationContext',
    'PluginHook',
    'PluginManager'
]

__version__ = '1.0.0'
