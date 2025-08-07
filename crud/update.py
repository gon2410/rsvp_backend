from fastapi import HTTPException
from fastapi.responses import JSONResponse
from supabase_client import supabase
from httpx import HTTPError
from gotrue.errors import AuthApiError
from schemas import invalid_characters

def edit_guest(edited_guest, request):

    # getting the auth-cookie from the request
    cookie_token = request.cookies.get("auth-cookie")

    # if cookie does not exist, return 401
    if not cookie_token:
        raise HTTPException(status_code=401, detail="Token inexistente o no estás autorizado")
    
    # validating cookie with supabase
    try:
        response = supabase.auth.get_user(cookie_token)

        if not response or not response.user:
            raise HTTPException(status_code=401, detail="No estás autorizado.")
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail="Token expirado, vuelva a iniciar sesión")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos autenticarte.")
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")

    # validating name and lastname
    if edited_guest.name == "" or any(invalid_character in edited_guest.name for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Nombre inválido.")
        
    if edited_guest.lastname == "" or any(invalid_character in edited_guest.lastname for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Apellido inválido.")
    
    try:
        response = supabase.table("guests").update({"name": edited_guest.name, "lastname": edited_guest.lastname}).eq("id", edited_guest.id).execute()
        return JSONResponse(status_code=200, content="Guardado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos actualizar al invitado.")
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
