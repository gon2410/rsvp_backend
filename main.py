import os
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


load_dotenv()


url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://form-supa-next.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/auth/status")
def get_user(request: Request):
    cookie_name = "sb-" + os.environ.get("SUPABASE_URL").split("https://")[1].split(".")[0] + "-auth-token"

    raw_cookie_header = request.headers.get("cookie", "")
    token_cookie = None
    for cookie in raw_cookie_header.split(";"):
        if cookie_name in cookie:
            token_cookie = cookie.split("=")[1].strip()
            break

    if not token_cookie:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    try:
        user_response = supabase.auth.get_user(token_cookie)
        if user_response.user is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"user": user_response.user}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


class User(BaseModel):
    email: str
    passwd: str

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

    cookie_name = "sb-" + os.environ.get("SUPABASE_URL").split("https://")[1].split(".")[0] + "-auth-token"
    token = auth_response.session.access_token
    print(token)
    response = JSONResponse(content={"message": "Login exitoso"})
    
    response.set_cookie(
        key=cookie_name,
        value=token,
        httponly=True,
        secure=False,
        samesite="Lax",
        path="/",
    )
    
    return response


@app.post("/auth/logout")
def logout_user(request: Request, response: Response):
    cookie_name = "sb-" + os.environ.get("SUPABASE_URL").split("https://")[1].split(".")[0] + "-auth-token"
    raw_cookie_header = request.headers.get("cookie", "")

    token_cookie = None
    for cookie in raw_cookie_header.split(";"):
        if cookie_name in cookie:
            token_cookie = cookie.split("=")[1].strip()
            break

    if not token_cookie:
        raise HTTPException(status_code=401, detail="No esta logueado")

    try:
        supabase.auth.sign_out()
        print("loged out")
    except Exception as e:
        print("Error")
    
    response = JSONResponse(content={"message": "Logout exitoso"})

    response.delete_cookie(
        key=cookie_name,
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
    )

    return response


@app.get("/")
def get_all_leaders():
    try:
        response = supabase.table("person").select('id', 'name', 'lastname', 'created_at').eq("is_leader", True).order("lastname").execute()

        if response.data.count == 0:
            return JSONResponse(status_code=404, content={"error": "No se encontró nada en la base de datos"})
        
        return response.data
    except:
        return JSONResponse(status_code=500, content={"error": "Hubo un error en la consulta"})


@app.get("/getall")
def get_all_guests(request: Request):
    token_cookie = None
    for name in request.cookies:
        if "auth-token" in name:
            token_cookie = request.cookies[name]
            break
    
    if token_cookie:
        try:
            response = supabase.table("person").select('*').order("lastname").execute()

            if response.data.count == 0:
                return JSONResponse(status_code=404, content={"error": "No se encontró nada en la base de datos"})
            
            return response.data
        except:
            return JSONResponse(status_code=500, content={"error": "Hubo un error en la consulta"})
    else:
        raise HTTPException(status_code=401, detail="Prohibido")


class Guest(BaseModel):
    name: str
    lastname: str
    menu: str
    role: str
    email: str
    leader: str

roles = ["leader", "companion"]
menus = ["sin_condicion", "vegetariano", "vegano", "celiaco"]

@app.post("/add")
def add_guest(guest: Guest):

    if guest.name == "":
        raise HTTPException(status_code=400, detail="Nombre inválido")
        
    if guest.lastname == "":
        raise HTTPException(status_code=400, detail="Apellido inválido")

    if guest.menu not in menus:
        raise HTTPException(status_code=400, detail="Menú inválido")

    if guest.role not in roles:
        raise HTTPException(status_code=400, detail="Rol inválido")
    

    response = supabase.table("person").select("id").ilike("name", guest.name).ilike("lastname", guest.lastname).execute()

    if response.data:
        raise HTTPException(status_code=400, detail="{} {} ya está registrado".format(guest.name, guest.lastname))
    
    if guest.role == "leader":
        if guest.email == "":
            raise HTTPException(status_code=400, detail="Email inválido")
        
        response = supabase.table("person").select("id").eq("email", guest.email).execute()
        if response.data:
            raise HTTPException(status_code=400, detail="El e-mail ya está registrado. Quizás esta intentando confirmar un acompañante")

        response = supabase.table("person").insert({"name": guest.name, "lastname": guest.lastname, "menu": guest.menu, "email": guest.email, "is_leader": True}).execute()
        print(response.data)
    else:
        if guest.leader == "":
            raise HTTPException(status_code=400, detail="ID de líder inválido")
            
        response = supabase.table("person").select("id").eq("id", guest.leader).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="No se encontró un invitado líder con ese ID")
        
        response = supabase.table("person").insert({"name": guest.name, "lastname": guest.lastname, "menu": guest.menu, "companion_of": guest.leader}).execute()
        print(response.data)

    return JSONResponse(status_code=200, content="¡Confirmado!")


class Group(BaseModel):
    email: str

@app.post("/getgroup")
def get_group(group: Group):
    group_list = []
    if group.email == "":
        raise HTTPException(status_code=400, detail="Email inválido")
    
    response = supabase.table("person").select("*").eq("email", group.email).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="No pudimos encontrar esa direccion de email")

    group_list = [response.data[0]]
    leader_id = response.data[0]["id"]

    response = supabase.table("person").select("*").eq("companion_of", leader_id).execute()

    for member in response.data:
        group_list.append(member)

    return JSONResponse(status_code=200, content=group_list)


class EditGuest(BaseModel):
    id: str
    name: str
    lastname: str
    menu: str

@app.post("/editguest")
def edit_guest(edit_guest: EditGuest, request: Request):
    token_cookie = None
    for name in request.cookies:
        if "auth-token" in name:
            token_cookie = request.cookies[name]
            break

    if not token_cookie:
        raise HTTPException(status_code=401, detail="No tenés permiso")
    
    response = supabase.table("person").update({"name": edit_guest.name, "lastname": edit_guest.lastname, "menu": edit_guest.menu}).eq("id", edit_guest.id).execute()

    print(response)
    return JSONResponse(status_code=200, content="Guardado")



@app.get("/getnumbers")
def get_numbers():
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