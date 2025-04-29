from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Tabla de USUARIO
class USUARIO(models.Model):
    ROLES = (
        (1, 'MESERO'),
        (2, 'COCINA'),
        (3, 'GESTOR'),
    )

    idUsuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apPaterno = models.CharField(max_length=50)
    apMaterno = models.CharField(max_length=50)
    telefono = models.CharField(max_length=15, unique=True)
    correo = models.EmailField(unique=True)
    rol = models.IntegerField(choices=ROLES)
    fechaRegistro = models.DateField()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usuario')

    # Sobreescribir el método save() para convertir todos los campos a mayúsculas antes de guardar
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        self.apPaterno = self.apPaterno.upper()
        self.apMaterno = self.apMaterno.upper()
        super(USUARIO, self).save(*args, **kwargs)
    
    class Meta:
        # Asegurarse de que no haya correos y telefonos duplicados, sin importar mayúsculas/minúsculas
        constraints = [
            models.UniqueConstraint(fields=['telefono'], name='unique_telefono'),
            models.UniqueConstraint(fields=['correo'], name='unique_correo')
        ]

    def __str__(self):
        return f"ID: {self.idUsuario} - {self.nombre.upper()} {self.apPaterno.upper()} {self.apMaterno.upper()}"

# Tabla de PRODUCTOS del MENÚ
class PRODUCTOS(models.Model):
    CATEGORIA = (
        (1, 'BEBIDAS CALIENTES'),
        (2, 'BEBIDAS FRÍAS'),
        (3, 'BOCADILLOS'),
    )

    idProducto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    categoria = models.IntegerField(choices=CATEGORIA)

    # Sobreescribir el método save() para convertir todos los campos a mayúsculas antes de guardar
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(PRODUCTOS, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"
    
# Tabla de PEDIDO
class PEDIDO(models.Model):
    ESTATUS = (
        (1, 'CREADO'),
        (2, 'ACEPTADO'),
        (3, 'LISTO PARA ENTREGA'),
        (4, 'ENTREGADO')
    )

    idPedido = models.AutoField(primary_key=True)
    estatus = models.IntegerField(choices=ESTATUS, default=1)
    usuario_registro = models.CharField(max_length=150)
    fechaRegistro = models.DateTimeField(auto_now_add=True)
    nota_cocina = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pedido {self.idPedido}"
    
# Tabla de DETALLE PEDIDO
class DETALLE_PEDIDO(models.Model):
    idDetallePedido = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(PEDIDO, on_delete=models.CASCADE, related_name='detalles')
    nombre_producto = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"Pedido {self.pedido.idPedido} - {self.nombre_producto} (x{self.cantidad})".upper()
    
    def total(self):
        return self.cantidad * self.precio_unitario
    