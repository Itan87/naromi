from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from gestion_general.models import Usuario, Producto, Pedido, PedidoInsumo
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
                    'first_name': 'Administrador',
                    'last_name': 'del Sistema'
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
                    'first_name': 'Encargado',
                    'last_name': 'del Taller'
                }
            )
            if created:
                encargado.set_password('encargado123')
                encargado.save()
            
            # Create products with realistic clothing names
            products = []
            colors = ['Rojo', 'Azul', 'Verde', 'Negro', 'Blanco']
            sizes = ['S', 'M', 'L', 'XL', 'Único']
            
            clothing_types = [
                'Camisa', 'Pantalón', 'Vestido', 'Falda', 'Chaqueta',
                'Abrigo', 'Suéter', 'Blusa', 'Camiseta', 'Polo',
                'Jeans', 'Blazer', 'Chaleco', 'Sudadera', 'Jersey',
                'Top', 'Cardigan', 'Gabardina', 'Parka', 'Bermuda'
            ]
            
            styles = [
                'Casual', 'Elegante', 'Deportivo', 'Clásico', 'Moderno',
                'Vintage', 'Formal', 'Slim Fit', 'Regular Fit', 'Oversize'
            ]
            
            for i in range(20):
                clothing_type = clothing_types[i % len(clothing_types)]
                style = random.choice(styles)
                product = Producto.objects.create(
                    sku=f'SKU{str(i+1).zfill(4)}',
                    nombre=f'{clothing_type} {style}',
                    descripcion=fake.text(max_nb_chars=200),
                    color=random.choice(colors),
                    talla=random.choice(sizes),
                    unidad='unidad',
                    stock_actual=random.randint(0, 100),
                    stock_minimo=random.randint(5, 15),
                    precio_unitario=Decimal(str(random.uniform(10.0, 1000.0))).quantize(Decimal('0.01'))
                )
                products.append(product)
            
            # Create orders with items
            for _ in range(10):
                order = Pedido.objects.create(
                    cliente=fake.name(),
                    estado=random.choice([x[0] for x in Pedido.ESTADOS]),
                    creado_por=random.choice([admin, encargado]),
                    total=Decimal('0')
                )
                
                # Add 1-5 items to each order
                total = Decimal('0')
                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)
                    quantity = random.randint(1, 10)
                    
                    PedidoInsumo.objects.create(
                        pedido=order,
                        producto=product,
                        cantidad=quantity
                    )
                    
                    if product.precio_unitario:
                        total += product.precio_unitario * quantity
                
                order.total = total
                order.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded mock data'))
