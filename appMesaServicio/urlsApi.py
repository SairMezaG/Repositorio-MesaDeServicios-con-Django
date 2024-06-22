from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    
    path('oficinaambiente/', views.OficinaAmbienteList.as_view()),
    path('oficinaambiente/int:<pk>/', views.OficinaAmbienteDetail.as_view()),
    
    path('user/', views.UserList.as_view()),
    path('user/int:<pk>/', views.UserDetail.as_view()),
    
    path('solicitud/', views.SolicitudList.as_view()),
    path('solicitud/int:<pk>/', views.SolicitudDetail.as_view()),
    
    
    path('caso/', views.CasoList.as_view()),
    path('caso/int:<pk>/', views.CasoDetail.as_view()),
    
    
    path('tipoprocedimiento/', views.TipoProcedimientoList.as_view()),
    path('tipoprocedimiento/int:<pk>/', views.TipoProcedimientoDetail.as_view()), 
    
    
    path('solucioncaso/', views.SolucionCasoList.as_view()),
    path('solucioncaso/int:<pk>/', views.SolucionCasoDetail.as_view()),
    
    
    path('solucioncasotipoprocedimientos/', views.SolucionCasoTipoProcedimientosList.as_view()),
    path('solucioncasotipoprocedimientos/int:<pk>/', views.SolucionCasoTipoProcedimientosDetail.as_view()), 
    
    path('docs/', include_docs_urls(title="Documentacion API")),
   

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
