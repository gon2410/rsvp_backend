from fastapi import HTTPException
from supabase_client import supabase
from httpx import HTTPError
from gotrue.errors import AuthApiError
from fastapi.responses import JSONResponse

def delete_guest(guest_to_delete, request):

    # getting the auth-cookie from the request
    cookie_token = request.cookies.get("auth-cookie")

    # if cookie does not exist, return 401
    if not cookie_token:
        raise HTTPException(status_code=401, detail="Token inexistente o no estás autorizado.")

    # validating cookie with supabase
    try:
        response = supabase.auth.get_user(cookie_token)

        if not response or not response.user:
            raise HTTPException(status_code=401, detail="No estás autorizado.")
    except AuthApiError:
        raise HTTPException(status_code=401, detail="Token inválido o no estás autorizado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos autenticarte.")
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")


    # getting the guest from supabase
    try:
        response = supabase.table("guests").select("id", "is_leader").eq("id", guest_to_delete.id).execute()
        if not response or not response.data:
            raise HTTPException(status_code=404, detail="No encontramos al invitado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="Algo salió mal buscando al invitado.")
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")

    guest = response.data[0]

    # if the guest is leader, the leader attribute should be given to someone from the same group!!!
    # WORKING ON IT, but for the moment...
    # if the guest is leader, it won't be deleted. If not, it will be.
    if guest["is_leader"]:
        raise HTTPException(status_code=400, detail="No se puede eliminar a líderes por el momento.")
    else:
        try:
            response = supabase.table("guests").delete().eq("id", guest_to_delete.id).execute()

            return JSONResponse(status_code=200, content="Eliminado.")
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos eliminar al invitado.")
        except:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")