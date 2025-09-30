from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from gestion_general.models import Usuario, Producto, Pedido


class Command(BaseCommand):
    help = 'Setup permissions for existing users'

    def handle(self, *args, **options):
        # Get content types
        producto_type = ContentType.objects.get_for_model(Producto)
        pedido_type = ContentType.objects.get_for_model(Pedido)

        # Get all permissions for Producto and Pedido
        producto_permissions = Permission.objects.filter(content_type=producto_type)
        pedido_permissions = Permission.objects.filter(content_type=pedido_type)

        # Update all empleados
        empleados = Usuario.objects.filter(rol='emp')
        for empleado in empleados:
            self.stdout.write(f'Setting up permissions for {empleado.username}')
            
            # Make sure they are staff
            if not empleado.is_staff:
                empleado.is_staff = True
                empleado.save(update_fields=['is_staff'])

            # Assign permissions
            for perm in producto_permissions:
                empleado.user_permissions.add(perm)
            for perm in pedido_permissions:
                empleado.user_permissions.add(perm)

        # Update all admins
        admins = Usuario.objects.filter(rol='admin')
        for admin in admins:
            self.stdout.write(f'Setting up permissions for {admin.username}')
            
            if not admin.is_superuser:
                admin.is_superuser = True
                admin.is_staff = True
                admin.save(update_fields=['is_superuser', 'is_staff'])

        self.stdout.write(self.style.SUCCESS('Successfully set up permissions'))
