import os, base64
from io import BytesIO
from PIL import Image
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from qrcode import QRCode as QRCodeGen, constants
from app.config.settings import settings as env
from app.config.database import get_db
from app.models.qr_model import QRCode
from app.models.files_model import File as FileModel
from app.models.users_model import User

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
    text: str = Form(...),
    name: str = Form(None),
    icon: UploadFile = File(None),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    """
    Genera un código QR a partir de un texto y lo guarda en la base de datos.
    Si se proporciona un icono, lo agrega al centro del QR.
    """
    # Verificar si el usuario está autenticado
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_identity()
    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Usuario no autenticado"})
    
    try:
        filename = f"{name or text}.png"
        filename = filename.replace(" ", "_")
        qr_path = os.path.join(env.QR_FOLDER, filename)
        
        if os.path.exists(qr_path):
            raise HTTPException(status_code=400, detail="QR para ese texto ya fue generado")
        
        # Generar código QR
        qr = QRCodeGen(
            version=5,
            error_correction=constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        
        if icon:
            icon_img = Image.open(icon.file)
            qr_img = add_icon_to_qr(qr_img, icon_img)

        qr_img.save(qr_path)

        # Guardar en la base de datos
        qr_entry = QRCode(
            filename=filename,
            text=text,
            filepath=qr_path,
            created_by=user_id
        )
        db.add(qr_entry)
        db.commit()
        db.refresh(qr_entry)

        return JSONResponse(status_code=200, content={"msg": "Código QR generado exitosamente", "filename": filename})
    except:
        return JSONResponse(status_code=500, content={"msg": "Error al generar el código QR"})

# Ruta para generar un código QR (A partir de un archivo)
@router.post("/qr/file/{filename}", status_code=status.HTTP_200_OK) # /api/v1/qr/file/<filename>
def generate_qr_from_file(
    filename: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_identity()

    file_path = os.path.join(env.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Si ya existe un QR, devolver una solicitud exitosa
    qr_path = os.path.join(env.QR_FOLDER, f"{filename}.png")
    if os.path.exists(qr_path):
        return JSONResponse(status_code=200, content={"msg": "Código QR ya generado", "filename": f"{filename}.png"})
    
    try:
        file_url = f"{env.BASE_URL}/files/view/{filename}"  # Ajustar ruta real

        qr = QRCodeGen()
        qr.add_data(file_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")
        qr_img.save(qr_path)

        qr_entry = QRCode(
            filename=f"{filename}.png",
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

        return JSONResponse(status_code=200, content={"msg": "Código QR generado exitosamente", "filename": f"{filename}.png"})
    except Exception as e:
        print(f"Error generando QR: {e}")
        
        return JSONResponse(status_code=500, content={"msg": "Error al generar el código QR"})

# Ruta para obtener un código QR
@router.get("/qr/{filename}", status_code=status.HTTP_200_OK) # /api/v1/qr/<filename>
def view_qr(
    filename: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_identity()
    claims = Authorize.get_raw_jwt()
    user_role = claims.get("role", "")

    if user_role == "admin":
        qr_record = db.query(QRCode).filter_by(filename=filename).first()
    else:
        qr_record = db.query(QRCode).filter_by(filename=filename, created_by=user_id).first()

    if not qr_record or not os.path.exists(qr_record.filepath):
        raise HTTPException(status_code=404, detail="QR no encontrado")

    user = db.query(User).filter_by(id=qr_record.created_by).first()
    
    # Servir la URL de acceso al archivo
    return JSONResponse(status_code=200, content={
        "filename": qr_record.filename,
        "text": qr_record.text,
        "created_by": user.to_dict() if user else "Desconocido",
        "created_at": qr_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "filepath": qr_record.filepath
    })

# Ruta para descargar un código QR
@router.get("/download/qr/{filename}", response_class=FileResponse) # /api/v1/download/qr/<filename>
def download_qr(
    filename: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_identity()
    claims = Authorize.get_raw_jwt()
    user_role = claims.get("role", "")

    if user_role == "admin":
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
    path = os.path.join(env.QR_FOLDER, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="QR no encontrado")
    return FileResponse(path, media_type="image/png")

# Ruta para listar los códigos QR generados
@router.get("/qrs", status_code=status.HTTP_200_OK)  # /api/v1/qrs
def list_qrs(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Usuario no autenticado"})
    
    claims = Authorize.get_raw_jwt()
    if not claims:
        return JSONResponse(status_code=401, content={"error": "Token inválido"})
    
    user_role = claims.get("role")
    if user_role != "admin":
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

    if not files:
        return JSONResponse(status_code=404, content={"msg": "No se encontraron códigos QR"})

    return JSONResponse(status_code=200, content={
        "msg": "Códigos QR encontrados",
        "files": files
    })

# Ruta para eliminar un código QR
@router.delete("/qr/{filename}", status_code=status.HTTP_200_OK)  # /api/v1/qr/<filename>
def delete_qr(
    filename: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_identity()
    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Usuario no autenticado"})
    
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.QR_FOLDER, filename)):
        return JSONResponse(status_code=404, content={"msg": "Código QR no encontrado"})

    # Eliminar el archivo
    os.remove(os.path.join(env.QR_FOLDER, filename))
    
    # Eliminar el registro de la base de datos
    qr_entry = db.query(QRCode).filter_by(filename=filename).first()
    file_record = db.query(FileModel).filter_by(qr_code=qr_entry.id).first()
    if file_record:
        file_record.qr_code = None
        db.commit()
    
    if qr_entry:
        db.delete(qr_entry)
        db.commit()

    return JSONResponse(status_code=200, content={"msg": "Código QR eliminado exitosamente"})

# Ruta para eliminar todos los códigos QR
@router.delete("/qrs", status_code=status.HTTP_200_OK)  # /api/v1/qrs
def delete_all_qrs(
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_identity()
    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Usuario no autenticado"})
    
    # Listar archivos en la carpeta de códigos QR
    files = os.listdir(env.QR_FOLDER)

    # Eliminar los códigos QR
    for file in files:
        os.remove(os.path.join(env.QR_FOLDER, file))
        
        # Eliminar el registro de la base de datos
        qr_entry =  db.query(QRCode).filter_by(filename=file).first()
        file_record = db.query(FileModel).filter_by(qr_code=qr_entry.id).first()
        if file_record:
            file_record.qr_code = None
            db.commit()
        
        if qr_entry:
            db.delete(qr_entry)
            db.commit()

    return JSONResponse(status_code=200, content={"msg": "Todos los códigos QR eliminados exitosamente"})