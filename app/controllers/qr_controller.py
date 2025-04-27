import os, base64, mimetypes
from io import BytesIO
from PIL import Image
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from qrcode import QRCode as QRCodeGen, constants

from app.config.settings import settings
from app.config.database import get_db
from app.models.qr_model import QRCode
from app.models.files_model import File as FileModel
from app.models.users_model import User
from app.middlewares.auth import auth_user
from app.config.constants import *
from app.schemas.qr_schema import QRCodeSchema

# Crear el router para los códigos QR
router = APIRouter()

# Utilidades
def decode_base64_icon(icon_base64: str):
    try:
        icon_data = base64.b64decode(icon_base64)
        return Image.open(BytesIO(icon_data))
    except Exception as e:
        print(f"Error decodificando icono: {e}")
        return None

def add_icon_to_qr(qr_img, icon_img):
    qr_size = qr_img.size[0]
    icon_size = qr_size // 4
    icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.BOX)
    icon_position = ((qr_size - icon_size) // 2, (qr_size - icon_size) // 2)
    qr_img.paste(icon_img, icon_position, mask=icon_img if icon_img.mode == "RGBA" else None)
    return qr_img

# Ruta para generar un código QR con icono opcional
@router.post("/qr", status_code=status.HTTP_200_OK)  # /api/v1/qr
def generate_qr(
    form_data: QRCodeSchema = Depends(QRCodeSchema.as_form),  # <-- ahora traemos 'text' y 'name' juntos
    icon: UploadFile = File(None),
    userInfo: dict = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """
    Genera un código QR a partir de un texto y lo guarda en la base de datos.
    Si se proporciona un icono, lo agrega al centro del QR.
    """
    # Verificar si el usuario está autenticado
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        filename = f"{form_data.name or form_data.text}.png"
        filename = filename.replace(" ", "_")
        qr_path = os.path.join(settings.QR_FOLDER, filename)
        
        if os.path.exists(qr_path):
            raise HTTPException(status_code=400, detail="QR para ese texto ya fue generado")
        
        # Generar código QR
        qr = QRCodeGen(
            version=5,
            error_correction=constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(form_data.text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        
        if icon:
            icon_img = Image.open(icon.file)
            qr_img = add_icon_to_qr(qr_img, icon_img)

        qr_img.save(qr_path)

        # Guardar en la base de datos
        qr_entry = QRCode(
            filename=filename,
            file_attach=None,  # No se adjunta un archivo
            text=form_data.text,
            filepath=qr_path,
            created_by=user_id
        )
        db.add(qr_entry)
        db.commit()
        db.refresh(qr_entry)

        return {
            "msg": "Código QR generado exitosamente",
            "filename": filename
        }
    except:
        raise HTTPException(status_code=500, detail="Error al generar el código QR")
    finally:
        if icon:
            icon.file.close()

# Ruta para generar un código QR (A partir de un archivo)
@router.post("/qr/file/{filename}", status_code=status.HTTP_200_OK) # /api/v1/qr/file/<filename>
def generate_qr_from_file(
    filename: str,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """
    Genera un código QR a partir de un archivo existente en el servidor.
    El archivo debe estar en la carpeta de archivos subidos.
    """
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    file_record = db.query(FileModel).filter_by(filename=filename).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en la base de datos")

    # Si ya existe un QR, devolver una solicitud exitosa
    qr_path = os.path.join(settings.QR_FOLDER, f"{filename}.png")
    if os.path.exists(qr_path):
        return {"msg": "Código QR ya generado", "filename": f"{filename}.png"}
    
    try:
        file_url = f"{settings.BASE_URL + settings.API_V1_STR}/files/view/{filename}"  # Ajustar ruta real

        qr = QRCodeGen()
        qr.add_data(file_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")
        qr_img.save(qr_path)

        qr_entry = QRCode(
            filename=f"{filename}.png",
            file_attach=file_record.id, # ID del archivo adjunto
            text=file_url,
            filepath=qr_path,
            created_by=user_id
        )
        db.add(qr_entry)
        db.commit()

        file_record = db.query(FileModel).filter_by(filename=filename).first()
        if file_record:
            file_record.qr_code = qr_entry.id
            db.commit()

        return {
            "msg": "Código QR generado exitosamente",
            "filename": f"{filename}.png"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el código QR: {str(e)}")

# Ruta para obtener un código QR
@router.get("/qr/{filename}", status_code=status.HTTP_200_OK) # /api/v1/qr/<filename>
def view_qr(
    filename: str,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """
    Devuelve los datos de un código QR específico.
    Si el usuario es admin, puede ver cualquier QR. De lo contrario, solo los suyos.
    """
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    user_roles = userInfo["roles"]
    if ROLE_ADMIN in user_roles:
        # Si el usuario es admin, puede ver cualquier QR
        qr_record = db.query(QRCode).filter_by(filename=filename).first()
    else:
        qr_record = db.query(QRCode).filter_by(filename=filename, created_by=user_id).first()

    if not qr_record or not os.path.exists(qr_record.filepath):
        raise HTTPException(status_code=404, detail="QR no encontrado")

    user = db.query(User).filter_by(id=qr_record.created_by).first()
    
    data = {
        "filename": qr_record.filename,
        "text": qr_record.text,
        "created_by": user.to_dict() if user else "Desconocido",
        "created_at": qr_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "filepath": qr_record.filepath,
        "url": f"{settings.BASE_URL + settings.API_V1_STR}/view/qr/{qr_record.filename}"
    }
    
    # Si el QR tiene un archivo adjunto, incluirlo en la respuesta
    if qr_record.file_attach:
        file_record = db.query(FileModel).filter_by(id=qr_record.file_attach).first()
        if file_record:
            data["attached_file"] = {
                "filename": file_record.filename,
                "url": f"{settings.BASE_URL + settings.API_V1_STR}/files/view/{file_record.filename}"
            }
        else:
            data["attached_file"] = None
    else:
        data["attached_file"] = None
    
    # Servir la URL de acceso al archivo
    return data

# Ruta para descargar un código QR
@router.get("/download/qr/{filename}", response_class=FileResponse) # /api/v1/download/qr/<filename>
def download_qr(
    filename: str,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """
    Descarga un código QR específico.
    Si el usuario es admin, puede descargar cualquier QR. De lo contrario, solo los suyos.
    """
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    user_roles = userInfo["roles"]
    if ROLE_ADMIN in user_roles:
        # Si el usuario es admin, puede descargar cualquier QR
        qr_record = db.query(QRCode).filter_by(filename=filename).first()
    else:
        qr_record = db.query(QRCode).filter_by(filename=filename, created_by=user_id).first()

    if not qr_record or not os.path.exists(qr_record.filepath):
        raise HTTPException(status_code=404, detail="QR no encontrado")

    # Enviar el archivo con los encabezados correctos
    return FileResponse(
        path=qr_record.filepath,
        filename=qr_record.filename,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={qr_record.filename}"}
    )

# Ruta para visualizar un código QR
@router.get("/view/qr/{filename}", response_class=FileResponse) # /api/v1/view/qr/<filename>
def view_qr_image(filename: str):
    file_path = os.path.join(settings.QR_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="QR no encontrado")
    
    # Detectar el tipo MIME real según la extensión del archivo
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    # Enviar el archivo para visualizarlo
    return FileResponse(path=file_path, media_type=mime_type)

# Ruta para listar los códigos QR generados
@router.get("/qrs", status_code=status.HTTP_200_OK)  # /api/v1/qrs
def list_qrs(
    userInfo: dict = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """
    Lista todos los códigos QR generados por el usuario autenticado.
    Si el usuario es admin, lista todos los códigos QR.
    """
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    user_roles = userInfo["roles"]
    if ROLE_ADMIN not in user_roles:
        # Si el usuario es admin, listar todos los códigos QR
        qr_records = db.query(QRCode).filter_by(created_by=user_id).all()
    else:
        qr_records = db.query(QRCode).all()
    
    # Listar archivos en la carpeta de códigos QR
    files = []
    for qr in qr_records:
        if not os.path.exists(qr.filepath): # Verificar si el archivo existe
            db.delete(qr)
            db.commit()
            continue
        
        files.append(qr.filename)

    data = {
        "msg": "Códigos QR encontrados" if files else "No se encontraron códigos QR",
        "files": files        
    }

    return data

# Ruta para eliminar un código QR
@router.delete("/qr/{filename}", status_code=status.HTTP_200_OK)  # /api/v1/qr/<filename>
def delete_qr(
    filename: str,
    userInfo: dict = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """
    Elimina un código QR específico.
    Si el usuario es admin, puede eliminar cualquier QR. De lo contrario, solo los suyos.
    """
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(settings.QR_FOLDER, filename)):
        raise HTTPException(status_code=404, detail="QR no encontrado")

    # Eliminar el archivo
    os.remove(os.path.join(settings.QR_FOLDER, filename))
    
    # Eliminar el registro de la base de datos
    qr_entry = db.query(QRCode).filter_by(filename=filename).first()
    file_record = db.query(FileModel).filter_by(qr_code=qr_entry.id).first()
    if file_record:
        file_record.qr_code = None
        db.commit()
    
    if qr_entry:
        db.delete(qr_entry)
        db.commit()

    return {
        "msg": "Código QR eliminado exitosamente"
    }

# Ruta para eliminar todos los códigos QR
@router.delete("/qrs", status_code=status.HTTP_200_OK)  # /api/v1/qrs
def delete_all_qrs(
    userInfo: dict = Depends(auth_user([ROLE_ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Elimina todos los códigos QR generados por el usuario autenticado.
    Si el usuario es admin, elimina todos los códigos QR.
    """
    # Verificar si el usuario está autenticado
    user_id = userInfo["id"]
    if user_id is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Listar archivos en la carpeta de códigos QR
    files = os.listdir(settings.QR_FOLDER)

    # Eliminar los códigos QR
    for file in files:
        os.remove(os.path.join(settings.QR_FOLDER, file))
        
        # Eliminar el registro de la base de datos
        qr_entry =  db.query(QRCode).filter_by(filename=file).first()
        file_record = db.query(FileModel).filter_by(qr_code=qr_entry.id).first()
        if file_record:
            file_record.qr_code = None
            db.commit()
        
        if qr_entry:
            db.delete(qr_entry)
            db.commit()

    return {
        "msg": "Todos los códigos QR eliminados exitosamente"
    }