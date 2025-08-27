# Import all perturbations to ensure they are registered
from . import shapes, noise, warp, texture
from .base import PERTURBATION_REGISTRY, register

__all__ = ["PERTURBATION_REGISTRY", "register"]