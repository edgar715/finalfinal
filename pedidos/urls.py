from django.urls import path
from . import views  

app_name = 'pedidos'

urlpatterns = [
    # Ruta para el login
    path('login/', views.v_login, name='login'),

    # Rutas para el mesero
    path('mesero/', views.v_mesero, name='adminMesero'),
    path('mesero/crear/', views.v_crear_pedido, name='crear_pedido'),
    path('mesero/editar/<int:id_pedido>/', views.v_editar_pedido, name='editar_pedido'),
    path('mesero/eliminar/<int:id_pedido>/', views.v_eliminar_pedido, name='eliminar_pedido'),
    path('mesero/entregado/<int:id_pedido>/', views.v_marcar_entregado, name='marcar_entregado'),
    path('cargar_productos/', views.v_cargar_productos, name='cargar_productos'),

    # Rutas para el de cocina
    path('cocina/', views.v_chef, name='adminCocina'),
    path('cocina/aceptar/<int:id_pedido>/', views.v_aceptar_pedido, name='aceptar_pedido'),
    path('cocina/listo/<int:id_pedido>/', views.v_listo_para_entrega, name='listo_entrega'),

    # Rutas para el administrador
    path('adminGeneral/', views.v_admin_general, name='adminGeneral'),

    # Rutas para la gestión de usuarios
    path('adminGeneral/usuarios/', views.v_lista_usuarios, name='admin_usuarios'),
    path('adminGeneral/usuarios/crear/', views.v_registro_usuario, name='registro_usuario'),
    path('adminGeneral/usuarios/editar/<int:id_usuario>/', views.v_editar_usuario, name='editar_usuario'),
    path('adminGeneral/usuarios/eliminar/<int:id_usuario>/', views.v_eliminar_usuario, name='eliminar_usuario'),
    
    # Rutas para la gestión de productos
    path('adminGeneral/productos/', views.v_lista_productos, name='admin_productos'),
    path('adminGeneral/productos/agregar/', views.v_agregar_producto, name='crear_producto'),
    path('adminGeneral/productos/editar/<int:id_producto>/', views.v_editar_producto, name='editar_producto'),
    path('adminGeneral/productos/eliminar/<int:id_producto>/', views.v_eliminar_producto, name='eliminar_producto'),

    # Ruta para la recuperación de contraseña
    path('recuperar-contraseña/', views.v_recuperar_contraseña, name='recuperar_contraseña'),
    # Ruta para cambiar contraseña después del link
    path('recuperar-contraseña/<uidb64>/<token>/', views.recuperar_contraseña_confirmar, name='recuperar_contraseña_confirmar'),
    # Ruta para cambiar contraseña teniendo la actual
    path('cambiar-contraseña/', views.v_cambiar_contraseña, name='cambiar_contraseña'),
]
