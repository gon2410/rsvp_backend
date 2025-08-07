from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from schemas import User, Guest, EditGuest, DeleteGuest, Group, Error
from crud.create import add_guest, report_error
from crud.read import get_guests, get_companions, get_group, get_errors, get_statistics, download_pdf
from crud.update import edit_guest
from crud.delete import delete_guest
from supabase_client import supabase

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

# ---------- CREATE ENDPOINTS ----------

@app.post("/add-guest")
def adding_guest(guest: Guest):
    return add_guest(guest)

@app.post("/report-error")
def reporting_error(error: Error):
    return report_error(error)

# ---------- READ ENDPOINTS -----------

@app.get("/get-guests/{type_of_guest}")
def get_all_guests(type_of_guest: str):
    return get_guests(type_of_guest)

@app.get("/get-companions-of/{id}")
def get_companions_of(id: int):
    return get_companions(id)

@app.post("/get-group")
def get_group_members(group: Group):
    return get_group(group)

@app.get("/get-errors")
def get_all_errors():
    return get_errors()

@app.get("/get-statistics")
def get_all_statistics():
    return get_statistics()

@app.get("/download-pdf")
def get_pdf():
    return download_pdf()

# ---------- UPDATE ENDPOINTS ----------

@app.post("/update-guest")
def editing_guest(edited_guest: EditGuest, request: Request):
    return edit_guest(edited_guest, request)

# ---------- DELETE ENDPOINTS ----------

@app.post("/delete-guest")
def deleting_guest(guest_to_delete: DeleteGuest, request: Request):
    return delete_guest(guest_to_delete, request)