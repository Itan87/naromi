"""
Unit tests for the Insumo model.

This module contains tests for:
- Stock critical status detection
- Stock state calculations
- Critical insumos retrieval
- Stock metrics calculation
- SKU uniqueness validation
"""
from typing import TYPE_CHECKING

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from gestion_general.models import Insumo

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


@pytest.mark.django_db
class TestInsumoModel:
    """Test cases for the Insumo model."""

    def test_insumo_creation_basic(self) -> None:
        """Test basic Insumo creation with required fields."""
        insumo = Insumo.objects.create(
            sku="TEST-001",
            nombre="Test Insumo",
            stock_actual=10,
            stock_minimo=5,
        )
        
        assert insumo.sku == "TEST-001"
        assert insumo.nombre == "Test Insumo"
        assert insumo.stock_actual == 10
        assert insumo.stock_minimo == 5
        assert insumo.unidad == "unidad"  # Default value

    def test_insumo_str_representation(self) -> None:
        """Test the string representation of Insumo."""
        insumo = Insumo.objects.create(
            sku="TEST-002",
            nombre="Test Insumo 2",
        )
        
        expected_str = f"{insumo.sku} — {insumo.nombre}"
        assert str(insumo) == expected_str

    def test_sku_uniqueness(self) -> None:
        """Test that SKU must be unique."""
        Insumo.objects.create(
            sku="DUPLICATE-SKU",
            nombre="First Insumo",
        )
        
        with pytest.raises(IntegrityError):
            Insumo.objects.create(
                sku="DUPLICATE-SKU",
                nombre="Second Insumo",
            )

    def test_es_critico_when_stock_below_minimo(self) -> None:
        """Test es_critico returns True when stock is below minimum."""
        insumo = Insumo.objects.create(
            sku="CRITICAL-001",
            nombre="Critical Insumo",
            stock_actual=3,
            stock_minimo=5,
        )
        
        assert insumo.es_critico() is True

    def test_es_critico_when_stock_equal_minimo(self) -> None:
        """Test es_critico returns True when stock equals minimum."""
        insumo = Insumo.objects.create(
            sku="CRITICAL-002",
            nombre="Critical Insumo 2",
            stock_actual=5,
            stock_minimo=5,
        )
        
        assert insumo.es_critico() is True

    def test_es_critico_when_stock_above_minimo(self) -> None:
        """Test es_critico returns False when stock is above minimum."""
        insumo = Insumo.objects.create(
            sku="NORMAL-001",
            nombre="Normal Insumo",
            stock_actual=10,
            stock_minimo=5,
        )
        
        assert insumo.es_critico() is False

    def test_estado_stock_critico(self) -> None:
        """Test estado_stock returns 'critico' when stock is 50% or less of minimum."""
        # Stock at exactly 50% of minimum
        insumo = Insumo.objects.create(
            sku="CRITICO-001",
            nombre="Critical Stock",
            stock_actual=2,
            stock_minimo=5,
        )
        
        assert insumo.estado_stock() == "critico"
        
        # Stock below 50% of minimum
        insumo2 = Insumo.objects.create(
            sku="CRITICO-002",
            nombre="Critical Stock 2",
            stock_actual=1,
            stock_minimo=5,
        )
        
        assert insumo2.estado_stock() == "critico"

    def test_estado_stock_bajo(self) -> None:
        """Test estado_stock returns 'bajo' when stock is between 50% and 100% of minimum."""
        insumo = Insumo.objects.create(
            sku="BAJO-001",
            nombre="Low Stock",
            stock_actual=4,
            stock_minimo=5,
        )
        
        assert insumo.estado_stock() == "bajo"
        
        # Stock at exactly minimum (not below 50%, so should be "bajo")
        insumo2 = Insumo.objects.create(
            sku="BAJO-002",
            nombre="Low Stock 2",
            stock_actual=5,
            stock_minimo=5,
        )
        
        assert insumo2.estado_stock() == "bajo"

    def test_estado_stock_normal(self) -> None:
        """Test estado_stock returns 'normal' when stock is above minimum."""
        insumo = Insumo.objects.create(
            sku="NORMAL-001",
            nombre="Normal Stock",
            stock_actual=10,
            stock_minimo=5,
        )
        
        assert insumo.estado_stock() == "normal"
        
        # Stock well above minimum
        insumo2 = Insumo.objects.create(
            sku="NORMAL-002",
            nombre="Normal Stock 2",
            stock_actual=100,
            stock_minimo=5,
        )
        
        assert insumo2.estado_stock() == "normal"

    def test_obtener_insumos_criticos(self) -> None:
        """Test obtener_insumos_criticos class method returns only critical insumos."""
        # Create critical insumos
        Insumo.objects.create(sku="CRIT-001", nombre="Critical 1", stock_actual=2, stock_minimo=5)
        Insumo.objects.create(sku="CRIT-002", nombre="Critical 2", stock_actual=5, stock_minimo=5)
        
        # Create normal insumos
        Insumo.objects.create(sku="NORM-001", nombre="Normal 1", stock_actual=10, stock_minimo=5)
        Insumo.objects.create(sku="NORM-002", nombre="Normal 2", stock_actual=20, stock_minimo=5)
        
        criticos = Insumo.obtener_insumos_criticos()
        
        assert criticos.count() == 2
        assert all(insumo.es_critico() for insumo in criticos)

    def test_obtener_insumos_criticos_empty(self) -> None:
        """Test obtener_insumos_criticos returns empty queryset when no critical insumos."""
        Insumo.objects.create(sku="NORM-001", nombre="Normal 1", stock_actual=10, stock_minimo=5)
        Insumo.objects.create(sku="NORM-002", nombre="Normal 2", stock_actual=20, stock_minimo=5)
        
        criticos = Insumo.obtener_insumos_criticos()
        
        assert criticos.count() == 0

    def test_obtener_metricas_stock(self) -> None:
        """Test obtener_metricas_stock calculates metrics correctly."""
        # Create mix of critical and normal insumos
        Insumo.objects.create(sku="CRIT-001", nombre="Critical 1", stock_actual=2, stock_minimo=5)
        Insumo.objects.create(sku="CRIT-002", nombre="Critical 2", stock_actual=5, stock_minimo=5)
        Insumo.objects.create(sku="NORM-001", nombre="Normal 1", stock_actual=10, stock_minimo=5)
        Insumo.objects.create(sku="NORM-002", nombre="Normal 2", stock_actual=20, stock_minimo=5)
        
        metricas = Insumo.obtener_metricas_stock()
        
        assert metricas["total"] == 4
        assert metricas["criticos"] == 2
        assert metricas["porcentaje_critico"] == 50.0

    def test_obtener_metricas_stock_empty(self) -> None:
        """Test obtener_metricas_stock handles empty database correctly."""
        metricas = Insumo.obtener_metricas_stock()
        
        assert metricas["total"] == 0
        assert metricas["criticos"] == 0
        assert metricas["porcentaje_critico"] == 0

    def test_obtener_metricas_stock_all_normal(self) -> None:
        """Test obtener_metricas_stock when all insumos are normal."""
        Insumo.objects.create(sku="NORM-001", nombre="Normal 1", stock_actual=10, stock_minimo=5)
        Insumo.objects.create(sku="NORM-002", nombre="Normal 2", stock_actual=20, stock_minimo=5)
        
        metricas = Insumo.obtener_metricas_stock()
        
        assert metricas["total"] == 2
        assert metricas["criticos"] == 0
        assert metricas["porcentaje_critico"] == 0.0

    def test_insumo_precio_unitario_nullable(self) -> None:
        """Test that precio_unitario can be null or blank."""
        insumo_sin_precio = Insumo.objects.create(
            sku="NO-PRICE-001",
            nombre="No Price Insumo",
        )
        
        assert insumo_sin_precio.precio_unitario is None
        
        insumo_con_precio = Insumo.objects.create(
            sku="PRICE-001",
            nombre="Priced Insumo",
            precio_unitario=100.50,
        )
        
        assert insumo_con_precio.precio_unitario == 100.50

    def test_insumo_descripcion_blank(self) -> None:
        """Test that descripcion can be blank."""
        insumo_sin_desc = Insumo.objects.create(
            sku="NO-DESC-001",
            nombre="No Description Insumo",
        )
        
        assert insumo_sin_desc.descripcion == ""
        
        insumo_con_desc = Insumo.objects.create(
            sku="DESC-001",
            nombre="Description Insumo",
            descripcion="Esta es una descripción",
        )
        
        assert insumo_con_desc.descripcion == "Esta es una descripción"

