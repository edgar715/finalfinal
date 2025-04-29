from django import forms
from django.forms import modelformset_factory
from .models import USUARIO, PRODUCTOS, PEDIDO, DETALLE_PEDIDO
import datetime

# Formulario de Login
class LoginForm(forms.Form):
    correo = forms.EmailField()
    contrasena = forms.CharField(widget=forms.PasswordInput)

# Formulario de Registro
class RegistroForm(forms.ModelForm):
    class Meta:
        model = USUARIO
        fields = ['nombre', 'apPaterno', 'apMaterno', 'telefono', 'correo', 'rol', 'fechaRegistro']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select', 'style': 'height: 51px;'})
        }
         
    fechaRegistro = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'min': '2020-01-01', 'max': datetime.date.today().strftime('%Y-%m-%d')}))

    def clean(self):
        cleaned_data = super().clean()
        correo = cleaned_data.get('correo')
        tel = cleaned_data.get('telefono')

        # Verificar si estamos en el caso de registro o edición
        if not self.instance.pk:  # Si la instancia no existe, estamos en registro
            # Verificar si el correo ya existe en el registro
            if USUARIO.objects.filter(correo__iexact=correo).exists():
                self.add_error(None, 'El correo electrónico ya está en uso.')

            # Verificar si el número de teléfono ya existe en el registro
            if USUARIO.objects.filter(telefono__iexact=tel).exists():
                self.add_error(None, 'El número de teléfono ya está en uso.')
        else:  # Si estamos editando, solo validamos si el campo fue modificado
            if self.instance.correo != correo:
                if USUARIO.objects.filter(correo__iexact=correo).exists():
                    self.add_error(None, 'El correo electrónico ya está en uso.')

            if self.instance.telefono != tel:
                if USUARIO.objects.filter(telefono__iexact=tel).exists():
                    self.add_error(None, 'El número de teléfono ya está en uso.')

        return cleaned_data
    
# Formulario para los Pedidos
class PedidoForm(forms.ModelForm):
    class Meta:
        model = PEDIDO
        fields = ['nota_cocina']
        widgets = {
            'nota_cocina': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
    
    def clean_nota_cocina(self):
        nota_cocina = self.cleaned_data.get('nota_cocina')
        
        # Si la nota de cocina está vacía, asignar "SIN DETALLES"
        if not nota_cocina:
            return "SIN DETALLES"
        return nota_cocina

# Formulario para Detalle de Pedido (Seleccionar Producto y Cantidad)
class DetallePedidoForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'required': 'required',
            'min': '1',
            'value': '1'  
        }),
        required=True
    )

# Formulario para Productos
class ProductoForm(forms.ModelForm):
    class Meta:
        model = PRODUCTOS
        fields = ['categoria', 'nombre', 'descripcion', 'precio'] 
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select', 'style': 'height: 51px;'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'})
        }
       