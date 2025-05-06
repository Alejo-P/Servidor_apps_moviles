import os, uuid, base64, mimetypes
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from app.config.settings import settings as env
from app.config.database import get_db
from app.models.files_model import File as FileModel
from app.models.qr_model import QRCode
from app.models.users_model import User
from app.middlewares.auth import auth_user
from app.config.constants import *
from app.schemas.upload_file_schema import UploadFileSchema
from app.config.settings import settings

# Crear el router
router = APIRouter()

# Función para verificar la extensión del archivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in env.ALLOWED_EXTENSIONS

# Función para generar un nombre único
def get_unique_filename(filename):
    """Genera un nombre único para evitar conflictos."""
    name, ext = os.path.splitext(filename)
    return f"{name}_{uuid.uuid4().hex[:8]}{ext}"

# Ruta para subir archivos
@router.post("/upload", status_code=status.HTTP_201_CREATED) # /api/v1/upload
def upload_file(
    file: UploadFileSchema,
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """Sube un archivo al servidor."""  
    # Verificar si se envió un archivo
    if not file:
        raise HTTPException(status_code=400, detail="No se envió ningún archivo")
    
    if file.size > env.MAX_CONTENT_LENGTH:
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande")
    
    # Verificar si el archivo tiene un nombre
    if not file.filename:
        raise HTTPException(status_code=400, detail="El archivo no tiene un nombre")
    
    # Verificar si la extensión del archivo es permitida
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(env.UPLOAD_FOLDER, filename)
    
    # Comprobar si el archivo ya existe
    if os.path.exists(filepath):
        filename = get_unique_filename(filename)
        filepath = os.path.join(env.UPLOAD_FOLDER, filename)
        
    # Guardar el archivo en el servidor
    with open(filepath, "wb") as f:
        f.write(
            base64.b64decode(file.filebase64) if file.filebase64 else file.file.read()
        )
    
    # Crear un registro en la base de datos
    file_record = FileModel(
        filename=filename,
        filepath=filepath,
        file_size=file.size,
        file_type=file.filetype if file.filetype else "application/octet-stream",
        uploaded_by=userInfo.id,
    )
    
    # Guardar el registro en la base de datos
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    
    return {
        "msg": "Archivo cargado exitosamente",
        "filename": filename,
        "file_id": file_record.id
    }

# Ruta para subir archivos (sin base64 y con multipart/form-data)
@router.post("/upload-formdata", status_code=status.HTTP_201_CREATED) # /api/v1/upload-formdata
def upload_form(
    file: UploadFile = File(...),
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """Sube un archivo al servidor."""      
    # Verificar si se envió un archivo
    contents = file.file.read()
    file.file.close()
    if not contents:
        raise HTTPException(status_code=400, detail="No se envió ningún archivo")
    
    if len(contents) > env.MAX_CONTENT_LENGTH:
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande")
    
    # Verificar si el archivo tiene un nombre
    if not file.filename:
        raise HTTPException(status_code=400, detail="El archivo no tiene un nombre")
    
    # Verificar si la extensión del archivo es permitida
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(env.UPLOAD_FOLDER, filename)
    
    # Comprobar si el archivo ya existe
    if os.path.exists(filepath):
        filename = get_unique_filename(filename)
        filepath = os.path.join(env.UPLOAD_FOLDER, filename)
        
    # Guardar el archivo en el servidor
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Crear un registro en la base de datos
    file_record = FileModel(
        filename=filename,
        filepath=filepath,
        file_size=len(contents),
        file_type=file.content_type if file.content_type else "application/octet-stream",
        uploaded_by=userInfo.id,
    )
    
    # Guardar el registro en la base de datos
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    
    return {
        "msg": "Archivo cargado exitosamente",
        "filename": filename,
        "file_id": file_record.id
    }

# Ruta para obtener un archivo cargado
@router.get("/file/{filename}", status_code=status.HTTP_200_OK)  # /api/v1/file/<filename>
def get_file(
    filename: str,
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """Devuelve los detalles de un archivo cargado."""
    user_id = userInfo.id
    user_roles = [role.name for role in userInfo.roles]
    # Verificar si el archivo existe en la base de datos
    if ROLE_ADMIN not in user_roles:
        # Si el usuario no es admin, filtrar por el ID del usuario
        file_record = db.query(FileModel).filter_by(
            filename=filename,
            uploaded_by=user_id
        ).first()
    else:
        file_record = db.query(FileModel).filter_by(filename=filename).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en la base de datos")

    # Verificar si el archivo existe
    if not os.path.exists(file_record.filepath):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    
    # Obtener el nombre de quien subio el archivo en la tabla users de la base de datos
    uploaded_by = file_record.uploaded_by
    
    file_data = file_record.to_dict()
    if uploaded_by:
        user_record = db.query(User).get(uploaded_by)
        file_data["uploaded_by"] = {
            "id": user_record.id,
            "name": user_record.name,
            "roles": [role.name for role in user_record.roles],
            "is_active": user_record.is_active
        } if user_record else "Desconocido"
    
    # Verificar si el archivo tiene un QR asociado
    if file_record.qr_code:
        qr_record = db.query(QRCode).get(file_record.qr_code)
        file_data["qr_code"] = qr_record.filename if qr_record else None

    # En lugar de url_for:
    file_data["url"] = f"{settings.BASE_URL + settings.API_V1_STR}/view/file/{file_record.filename}"

    # Servir la URL de acceso al archivo
    return {
        "msg": "Archivo encontrado",
        "file": file_data
    }

# Ruta para descargar un archivo cargado
@router.get("/download/file/{filename}", status_code=status.HTTP_200_OK)  # /api/v1/download/<filename>
def download_file(
    filename: str,
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER]))
):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)
    
    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Enviar el archivo con los encabezados correctos
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

# Ruta para visualizar un archivo cargado
@router.get("/view/file/{filename}", status_code=status.HTTP_200_OK) # /api/v1/file/<filename>
def view_file(
    filename: str,
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Detectar el tipo MIME real según la extensión del archivo
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    # Enviar el archivo para visualizarlo
    return FileResponse(path=file_path, media_type=mime_type)

# Ruta para listar los archivos subidos
@router.get("/files", status_code=status.HTTP_200_OK) # /api/v1/files
def list_files(
    userInfo: User = Depends(auth_user([ROLE_ALL])),
    db: Session = Depends(get_db)
):
    """Devuelve una lista de archivos subidos."""
    user_id = userInfo.id
    
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN not in user_roles:
        # Si el usuario no es admin, filtrar por el ID del usuario
        files_records = db.query(FileModel).filter_by(uploaded_by=user_id).all()
    else:
        files_records = db.query(FileModel).all()
        
    files = []
    for archivo in files_records:
        if not os.path.exists(archivo.filepath): # Verificar si el archivo existe
            db.delete(archivo)
            db.commit()
            continue
        
        files.append(archivo.filename)
    
    data ={
        "msg": "Archivos encontrados" if files else "No se encontraron archivos",
        "files": files
    }
    
    return data

# Ruta para eliminar un archivo
@router.delete("/delete/file/{filename}", status_code=status.HTTP_200_OK) # /api/v1/delete/file/<filename>
def delete_file(
    filename:str,
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """Elimina un archivo del servidor."""
    user_id = userInfo.id
    
    user_roles = [role.name for role in userInfo.roles]
    if ROLE_ADMIN not in user_roles:
        # Si el usuario no es admin, filtrar por el ID del usuario
        file_record = db.query(FileModel).filter_by(filename=filename, uploaded_by=user_id).first()
    else:
        file_record = db.query(FileModel).filter_by(filename=filename).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en la base de datos")

    # Eliminar el archivo físico
    if os.path.exists(file_record.filepath):
        os.remove(file_record.filepath)

    # Eliminar QR asociado
    if file_record.qr_code:
        qr_record = db.query(QRCode).get(file_record.qr_code)
        if qr_record:
            if os.path.exists(qr_record.filename):
                os.remove(qr_record.filename)
            db.delete(qr_record)
            db.commit()

    db.delete(file_record)
    db.commit()

    return {
        "msg": "Archivo eliminado exitosamente",
        "filename": filename
    }

# Ruta para eliminar todos los archivos
@router.delete("/delete/all", status_code=status.HTTP_200_OK) # /api/v1/delete/all
def delete_all_files(
    userInfo: User = Depends(auth_user([ROLE_ADMIN, ROLE_USER])),
    db: Session = Depends(get_db)
):
    """Elimina todos los archivos del servidor."""
    user_id = userInfo.id
    
    user_roles = [role.name for role in userInfo.roles]
    # Verificar si el usuario es admin o no
    if ROLE_ADMIN not in user_roles:
        files_records = db.query(FileModel).filter_by(uploaded_by=user_id).all()
    else:
        files_records = db.query(FileModel).all()
    
    # Eliminar archivos en la carpeta de subidas
    if not files_records:
        raise HTTPException(status_code=404, detail="No se encontraron archivos para eliminar")
    
    for archivo in files_records:
        if os.path.exists(archivo.filepath):
            os.remove(archivo.filepath)
        
        if archivo.qr_code:
            qr_record = db.query(QRCode).get(archivo.qr_code)
            if qr_record:
                if os.path.exists(qr_record.filename):
                    os.remove(qr_record.filename)
                db.delete(qr_record)
                db.commit()

        db.delete(archivo)
        db.commit()
    
    return {
        "msg": "Archivos eliminados exitosamente"
    }