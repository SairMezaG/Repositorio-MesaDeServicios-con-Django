from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib import auth
from appMesaServicio.models import *
from random import *
from django.db import Error, transaction
from datetime import datetime
# para correo
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
import threading
from smtplib import SMTPException
from django.http import JsonResponse

# Create your views here.


def inicio(request):
    return render(request, "frmIniciarSesion.html")


def inicioAdministrador(request):
    if request.user.is_authenticated:
        datosSesion = {"user": request.user,
                       "rol": request.user.groups.get().name}
        return render(request, "administrador/inicio.html", datosSesion)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})


def inicioTecnico(request):
    if request.user.is_authenticated:
        datosSesion = {"user": request.user,
                       "rol": request.user.groups.get().name}
        return render(request, "tecnico/inicio.html", datosSesion)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})


def inicioEmpleado(request):
    if request.user.is_authenticated:
        datosSesion = {"user": request.user,
                       "rol": request.user.groups.get().name}
        return render(request, "empleado/inicio.html", datosSesion)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})


def login(request):
    username = request.POST["usuario"]
    password = request.POST["contraseña"]
    user = authenticate(username=username, password=password)
    if user is not None:
        # registrar la variable de sesión
        auth.login(request, user)
        if user.groups.filter(name='Administrador').exists():
            return redirect('/inicioAdministrador')
        elif user.groups.filter(name='Tecnico').exists():
            return redirect('/inicioTecnico')
        else:
            return redirect('/inicioEmpleado')
    else:
        mensaje = "Usuario o Contraseña Incorrectas"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})


def vistaSolicitud(request):
    if request.user.is_authenticated:
        # consultar las oficinas y ambientes registrados
        oficinaAmbientes = OficinaAmbiente.objects.all()
        datosSesion = {"user": request.user,
                       "rol": request.user.groups.get().name,
                       'oficinasAmbientes': oficinaAmbientes}
        return render(request, 'empleado/solicitud.html', datosSesion)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "frmIniciarSesion.html", {"mensaje": mensaje})


def registrarSolicitud(request):
    try:
        with transaction.atomic():
            user = request.user
            descripcion = request.POST['descripcion']
            idOficinaAmbiente = int(request.POST['selectOficinaAmbiente'])
            oficinaAmbiente = OficinaAmbiente.objects.get(pk=idOficinaAmbiente)
            solicitud = Solicitud(solUsuario=user, solDescripcion=descripcion,
                                  solOficinaAmbiente=oficinaAmbiente)
            solicitud.save()
            # obtener año para en el consecutivo agregar el año.
            fecha = datetime.now()
            year = fecha.year
            # obtener el número de solicitudes hechas por año actual
            consecutivoCaso = Solicitud.objects.filter(
                fechaHoraCreacion__year=year).count()
            # ajustar el consecutivon con ceros a las izquierda
            consecutivoCaso = str(consecutivoCaso).rjust(5, '0')
            # crear el código del caso formato REQ-AÑOVIGENCIA-CONSECUTIVO
            codigoCaso = f"REQ-{year}-{consecutivoCaso}"
            # consultar el usuario tipo Administrador para asignarlo al caso
            userCaso = User.objects.filter(
                groups__name__in=['administrador']).first()
            # crear el caso
            caso = Caso(casSolicitud=solicitud,
                        casCodigo=codigoCaso, casUsuario=userCaso)
            caso.save()
            # enviar el correo al empleado
            asunto = 'Registro Solicitud - Mesa de Servicio'
            mensajeCorreo = f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos \
                informarle que su solicitud fue registrada en nuestro sistema con el número de caso \
                <b>{codigoCaso}</b>. <br><br> Su caso será gestionado en el menor tiempo posible, \
                según los acuerdos de solución establecidos para la Mesa de Servicios del CTPI-CAUCA.\
                <br><br>Lo invitamos a ingresar a nuestro sistema en la siguiente url:\
                http://mesadeservicioctpicauca.sena.edu.co.'
            # crear el hilo para el envío del correo
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensajeCorreo, [user.email]))
            # ejecutar el hilo
            thread.start()
            mensaje = "Se ha registrado su solicitud de manera exitosa"
    except Error as error:
        transaction.rollback()
        mensaje = f"{error}"

    oficinaAmbientes = OficinaAmbiente.objects.all()
    retorno = {"mensaje": mensaje, "oficinasAmbientes": oficinaAmbientes}
    return render(request, "empleado/solicitud.html", retorno)


def enviarCorreo(asunto=None, mensaje=None, destinatario=None, archivo=None):
    remitente = settings.EMAIL_HOST_USER
    template = get_template('enviarCorreo.html')
    contenido = template.render({
        'mensaje': mensaje,
    })
    try:
        correo = EmailMultiAlternatives(
            asunto, mensaje, remitente, destinatario)
        correo.attach_alternative(contenido, 'text/html')
        if archivo != None:
            correo.attach_file(archivo)
        correo.send(fail_silently=True)
    except SMTPException as error:
        print(error)


def salir(request):
    auth.logout(request)
    return render(request, "frmIniciarSesion.html",
                  {"mensaje": "Ha cerrado la sesión"})


# //////////////////////////////

def listarCasos(request):
    try:
        mensaje=""
        listaCasos= Caso.objects.all()
        tecnicos=User.objects.filter(groups__name__in=['tecnico'])
        
        
    except Error as error:
        mensaje=str(error)
    retorno={'listaCasos':listaCasos,'tecnicos':tecnicos, 'mensaje':mensaje}
    return render(request,'administrador/listarCaso.html', retorno)


def listarEmpleadosTecnicos(request):
    try:
        # consulta para obtener todos los tecnicos
        tecnicos=User.objects.filter(groups__name__in=['Tecnico'])
        mensaje=''
    except Error as error:
        mensaje=str(error)
    retorno={'tecnicos':tecnicos, 'mensaje':mensaje}
    return JsonResponse(retorno)




def asignarTecnicoCaso(request):
    if request.user.is_authenticated:
        try:
            idTecnico=int(request.POST['selectTecnicoCaso'])
            userTecnico=User.objects.get(pk=idTecnico)
            idCaso=int(request.POST['idCaso'])
            caso=Caso.objects.get(pk=idCaso)
            caso.casUsuario= userTecnico
            caso.casEstado= " En proceso"
            caso.save()
            
            # enviar el correo al tecnico
            asunto = 'Registro Solicitud - Mesa de Servicio'
            mensajeCorreo = f'Cordial saludo, <b>{userTecnico.first_name} {userTecnico.last_name}</b>, nos permitimos \
                informarle que se le ha asignado un caso para dar solucion en el sistema con el número de caso \
                <b>{Caso.casCodigo}</b>. <br><br> Se solicita se atienda de manera oportuna, \
                según los acuerdos de solución establecidos para la Mesa de Servicios del CTPI-CAUCA.\
                <br><br>Lo invitamos a ingresar al sistema para gestionar sus casos asignados en la siguiente url:\
                http://mesadeservicioctpicauca.sena.edu.co.'
            # crear el hilo para el envío del correo
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensajeCorreo, [userTecnico.email]))
            # ejecutar el hilo
            thread.start()
            mensaje='Caso asignado'
            
            
            
        except Error as error:
            mensaje=str(error)
            
        return redirect('/listarCasosParaAsignar/')
    else:
        mensaje="Debe iniciar sesión Primero"
        
        
    
# ///////////////////////////
def listarCasosAsignadosTecnico(request):
    if request.user.is_authenticated:
        try:
            ListaCasos=Caso.objects.filter(casEstado=" En Proceso",
                                        casUsuario=request.user)
            TipoProcedimientos=TipoProcedimiento.objects.all()
            
            mensaje="lista de casos asignados"
        except Error as error:
            mensaje=str(error)
           
        retorno={"mensaje":mensaje, "ListaCasos":ListaCasos,
                "tipoSolucion":tipoSolucion, "TipoProcedimientos":TipoProcedimientos}
        return render(request,'tecnico/listarCasosAsignados.html',retorno)
    else:
        mensaje="debes iniciar sesión"
        return render(request, "frmIniciarSesion.html",{"mensaje":mensaje})     
    
    
    
    
    