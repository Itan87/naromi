"""
COMMANDS TO APPLY CHANGES TO MOCK DATA:

1. Activate virtual environment (if not already active):
   .\venv\Scripts\Activate.ps1

2. If you modified the models (added/removed fields), create migrations:
   python manage.py makemigrations

3. Apply any pending migrations:
   python manage.py migrate

4. Load/Reload mock data:
   python manage.py load_mock_data

5. Start development server to test:
   python manage.py runserver

Note: The load_mock_data command uses get_or_create(), so it won't create duplicates
if you run it multiple times. It will only create new records if they don't exist.

IMPORTANT: If you changed model names (like Producto -> Insumo) or want to completely
refresh the data, you need to clear the old data first:

1. Clear all data from database:
python manage.py shell

from gestion_general.models import *
PedidoInsumo.objects.all().delete()
Insumo.objects.all().delete()
Pedido.objects.all().delete()
Cliente.objects.all().delete()
Usuario.objects.filter(username__in=['admin@taller.com', 'encargado@taller.com']).delete()
exit()

2. Then reload mock data:
   python manage.py load_mock_data

3. Setup permissions for the recreated users:
   python manage.py setup_permissions
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from gestion_general.models import Usuario, Insumo, Pedido, PedidoInsumo, Cliente
import random
from decimal import Decimal

fake = Faker('es_ES')  # Spanish locale for more realistic data

class Command(BaseCommand):
    help = 'Loads mock data into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading mock data...')
        
        with transaction.atomic():
            # Create admin and encargado users if they don't exist
            admin, created = Usuario.objects.get_or_create(
                username='admin@taller.com',
                defaults={
                    'email': 'admin@taller.com',
                    'rol': 'admin',
                    'is_superuser': True,
                    'is_staff': True,
                    'first_name': 'Maria',
                    'last_name': 'Serrano (Admin)'
                }
            )
            if created:
                admin.set_password('admin123')
                admin.save()
            
            encargado, created = Usuario.objects.get_or_create(
                username='encargado@taller.com',
                defaults={
                    'email': 'encargado@taller.com',
                    'rol': 'emp',
                    'is_staff': True,
                    'first_name': 'Karen',
                    'last_name': 'Tejedo (Encargada)'
                }
            )
            if created:
                encargado.set_password('encargado123')
                encargado.save()
            
            # Create clients with realistic Spanish names
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
                clients.append(client)
            
            # Create insumos with realistic embroidery supply names
            insumos = []
            colors = ['Rojo', 'Azul', 'Verde', 'Negro', 'Blanco', 'Amarillo', 'Rosa', 'Morado', 'Naranja', 'Gris']
            
            embroidery_supplies = [
                'Fiselina 90gr', 'Fiselina 120gr', 'Fiselina 180gr',
                'Hilo Poliéster', 'Hilo Algodón', 'Hilo Metálico', 'Hilo Rayón',
                'Lino Natural 180g', 'Lino Natural 200g', 'Lino Blanco',
                'Tela de Algodón', 'Tela de Poliéster', 'Tela de Lino',
                'Bobina de Algodón', 'Bobina de Poliéster', 'Bobina Metálica'
            ]
            
            for i in range(30):  # Increased to match the number of embroidery supplies
                supply_name = embroidery_supplies[i % len(embroidery_supplies)]
                sku = f'SKU{str(i+1).zfill(4)}'
                insumo, created = Insumo.objects.get_or_create(
                    sku=sku,
                    defaults={
                        'nombre': supply_name,
                        'descripcion': f'Insumo profesional para bordado: {supply_name}',
                        'color': random.choice(colors) if 'Hilo' in supply_name or 'Tela' in supply_name else '',
                        'unidad': 'unidad',
                        'stock_actual': random.randint(0, 100),
                        'stock_minimo': random.randint(5, 15),
                        'precio_unitario': Decimal(str(random.uniform(5.0, 500.0))).quantize(Decimal('0.01'))
                    }
                )
                insumos.append(insumo)
            
            # Create orders with realistic client distribution
            # Some clients will have many orders, others few or none
            for _ in range(25):  # Increased to 25 orders for better distribution
                # Weighted random selection: some clients more likely to have orders
                client_weights = [random.randint(1, 10) for _ in clients]
                selected_client = random.choices(clients, weights=client_weights)[0]
                
                order = Pedido.objects.create(
                    cliente=selected_client,
                    estado=random.choice([x[0] for x in Pedido.ESTADOS]),
                    creado_por=random.choice([admin, encargado]),
                    total=Decimal('0')
                )
                
                # Add 1-5 items to each order
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
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded mock data'))
