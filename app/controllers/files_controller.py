import os, uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.config.settings import settings as env
from app.config.database import get_db
from app.models.files_model import File as FileModel
from app.models.qr_model import QRCode
from app.models.users_model import User
from werkzeug.utils import secure_filename

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
    file: UploadFile = File(...),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Sube un archivo al servidor."""  
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    if user_id is None:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Usuario no autenticado"})  
    
    # Verificar si se envió un archivo
    contents = file.file.read()
    if not contents:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "No se envió ningún archivo"})
    
    if len(contents) > env.MAX_CONTENT_LENGTH:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "El archivo excede el tamaño máximo permitido"})
    
    # Verificar si la extensión del archivo es permitida
    if not allowed_file(file.filename):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "La extensión del archivo no está permitida"})
    
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
        uploaded_by=user_id
    )
    
    # Guardar el registro en la base de datos
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={
        "msg": "Archivo cargado exitosamente",
        "filename": filename,
        "file_id": file_record.id
    })

# Ruta para obtener un archivo cargado
@router.get("/file/{filename}", status_code=status.HTTP_200_OK)  # /api/v1/file/<filename>
def get_file(
    filename: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Devuelve los detalles de un archivo cargado."""
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    if user_id is None:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Usuario no autenticado"})
    
    # Obtener los claims del JWT
    claims = Authorize.get_raw_jwt()
    user_role = claims.get("role")
    if user_role is None:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Rol no encontrado"})
    
    # Verificar si el archivo existe en la base de datos
    if user_role != "admin":
        file_record = db.query(FileModel).filter_by(
            filename=filename,
            uploaded_by=user_id
        ).first()
    else:
        file_record = db.query(FileModel).filter_by(filename=filename).first()
    
    if not file_record:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Archivo no encontrado"})

    # Verificar si el archivo existe
    if not os.path.exists(file_record.filepath):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Archivo no encontrado en el servidor"})
    
    # Obtener el nombre de quien subio el archivo en la tabla users de la base de datos
    uploaded_by = file_record.uploaded_by
    
    file_data = file_record.to_dict()
    if uploaded_by:
        user_record = db.query(User).get(uploaded_by)
        file_data["uploaded_by"] = {"id": user_record.id, "name": user_record.name, "role": user_record.role} if user_record else "Desconocido"
    
    # Verificar si el archivo tiene un QR asociado
    if file_record.qr_code:
        qr_record = db.query(QRCode).get(file_record.qr_code)
        file_data["qr_code"] = qr_record.filename if qr_record else None

    # En lugar de url_for:
    file_data["url"] = f"/view/file/{file_record.filename}"

    # Servir la URL de acceso al archivo
    return JSONResponse(status_code=status.HTTP_200_OK, content={
        "msg": "Archivo encontrado",
        "file": file_data
    })

# Ruta para descargar un archivo cargado
@router.get("/download/file/{filename}", status_code=status.HTTP_200_OK)  # /api/v1/download/<filename>
def download_file(
    filename: str,
):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)
    
    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Archivo no encontrado"})

    # Enviar el archivo con los encabezados correctos
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)
# Ruta para visualizar un archivo cargado
@router.get("/view/file/{filename}", status_code=status.HTTP_200_OK) # /api/v1/file/<filename>
def view_file(
    filename:str
):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)

    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")        

    # Enviar el archivo con los encabezados correctos
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

# Ruta para listar los archivos subidos
@router.get("/files", status_code=status.HTTP_200_OK) # /api/v1/files
def list_files(
    Autorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Devuelve una lista de archivos subidos."""
    Autorize.jwt_required()
    user_id = Autorize.get_jwt_subject()
    claims = Autorize.get_raw_jwt()
    
    if not user_id:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Usuario no autenticado"})
    
    user_role = claims.get("role")
    if user_role != "admin":
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
    
    if not files:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "No hay archivos disponibles"})
    
    return JSONResponse(status_code=status.HTTP_200_OK, content={
        "msg": "Archivos encontrados",
        "files": files
    })

# Ruta para eliminar un archivo
@router.delete("/delete/file/{filename}", status_code=status.HTTP_200_OK) # /api/v1/delete/file/<filename>
def delete_file(
    filename:str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Elimina un archivo del servidor."""
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    claims = Authorize.get_raw_jwt()
    if user_id is None:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Usuario no autenticado"})
    
    user_role = claims.get("role")
    
    if user_role != "admin":
        file_record = db.query(FileModel).filter_by(filename=filename, uploaded_by=user_id).first()
    else:
        file_record = db.query(FileModel).filter_by(filename=filename).first()
    
    if not file_record:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Archivo no encontrado"})

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

    return JSONResponse(status_code=status.HTTP_200_OK, content={
        "msg": "Archivo eliminado exitosamente",
        "filename": filename
    })

# Ruta para eliminar todos los archivos
@router.delete("/delete/all", status_code=status.HTTP_200_OK) # /api/v1/delete/all
def delete_all_files(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """Elimina todos los archivos del servidor."""
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    claims = Authorize.get_raw_jwt()
    if user_id is None:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Usuario no autenticado"})
    
    user_role = claims.get("role")
    if user_role != "admin":
        files_records = db.query(FileModel).filter_by(uploaded_by=user_id).all()
    else:
        files_records = db.query(FileModel).all()
    
    # Eliminar archivos en la carpeta de subida
    deleted_files = []

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

        deleted_files.append(archivo.filename)
        db.delete(archivo)
        db.commit()
    
    return JSONResponse(status_code=status.HTTP_200_OK, content={
        "msg": "Archivos eliminados exitosamente",
        "deleted_files": deleted_files
    })