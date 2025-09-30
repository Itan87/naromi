from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Usuario, Producto, Pedido

@receiver(post_save, sender=Usuario)
def setup_user_permissions(sender, instance, created, **kwargs):
    if created or instance.rol == 'emp':  # Apply for new users or when role changes to emp
        # Make employee a staff member to access admin
        if instance.rol == 'emp' and not instance.is_staff:
            instance.is_staff = True
            instance.save(update_fields=['is_staff'])

        if instance.rol == 'emp':
            # Get content types
            producto_type = ContentType.objects.get_for_model(Producto)
            pedido_type = ContentType.objects.get_for_model(Pedido)

            # Get all permissions for Producto and Pedido
            producto_permissions = Permission.objects.filter(content_type=producto_type)
            pedido_permissions = Permission.objects.filter(content_type=pedido_type)

            # Assign permissions
            for perm in producto_permissions:
                instance.user_permissions.add(perm)
            for perm in pedido_permissions:
                instance.user_permissions.add(perm)

        elif instance.rol == 'admin':
            # Admins get all permissions through is_superuser
            instance.is_superuser = True
            instance.is_staff = True
            instance.save(update_fields=['is_superuser', 'is_staff'])
