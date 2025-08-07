from supabase_client import supabase
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response
from httpx import HTTPError
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def get_guests(type_of_guest):
    if type_of_guest == "leader":
        try:
            response = supabase.table("guests").select("id", "name", "lastname").eq("is_leader", True).order("lastname").execute()
            return response.data
        except:
            raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
    else:
        try:
            response = supabase.table("guests").select("*").order("lastname").execute()

            if response.data.count == 0:
                raise HTTPException(status_code=404, detail="No se encontró nada en la base de datos")
        
            return response.data
        except Exception as e:
            return HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")

def get_companions(id):
    response = supabase.table("guests").select("id", "name", "lastname").eq("companion_of", id).order("lastname").execute()

    return JSONResponse(status_code=200, content=response.data)


def get_group(group):
    group_list = []
    if group.email == "":
        raise HTTPException(status_code=400, detail="Email inválido")
    
    try:
        response = supabase.table("guests").select("*").eq("email", group.email).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="No pudimos encontrar esa direccion de email.")

        group_list = [response.data[0]]
        leader_id = response.data[0]["id"]

        response = supabase.table("guests").select("*").eq("companion_of", leader_id).execute()

        for member in response.data:
            group_list.append(member)

        return JSONResponse(status_code=200, content=group_list)
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos verificar el email. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
    

def get_errors():
    try:
        response = supabase.table("errors").select("id", "name", "lastname", "description").execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No hay errores.")
        return JSONResponse(status_code=200, content=response.data)
    except HTTPError:
        raise HTTPException(status_code=503, detail="No obtener los errores. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
    


def get_statistics():
    try:
        total = supabase.table("guests").select("id", count="exact").execute()

        data = [{"name": "Total", "quantity": total.count}]
        
        return JSONResponse(status_code=200, content=data)
    except HTTPError:
        raise HTTPException(status_code=503, detail="No pudimos obtener las estadisticas. Intente de nuevo.")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Algo salió mal de nuestro lado.")
    
env = Environment(loader=FileSystemLoader("templates"))

def download_pdf():
    response = supabase.table("guests").select("name, lastname").order("lastname").execute()
    data = response.data

    template = env.get_template("listado.html")
    html_renderizado = template.render(invitados=data)
    pdf = HTML(string=html_renderizado).write_pdf()

    return Response(content=pdf, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=listado_de_invitados.pdf"
    })