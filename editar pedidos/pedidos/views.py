from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.crypto import get_random_string
from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.forms import formset_factory
from django.forms import modelformset_factory
from django.conf import settings
from .models import PEDIDO, PRODUCTOS, DETALLE_PEDIDO, USUARIO
from .forms import LoginForm, RegistroForm, PedidoForm, ProductoForm, DetallePedidoForm
import datetime

# Create your views here.
 
# Vista para el login
def v_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo'].lower()  # Asegurarse de que el correo esté en minusculas.
            contrasena = form.cleaned_data['contrasena']
            
            # Verificar si existe un usuario con ese correo
            try:
                usuario = USUARIO.objects.get(correo=correo)
                if usuario.user.check_password(contrasena):  # Validar la contraseña
                    user = usuario.user  # Obtener el User relacionado con el modelo USUARIO
                    login(request, user)  # Iniciar sesión con el usuario

                    # Redirigir según el rol 
                    if usuario.rol == 1:  # Si es mesero
                        return redirect('pedidos:adminMesero') 
                    elif usuario.rol == 2:  # Si es cocina
                        return redirect('pedidos:adminCocina')  
                    elif usuario.rol == 3:  # Si es administrador
                        return redirect('pedidos:adminGeneral')
                else:
                    form.add_error(None, "La contraseña es incorrecta.")
            except USUARIO.DoesNotExist:
                form.add_error(None, "El usuario no existe.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})
 

# Vistas para MESERO

# Vista de lista de pedidos
@login_required
def v_mesero(request):
    if request.user.usuario.rol != 1:  # Verificar si es un mesero
        return redirect('pedidos:login')
    
    pedidos = PEDIDO.objects.filter(usuario_registro=request.user.usuario.nombre).order_by('estatus')  # Obtener pedidos ordenados por el estado
    
    # Configurar la paginación
    paginator = Paginator(pedidos, 5)  # Mostrar 5 pedidos por página
    page_number = request.GET.get('page')  # Obtener el número de página de la URL
    page_obj = paginator.get_page(page_number)  # Obtener la página actual

    # Calcular el total de cada pedido
    for pedido in page_obj:
        detalles = pedido.detalles.all()  # Para obtener detalles
        total = sum([detalle.total() for detalle in detalles])  # Calcular total
        setattr(pedido, 'total', total)  # Asignar total como atributo dinámico
    
    return render(request, 'areaMesero.html', {'pedidos': page_obj})

# Vista para cargar los productos y filtrarlos.
def v_cargar_productos(request):
    categoria_id = request.GET.get('categoria', None)
    productos = PRODUCTOS.objects.filter(categoria=categoria_id) if categoria_id else PRODUCTOS.objects.none()

    data = [{"id": p.idProducto, "text": f"{p.nombre} - ${p.precio}"} for p in productos]
    return JsonResponse({"productos": data})

# Vista para crear un nuevo pedido
@login_required
def v_crear_pedido(request):
    if request.user.usuario.rol != 1:  # Verificar si es un mesero
        return redirect('pedidos:login')
    
    DetalleFormSet = formset_factory(DetallePedidoForm, extra=1, can_delete=True)

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        formset = DetalleFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            print("Información del Formulario:", request.POST)
            # Crear el pedido
            pedido = form.save(commit=False)
            pedido.usuario_registro = request.user.usuario.nombre
            pedido.estatus = 1  # El pedido comienza con el estatus 'CREADO'
            pedido.save()

            # Guardar los detalles del pedido
            for i, detalle_form in enumerate(formset):
                if detalle_form.cleaned_data:
                    producto_id = request.POST.get(f'form-{i}-producto')
                    cantidad = detalle_form.cleaned_data['cantidad']

                    if producto_id:
                        try:
                            producto = PRODUCTOS.objects.get(pk=producto_id)  # Intentamos obtener el producto
                        except PRODUCTOS.DoesNotExist:
                            # Si no se encuentra el producto
                            messages.error(request, f"Producto con ID {producto_id} no encontrado.")
                            continue  # Continuamos con el siguiente detalle
                    else:
                        producto = None

                    if producto and cantidad >= 1:   # Solo intentamos guardar si el producto existe
                        DETALLE_PEDIDO.objects.create(
                            pedido=pedido,
                            nombre_producto=producto.nombre,
                            cantidad=cantidad,
                            precio_unitario=producto.precio
                        )
                    else:
                        print(f"No se guarda el producto: {producto.nombre if producto else 'Desconocido'}, Cantidad: {cantidad}")
                        messages.error(request, f"Cantidad inválida o producto no encontrado: {producto_id if not producto else ''}")
            messages.success(request, 'Pedido creado exitosamente.')
            return render(request, 'areaMeseroCrearPedido.html', { 'form': PedidoForm(), 'formset': DetalleFormSet(), 'categorias': PRODUCTOS.CATEGORIA, 'pedido_exitoso': True})
        else:
            messages.error(request, 'Hubo un error en el formulario. Por favor, inténtalo de nuevo.')
    else:
        form = PedidoForm()
        formset = DetalleFormSet()

    categorias = PRODUCTOS.CATEGORIA

    return render(request, 'areaMeseroCrearPedido.html', {'form': form, 'formset': formset, 'categorias': categorias})


from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.contrib.auth.decorators import login_required

@login_required
def v_editar_pedido(request, id_pedido):
    if request.user.usuario.rol != 1:  # Verificar si es mesero
        return redirect('pedidos:login')

    pedido = get_object_or_404(PEDIDO, pk=id_pedido)
    DetalleFormSet = formset_factory(DetallePedidoForm, extra=0, can_delete=True)

    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        formset = DetalleFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Actualizar datos del pedido
            pedido = form.save(commit=False)
            pedido.usuario_registro = request.user.usuario.nombre
            pedido.save()

            # Eliminar detalles existentes y crear nuevos (forma simple y segura)
            DETALLE_PEDIDO.objects.filter(pedido=pedido).delete()

            for i, detalle_form in enumerate(formset):
                if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE', False):
                    producto_id = request.POST.get(f'form-{i}-producto')
                    cantidad = detalle_form.cleaned_data['cantidad']

                    try:
                        producto = PRODUCTOS.objects.get(pk=producto_id)
                    except PRODUCTOS.DoesNotExist:
                        messages.error(request, f"Producto con ID {producto_id} no encontrado.")
                        continue

                    if producto and cantidad >= 1:
                        DETALLE_PEDIDO.objects.create(
                            pedido=pedido,
                            nombre_producto=producto.nombre,
                            cantidad=cantidad,
                            precio_unitario=producto.precio
                        )
            messages.success(request, 'Pedido actualizado exitosamente.')
            return redirect('pedidos:adminMesero')  # Cambiado para redirigir al panel del mesero
        else:
            messages.error(request, 'Hubo un error en el formulario.')
    else:
        form = PedidoForm(instance=pedido)

        # Creamos data inicial para el formset con los detalles del pedido
        detalles = DETALLE_PEDIDO.objects.filter(pedido=pedido)
        formset_data = [{
            'producto': detalle.nombre_producto,
            'cantidad': detalle.cantidad
        } for detalle in detalles]
        DetalleFormSet = formset_factory(DetallePedidoForm, extra=0, can_delete=True)
        formset = DetalleFormSet(initial=formset_data)

    categorias = PRODUCTOS.CATEGORIA

    return render(request, 'areaMeseroEditarPedido.html', {
        'form': form,
        'formset': formset,
        'categorias': categorias
    })


# Vista para eliminar un pedido
@login_required
def v_eliminar_pedido(request, id_pedido):
    if request.user.usuario.rol != 1:  # Verificar si es un mesero
        return redirect('pedidos:login')
    
    pedido = get_object_or_404(PEDIDO, idPedido=id_pedido, estatus=1)  # Solo se pueden eliminar pedidos con estatus 'CREADO'
    
    if request.method == 'POST':
        # Eliminar los detalles asociados al pedido
        DETALLE_PEDIDO.objects.filter(pedido=pedido).delete()

        # Eliminar el pedido
        pedido.delete()
        messages.success(request, 'Pedido eliminado exitosamente.')
        return redirect('pedidos:adminMesero')
    
    messages.error(request, 'Operación no permitida.')
    return redirect('pedidos:adminMesero')

# Vista para marcar el pedido como entregado
@login_required
def v_marcar_entregado(request, id_pedido):
    pass





# Vistas para PERSONAL DE COCINA

# Vista de lista de pedidos
@login_required
def v_chef(request):
    pass

# Vista para que el personal de cocina pueda aceptar los pedidos
@login_required
def v_aceptar_pedido(request, id_pedido):
    pass

# Vista para cambiar el estado de un pedido a "Listo para entrega"
@login_required
def v_listo_para_entrega(request, id_pedido):
    pass




# Vistas para ADMINISTRADOR
def v_admin_general(request):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea administrador
        return redirect('pedidos:login')
    
    return render(request, 'admin.html')


# Vista de lista de usuarios
@login_required
def v_lista_usuarios(request):
    if request.user.usuario.rol != 3:  # Verificar si es un administrador
        return redirect('pedidos:login')
    
    usuarios = USUARIO.objects.all()  # Obtiene todos los usuarios
    
    if not usuarios:
        messages.warning(request, 'No hay usuarios registrados.')

    # Configurar la paginación
    paginator = Paginator(usuarios, 5)  # Mostrar 5 usuarios por página
    page_number = request.GET.get('page')  # Obtener el número de página de la URL
    page_obj = paginator.get_page(page_number)  # Obtener la página actual
    
    return render(request, 'adminUsuarios.html', {'usuarios': page_obj})

# Vista para el registro de usuarios
def v_registro_usuario(request): 
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                # Guardar los datos del formulario (sin la contraseña)
                usuario = form.save(commit=False)

                # Generar una contraseña aleatoria para el usuario
                contrasena = get_random_string(length=8)

                # Crear el User de Django (la contraseña se guarda de manera segura)
                user = User.objects.create_user(
                    username=usuario.correo,  # Usamos el correo como nombre de usuario
                    password=contrasena,
                    email=usuario.correo  # Guardamos el correo
                )

                # Asignamos el objeto User de Django al modelo USUARIO
                usuario.user = user
                usuario.save()

                # Enviar correo con la contraseña generada
                asunto = "Bienvenido a la Plataforma"
                mensaje = (
                    f"Hola {usuario.nombre},\n\n"
                    f"Tu cuenta ha sido creada exitosamente.\n"
                    f"Correo: {usuario.correo}\n"
                    f"Contraseña: {contrasena}\n\n"
                    "Te recomendamos cambiar tu contraseña después de iniciar sesión.\n\n"
                    "Atentamente,\n"
                    "Equipo de Soporte."
                )
                remitente = settings.EMAIL_HOST_USER
                destinatario = [usuario.correo]

                send_mail(asunto, mensaje, remitente, destinatario, fail_silently=False)

                form = RegistroForm() # Limpiar los campos después de guardar los datos
                return render(request, 'adminRegistroUsuarios.html', {'registro_exitoso': True, 'form': form})
            except Exception as e:
                form.add_error(None, 'Ocurrió un error al registrar el usuario.')
                return render(request, 'adminRegistroUsuarios.html', {'form': form, 'registro_exitoso': False})
    else:
        form = RegistroForm()
    return render(request, 'adminRegistroUsuarios.html', {'form': form, 'registro_exitoso': False})

# Vista para editar un usuario
@login_required
def v_editar_usuario(request, id_usuario):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    usuario = get_object_or_404(USUARIO, idUsuario=id_usuario)  # Obtiene el usuario a editar
    user = usuario.user  # Obtener el usuario de Django asociado

    # Calcular la fecha máxima
    fecha_max = datetime.date.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        form = RegistroForm(request.POST, instance=usuario)
        if form.is_valid():
            # Guardar los datos del modelo USUARIO
            usuario = form.save()

            nuevo_email = usuario.correo  # Nuevo correo ingresado

            # Verificar si el correo ya está en uso por otro usuario
            if User.objects.exclude(id=user.id).filter(email=nuevo_email).exists():
                messages.error(request, 'El correo electrónico ya está en uso por otro usuario.')
                return render(request, 'adminEditarUsuario.html', {'form': form, 'usuario': usuario})
            
            # Actualizar correo y username en User si no están en uso
            if user.email != nuevo_email:
                user.email = nuevo_email
            if user.username != nuevo_email:
                user.username = nuevo_email
            
            user.save()  # Guardar cambios en User

            messages.success(request, 'Usuario actualizado exitosamente.')
            return render(request, 'adminEditarUsuario.html', {'form': form, 'usuario': usuario, 'usuario_actualizado': True})
    else:
        form = RegistroForm(instance=usuario)
    
    return render(request, 'adminEditarUsuario.html', {'form': form, 'usuario': usuario, 'fecha_max': fecha_max})

# Vista para eliminar un usuario
@login_required
def v_eliminar_usuario(request, id_usuario):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    usuario = get_object_or_404(USUARIO, idUsuario=id_usuario)  # Obtiene el usuario a eliminar
    user_django = usuario.user # Obtiene el objeto User de Django relacionado con este usuario
    
    if request.method == 'POST':
        # Evitar que el usuario elimine su propio registro
        if request.user.usuario.idUsuario == usuario.idUsuario:
            messages.error(request, 'No puedes eliminar tu propio usuario.')
            return redirect('pedidos:admin_usuarios')
        
        # Primero, elimina el usuario de Django
        user_django.delete()

        # Luego, elimina el usuario del modelo USUARIO
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('pedidos:admin_usuarios')
    
    messages.error(request, 'Operación no permitida.')
    return redirect('pedidos:admin_usuarios')


# Vista para ver la lista de productos
@login_required
def v_lista_productos(request):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    productos = PRODUCTOS.objects.all()  # Obtiene todos los productos

    if not productos:
        messages.warning(request, 'No hay productos registrados.')

    # Configurar la paginación
    paginator = Paginator(productos, 5)  # Mostrar 5 productos por página
    page_number = request.GET.get('page')  # Obtener el número de página de la URL
    page_obj = paginator.get_page(page_number)  # Obtener la página actual
    
    return render(request, 'adminProductos.html', {'productos': page_obj})

# Vista para agregar un nuevo producto
@login_required
def v_agregar_producto(request):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            try:
                # Guardar el producto si el formulario es válido
                form.save()

                # Limpiar el formulario después de guardar
                form = ProductoForm()
                
                # Renderizar la plantilla con el modal de éxito
                return render(request, 'adminAgregarProducto.html', {'registro_exitoso': True, 'form': form})
            except Exception as e:
                form.add_error(None, 'Ocurrió un error al agregar el producto.')
                return render(request, 'adminAgregarProducto.html', {'form': form, 'registro_exitoso': False})
    else:
        form = ProductoForm()
    return render(request, 'adminAgregarProducto.html', {'form': form, 'registro_exitoso': False})

# Vista para editar un producto
@login_required
def v_editar_producto(request, id_producto):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    producto = get_object_or_404(PRODUCTOS, idProducto=id_producto)  # Obtiene el producto a editar
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return render(request, 'adminEditarProducto.html', {'form': form, 'producto_actualizado': True})
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'adminEditarProducto.html', {'form': form, 'producto_actualizado': False})

# Vista para eliminar un producto
@login_required
def v_eliminar_producto(request, id_producto):
    if request.user.usuario.rol != 3:  # Verifica que el usuario sea un administrador
        return redirect('pedidos:login')
    
    producto = get_object_or_404(PRODUCTOS, idProducto=id_producto)  # Obtiene el producto a eliminar
    
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('pedidos:admin_productos')
    
    messages.error(request, 'Operación no permitida.')
    return redirect('pedidos:admin_productos')

  
# Vista para cambiar la contraseña teniendo la contraseña actual
@login_required
def v_cambiar_contraseña(request):
    if request.method == 'POST':
        # Usar el formulario de cambio de contraseña sin contraseña actual
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            # Guardar la nueva contraseña
            form.save()
            # Mantener la sesión del usuario activa después de cambiar la contraseña
            update_session_auth_hash(request, request.user)

            # Obtener el usuario de la tabla USUARIO
            usuario = USUARIO.objects.get(user=request.user) 
            
            # Redirigir según el rol del usuario
            if usuario.rol == 1:  # MESERO
                redirect_url = reverse('pedidos:adminMesero')
            elif usuario.rol == 2:  # COCINA
                redirect_url = reverse('pedidos:adminCocina')
            elif usuario.rol == 3:  # GESTOR
                redirect_url = reverse('pedidos:adminGeneral')
            else:
                redirect_url = reverse('pedidos:login')  # Si no tiene un rol definido
            
            # Redirigir al panel correspondiente
            return render(request, 'cambiarContraseña.html', {'form': form, 'cambio_exitoso': True, 'redirect_url': redirect_url})
        else:
            # Si el formulario no es válido, mostrar los errores
            messages.error(request, "Hubo un error al cambiar la contraseña.")
    else:
        # Crear el formulario para cambiar la contraseña
        form = PasswordChangeForm(user=request.user)

    return render(request, 'cambiarContraseña.html', {'form': form})


# Vista para enviar correo de recuperación de contraseña
def v_recuperar_contraseña(request):
    # Borra todos los mensajes de la sesión
    request.session['messages'] = []

    correo_enviado = False 
    correo_inexistente = False 

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email__iexact=email)
                # Generar uid y token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                # Generar enlace de recuperación dinámico
                reset_link = request.build_absolute_uri(
                    reverse('pedidos:recuperar_contraseña_confirmar', kwargs={'uidb64': uid, 'token': token})
                )

                # Enviar correo con el enlace de recuperación
                subject = "Recuperación de contraseña"
                message_html = render_to_string('textoEmail.html', {
                    'reset_link': reset_link,
                    'user': user,
                })

                email_message = EmailMultiAlternatives(subject, message_html, settings.EMAIL_HOST_USER, [email])
                email_message.attach_alternative(message_html, "text/html")
                email_message.send()
                
                correo_enviado = True  # Activar modal
            except User.DoesNotExist:
                correo_inexistente = True # Correo no registrado
        else:
            messages.error(request, "Por favor ingresa un correo válido.")
    else:
        form = PasswordResetForm()

    return render(request, 'recuperarContraseña.html', {'form': form, 'correo_enviado': correo_enviado, 'correo_inexistente': correo_inexistente})


# Vista para recuperar la contraseña (hacer cambio)
def recuperar_contraseña_confirmar(request, uidb64, token):
    try:
        # Decodificar el UID del usuario
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        # Verificar que el token sea válido
        if default_token_generator.check_token(user, token):
            if request.method == "POST":
                # Crear el formulario de cambio de contraseña
                form = SetPasswordForm(user, request.POST)

                if form.is_valid():
                    # Si el formulario es válido, guardar la nueva contraseña
                    form.save()
                    return render(request, 'restablecerContraseña.html', {'form': form, 'cambio_exitoso': True})  # Mostrar el modal
                else:
                    return render(request, 'restablecerContraseña.html', {'form': form, 'cambio_exitoso': False})
            else:
                # Si es un GET, mostrar el formulario vacío
                form = SetPasswordForm(user)
                return render(request, 'restablecerContraseña.html', {'form': form, 'cambio_exitoso': False})

        else:
            # Si el token es inválido o ha expirado
            messages.error(request, "El enlace de recuperación ha expirado o es inválido.")
            return redirect(reverse('pedidos:recuperar_contraseña'))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        # En caso de error al obtener el usuario
        messages.error(request, "El enlace de recuperación es inválido.")
        return redirect(reverse('pedidos:recuperar_contraseña'))
