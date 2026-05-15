"""Pydantic message contracts shared across agents.

Schemas are the only types crossing agent boundaries. Agents never import
each other; they exchange instances of the models defined here.
"""
