import os
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import string
from httpx import HTTPError
from gotrue.errors import AuthApiError
from schemas import *

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://form-supa-next.vercel.app", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ---------- AUTHENTICATION ENDPOINTS ----------

@app.post("/auth/login")
def login_user(user: User, response: Response):
    auth_response = supabase.auth.sign_in_with_password(
        {
            "email": user.email,
            "password": user.passwd,
        }
    )
    
    if not auth_response.session:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = auth_response.session.access_token
    
    response.set_cookie(
        key="auth-cookie",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )
    
    return {"message": "Login exitoso"}


@app.post("/auth/logout")
def logout_user(response: Response):
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print("Error")
    
    response = JSONResponse(content={"message": "Logout exitoso"})

    response.delete_cookie(
        key="auth-cookie",
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
    )

    return response

# ---------- PUBLIC ENDPOINTS ----------

@app.get("/")
def get_all_leaders():
    try:
        response = supabase.table("person").select("id", "name", "lastname", "created_at").eq("is_leader", True).order("lastname").execute()

        if response.data.count == 0:
            raise HTTPException(status_code=404, detail="No se encontró nada en la base de datos")
        
        return response.data
    except:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")


@app.get("/get-all-guests")
def get_all_guests():
    try:
        response = supabase.table("person").select("id", "name", "lastname", "menu", "is_leader", "companion_of").order("lastname").execute()

        if response.data.count == 0:
            raise HTTPException(status_code=404, detail="No se encontró nada en la base de datos")
            
        return response.data
    except:
        return HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")


roles = ["leader", "companion"]
menus = ["sin_condicion", "vegetariano", "vegano", "celiaco"]
invalid_characters = tuple(string.punctuation + string.digits + "¨" + "´" + "`" + "¿")
@app.post("/add-guest")
def add_guest(guest: Guest):

    if guest.name == "" or any(invalid_character in guest.name for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Nombre inválido")
        
    if guest.lastname == "" or any(invalid_character in guest.lastname for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Apellido inválido")

    if guest.menu not in menus:
        raise HTTPException(status_code=400, detail="Menú inválido")

    if guest.role not in roles:
        raise HTTPException(status_code=400, detail="Rol inválido")
    
    try:
        response = supabase.table("person").select("id").ilike("name", guest.name).ilike("lastname", guest.lastname).execute()
        if response.data:
            raise HTTPException(status_code=400, detail=f"{guest.name} {guest.lastname} ya está registrado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos verificar tu nombre. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
        
    if guest.role == "leader":
        if guest.email == "":
            raise HTTPException(status_code=400, detail="Email inválido")
        
        try:
            response = supabase.table("person").select("id").eq("email", guest.email).execute()
            if response.data:
                raise HTTPException(status_code=400, detail="El e-mail ya está en uso. Quizás esta intentando confirmar un acompañante")
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos verificar el email. Intente de nuevo.")
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
        try:
            response = supabase.table("person").insert({"name": guest.name, "lastname": guest.lastname, "menu": guest.menu, "email": guest.email, "is_leader": True}).execute()
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos inscribirte. Intente de nuevo.")
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
    else:
        if guest.leader == "":
            raise HTTPException(status_code=400, detail="ID de líder inválido.")
        
        try:
            response = supabase.table("person").select("id").eq("id", guest.leader).execute()
            if not response.data:
                raise HTTPException(status_code=404, detail="No se encontró un invitado líder con ese ID.")
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos verificar al responsable de grupo. Intente de nuevo.")
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
        try:
            response = supabase.table("person").insert({"name": guest.name, "lastname": guest.lastname, "menu": guest.menu, "companion_of": guest.leader}).execute()
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos inscribirte. Intente de nuevo.")
        except Exception:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
        
    return JSONResponse(status_code=200, content="¡Confirmado!")


@app.post("/get-group")
def get_group(group: Group):
    group_list = []
    if group.email == "":
        raise HTTPException(status_code=400, detail="Email inválido")
    
    try:
        response = supabase.table("person").select("*").eq("email", group.email).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="No pudimos encontrar esa direccion de email.")

        group_list = [response.data[0]]
        leader_id = response.data[0]["id"]

        response = supabase.table("person").select("*").eq("companion_of", leader_id).execute()

        for member in response.data:
            group_list.append(member)

        return JSONResponse(status_code=200, content=group_list)
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos verificar el email. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")


@app.post("/report-error")
def report_error(error: Error):

    if error.email == "":
        raise HTTPException(status_code=400, detail="Email inválido.")

    try:
        response = supabase.table("person").select("id").eq("email", error.email).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No pudimos encontrar esa direccion de email.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos verificar el email. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
     
    try:
        response = supabase.table("errors").insert({"email": error.email, "description": error.description}).execute()
        return JSONResponse(status_code=200, content="Enviado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos reportar el error. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")


@app.get("/get-statistics")
def get_numbers():
    try:
        total = supabase.table("person").select("id", count="exact").execute()
        sin_condicion = supabase.table("person").select("id", count="exact").eq("menu", "sin_condicion").execute()
        vegetariano = supabase.table("person").select("id", count="exact").eq("menu", "vegetariano").execute()
        vegano = supabase.table("person").select("id", count="exact").eq("menu", "vegano").execute()
        celiaco = supabase.table("person").select("id", count="exact").eq("menu", "celiaco").execute()
        
        data = [{"menu_name": "Total", "quantity": total.count},
                {"menu_name": "Sin Condicion", "quantity": sin_condicion.count},
                {"menu_name": "Vegetariano", "quantity": vegetariano.count},
                {"menu_name": "Vegano", "quantity": vegano.count},
                {"menu_name": "Celiaco", "quantity": celiaco.count}]
        
        return JSONResponse(status_code=200, content=data)
    except:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")


# ---------- PROTECTED ENDPOINTS ----------

@app.post("/update-guest")
def edit_guest(edit_guest: EditGuest, request: Request):

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
        raise HTTPException(status_code=401, detail="Token inválido, expirado o no estás autorizado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos autenticarte.")
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")

    # validating name and lastname
    if edit_guest.name == "" or any(invalid_character in edit_guest.name for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Nombre inválido.")
        
    if edit_guest.lastname == "" or any(invalid_character in edit_guest.lastname for invalid_character in invalid_characters):
        raise HTTPException(status_code=400, detail="Apellido inválido.")
    
    try:
        response = supabase.table("person").update({"name": edit_guest.name, "lastname": edit_guest.lastname, "menu": edit_guest.menu}).eq("id", edit_guest.id).execute()
        return JSONResponse(status_code=200, content="Guardado.")
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos actualizar al invitado.")
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")

@app.post("/delete-guest")
def delete_guest(guest_to_delete: DeleteGuest, request: Request):

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
        response = supabase.table("person").select("id", "is_leader").eq("id", guest_to_delete.id).execute()
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
            response = supabase.table("person").delete().eq("id", guest_to_delete.id).execute()

            return JSONResponse(status_code=200, content="Eliminado.")
        except HTTPError:
            raise HTTPException(status_code=503, detail="No pudimos eliminar al invitado.")
        except:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")