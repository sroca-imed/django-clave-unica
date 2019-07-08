from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import login

from .lib.utils import oauth2_claveunica
from .models import Login as LoginClaveUnica, Person as PersonClaveUnica
from clave_unica_auth import settings

def claveunica_login(request):
    """Redirect a Clave Unica"""
    state = oauth2_claveunica.generate_state()
    cache.set(state, { 'remote_addr': request.META.get('REMOTE_ADDR') }, settings.get('CLAVEUNICA_STATE_TIMEOUT'))
    return redirect(oauth2_claveunica.get_url_login_claveunica(settings.get('CLAVEUNICA_URL_LOGIN'), settings.get('CLAVEUNICA_CLIENT_ID'), settings.get('CLAVEUNICA_REDIRECT_URI'), state))

def claveunica_callback(request):
    """Intercambio authorization_code a access_token y obtener info de usuario"""
    state = request.GET.get('state')
    code = request.GET.get('code')
    cache_data = cache.get(state)
    # verificando state en cache, si existe entonces no ha expirado el state
    if cache_data is None:
        context = {
            'error': 'State expirado',
            'description': 'El parametro state ha expirado. Por favor, vuelva a iniciar sesion.',
        }
        return claveunica_error(request, context)
    cache.delete(state)
    #crea instancia loginClaveUnica
    loginClaveUnica = LoginClaveUnica()
    loginClaveUnica.state = state
    loginClaveUnica.authorization_code = code
    loginClaveUnica.remote_addr = cache_data.get('remote_addr')
    try:
        #obtener authorization_code
        access_token_json = oauth2_claveunica.request_authorization_code(
            settings.get('CLAVEUNICA_TOKEN_URI'),
            settings.get('CLAVEUNICA_CLIENT_ID'),
            settings.get('CLAVEUNICA_CLIENT_SECRET'),
            settings.get('CLAVEUNICA_REDIRECT_URI'),
            loginClaveUnica.authorization_code,
            loginClaveUnica.state
        )
        loginClaveUnica.access_token = access_token_json.get('access_token')
        #obtener info usuario
        info_user_json = oauth2_claveunica.request_info_user(
            settings.get('CLAVEUNICA_USERINFO_URI'),
            loginClaveUnica.access_token
        )
    except Exception as e:
        #se guarda el login clave unica en bd a pesar de sea error, para guardar evidencia de auth
        loginClaveUnica.save()
        context = {
            'error': e.message if hasattr(e, 'message') else 'Error en Clave Unica',
            'description': e,
        }
        return claveunica_error(request, context)
    try:
        username = str(info_user_json['RolUnico']['numero'])+'-'+str(info_user_json['RolUnico']['DV'])
        user = User.objects.get(username = username)
    except User.DoesNotExist:
        if settings.get('CLAVEUNICA_AUTO_CREATE_USER'):
            #crea usuario y person en bd
            personClaveUnica = PersonClaveUnica()
            personClaveUnica.parse_json(info_user_json)
            user = personClaveUnica.parse_json_to_user(info_user_json)
            user.save()
            personClaveUnica.user = user
            personClaveUnica.save()
        else:
            loginClaveUnica.save()
            context = {
                'error': 'Usuario no registrado',
                'description': 'El usuario no se encuentra actualmente registrado.',
            }
            return claveunica_error(request, context)
    if user is not None:
        login(request, user)
        loginClaveUnica.user = user
        loginClaveUnica.completed = True
        loginClaveUnica.save()
        return redirect(settings.get('CLAVEUNICA_PATH_SUCCESS_LOGIN'))
    else:
        loginClaveUnica.save()
        context = {
            'error': 'Error en autenticacion',
            'description': 'No se ha logrado autenticar el usuario.',
        }
        return claveunica_error(request, context)

def claveunica_error(request, context={'error': 'Error autenticación', 'description': 'Error en autenticación del usuario.'}):
    """Error vista clave unica"""
    if not settings.get('CLAVEUNICA_REMEMBER_LOGIN'):
        context['url_logout'] = settings.get('CLAVEUNICA_URL_LOGOUT')
    return render(request, settings.get('CLAVEUNICA_HTML_ERROR'), context)