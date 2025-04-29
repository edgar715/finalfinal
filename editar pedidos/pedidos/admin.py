from django.contrib import admin
from .models import USUARIO, PRODUCTOS, PEDIDO, DETALLE_PEDIDO

# Register your models here.
admin.site.register(USUARIO)
admin.site.register(PRODUCTOS)
admin.site.register(PEDIDO)
admin.site.register(DETALLE_PEDIDO)