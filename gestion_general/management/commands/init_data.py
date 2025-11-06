# gestion_general/management/commands/init_data.py

"""
Comando para pre-cargar datos iniciales en la base de datos PostgreSQL remota.
Crea usuarios de prueba y datos mock para desarrollo y testing.

Uso:
    python manage.py init_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from gestion_general.models import Usuario, Insumo, Pedido, PedidoInsumo, Cliente
import random
from decimal import Decimal
from typing import List

fake = Faker('es_ES')  # Spanish locale for more realistic data


class Command(BaseCommand):
    help = 'Crea usuarios de prueba y carga datos mock iniciales en la base de datos.'

    def handle(self, *args, **options) -> None:
        """Ejecuta la carga de usuarios de prueba y datos mock."""
        self.stdout.write('Iniciando carga de datos iniciales...')
        
        with transaction.atomic():
            # Crear usuarios de prueba
            self._create_test_users()
            
            # Cargar datos mock
            self._load_mock_data()
        
        self.stdout.write(self.style.SUCCESS('✅ Datos iniciales cargados exitosamente.'))

    def _create_test_users(self) -> None:
        """Crea los usuarios de prueba según especificación del README."""
        # Usuario Administrador
        admin, created = Usuario.objects.get_or_create(
            username='admin@taller.com',
            defaults={
                'email': 'admin@taller.com',
                'rol': 'admin',
                'is_superuser': True,
                'is_staff': True,
                'first_name': 'Admin',
                'last_name': 'Sistema'
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('✅ Usuario Administrador creado: admin@taller.com'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Usuario Administrador ya existe: admin@taller.com'))
        
        # Usuario Encargado (Empleado)
        encargado, created = Usuario.objects.get_or_create(
            username='encargado@taller.com',
            defaults={
                'email': 'encargado@taller.com',
                'rol': 'emp',
                'is_staff': True,
                'first_name': 'Encargado',
                'last_name': 'Taller'
            }
        )
        if created:
            encargado.set_password('encargado123')
            encargado.save()
            self.stdout.write(self.style.SUCCESS('✅ Usuario Encargado creado: encargado@taller.com'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Usuario Encargado ya existe: encargado@taller.com'))

    def _load_mock_data(self) -> None:
        """Carga datos mock de insumos, clientes y pedidos."""
        # Obtener usuarios creados
        admin = Usuario.objects.get(username='admin@taller.com')
        encargado = Usuario.objects.get(username='encargado@taller.com')
        
        # Crear clientes
        clients = self._create_clients()
        self.stdout.write(self.style.SUCCESS(f'✅ {len(clients)} clientes creados.'))
        
        # Crear insumos
        insumos = self._create_insumos()
        self.stdout.write(self.style.SUCCESS(f'✅ {len(insumos)} insumos creados.'))
        
        # Crear pedidos
        pedidos_count = self._create_pedidos(clients, insumos, admin, encargado)
        self.stdout.write(self.style.SUCCESS(f'✅ {pedidos_count} pedidos creados.'))

    def _create_clients(self) -> List[Cliente]:
        """Crea clientes de prueba con datos realistas."""
        clients = []
        for _ in range(15):
            client_name = fake.name()
            client_email = fake.email()
            client, created = Cliente.objects.get_or_create(
                email=client_email,
                defaults={
                    'nombre': client_name,
                    'telefono': fake.phone_number()
                }
            )
            if created:
                clients.append(client)
        return clients

    def _create_insumos(self) -> List[Insumo]:
        """Crea insumos de bordado con datos realistas."""
        insumos = []
        
        embroidery_supplies = [
            'Fiselina 90gr', 'Fiselina 120gr', 'Fiselina 180gr',
            'Hilo Algodón Negro', 'Hilo Algodón Blanco', 'Hilo Algodón Rojo', 
            'Hilo Algodón Azul', 'Hilo Algodón Verde',
            'Hilo Poliéster Negro', 'Hilo Poliéster Blanco', 'Hilo Poliéster Rojo', 
            'Hilo Poliéster Azul', 'Hilo Poliéster Verde',
            'Hilo Metálico', 'Hilo Rayón',
            'Lino Natural 180g', 'Lino Natural 200g', 'Lino Blanco',
            'Tela de Algodón', 'Tela de Poliéster', 'Tela de Lino',
            'Bobina de Algodón', 'Bobina de Poliéster', 'Bobina Metálica',
            'Estabilizador Cut Away', 'Estabilizador Tear Away', 'Estabilizador Wash Away',
            'Aguja Bordado #75', 'Aguja Bordado #90', 'Aguja Bordado #100'
        ]
        
        # Crear un insumo para cada suministro único
        for i, supply_name in enumerate(embroidery_supplies):
            sku = f'SKU{str(i+1).zfill(4)}'
            insumo, created = Insumo.objects.get_or_create(
                sku=sku,
                defaults={
                    'nombre': supply_name,
                    'descripcion': f'Insumo profesional para bordado: {supply_name}',
                    'unidad': 'unidad',
                    'stock_actual': random.randint(0, 100),
                    'stock_minimo': random.randint(5, 15),
                    'precio_unitario': Decimal(str(random.uniform(5.0, 500.0))).quantize(Decimal('0.01'))
                }
            )
            if created:
                insumos.append(insumo)
        
        return insumos

    def _create_pedidos(
        self, 
        clients: List[Cliente], 
        insumos: List[Insumo], 
        admin: Usuario, 
        encargado: Usuario
    ) -> int:
        """Crea pedidos de ejemplo con estados aleatorios."""
        if not clients or not insumos:
            return 0
        
        pedidos_created = 0
        for _ in range(25):
            # Selección ponderada de clientes: algunos tienen más pedidos
            client_weights = [random.randint(1, 10) for _ in clients]
            selected_client = random.choices(clients, weights=client_weights)[0]
            
            order = Pedido.objects.create(
                cliente=selected_client,
                estado=random.choice([x[0] for x in Pedido.ESTADOS]),
                creado_por=random.choice([admin, encargado]),
                total=Decimal('0')
            )
            
            # Agregar 1-5 items a cada pedido
            total = Decimal('0')
            for _ in range(random.randint(1, 5)):
                insumo = random.choice(insumos)
                quantity = random.randint(1, 10)
                
                PedidoInsumo.objects.create(
                    pedido=order,
                    insumo=insumo,
                    cantidad=quantity
                )
                
                if insumo.precio_unitario:
                    total += insumo.precio_unitario * quantity
            
            order.total = total
            order.save()
            pedidos_created += 1
        
        return pedidos_created