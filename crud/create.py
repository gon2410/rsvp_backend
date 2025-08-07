from fastapi import HTTPException
from httpx import HTTPError
from fastapi.responses import JSONResponse
import string
from supabase_client import supabase
from schemas import roles, invalid_characters

def add_guest(guest):

    if guest.name == "" or any(invalid_character in guest.name for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Nombre inválido")
        
    if guest.lastname == "" or any(invalid_character in guest.lastname for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Apellido inválido")

    if guest.role not in roles:
        raise HTTPException(status_code=400, detail="Rol inválido")
    
    try:
        response = supabase.table("guests").select("id").ilike("name", guest.name).ilike("lastname", guest.lastname).execute()
        if response.data:
            raise HTTPException(status_code=400, detail=f"{guest.name} {guest.lastname} ya está registrado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos verificar tu nombre. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
        
    if guest.role == "leader":
        if guest.email == "":
            raise HTTPException(status_code=400, detail="Email inválido")
        
        try:
            response = supabase.table("guests").select("id").eq("email", guest.email).execute()
            if response.data:
                raise HTTPException(status_code=400, detail="El e-mail ya está en uso. Quizás esta intentando confirmar un acompañante")
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos verificar el email. Intente de nuevo.")
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
        try:
            response = supabase.table("guests").insert({"name": guest.name, "lastname": guest.lastname, "email": guest.email, "is_leader": True}).execute()
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos inscribirte. Intente de nuevo.")
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
    else:
        if guest.leader == "":
            raise HTTPException(status_code=400, detail="ID de líder inválido.")
        
        try:
            response = supabase.table("guests").select("id").eq("id", guest.leader).execute()
            if not response.data:
                raise HTTPException(status_code=404, detail="No se encontró un invitado líder con ese ID.")
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos verificar al responsable de grupo. Intente de nuevo.")
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
        try:
            response = supabase.table("guests").insert({"name": guest.name, "lastname": guest.lastname, "companion_of": guest.leader}).execute()
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos inscribirte. Intente de nuevo.")
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
    return JSONResponse(status_code=200, content="¡Confirmado!")



def report_error(error):
    if error.name == "" or any(invalid_character in error.name for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Nombre inválido")
        
    if error.lastname == "" or any(invalid_character in error.lastname for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Apellido inválido")

    if error.email == "":
        raise HTTPException(status_code=400, detail="Email inválido.")

    try:
        response = supabase.table("guests").select("id").eq("email", error.email).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No pudimos encontrar esa direccion de email.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos verificar el email. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
     
    try:
        response = supabase.table("errors").insert({"name": error.name, "lastname": error.lastname, "email": error.email, "description": error.description}).execute()
        return JSONResponse(status_code=200, content="Enviado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos reportar el error. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
