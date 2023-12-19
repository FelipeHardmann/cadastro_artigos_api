from typing import List

from fastapi import (
    APIRouter,
    Depends,
    status,
    Response,
    HTTPException
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from models.usuario_model import UsuarioModel
from schemas.usuario_schema import (
    UsuarioSchemaBase,
    UsuarioSchemaCreate,
    UsuarioSchemaUp,
    UsuarioSchemaArtigos
)
from core.deps import get_current_user, get_session
from core.security import gerar_hash_senha
from core.auth import autenticar, criar_token_acesso


router = APIRouter()


# GET logado
@router.get(
    '/logado',
    response_model=UsuarioSchemaBase
)
def get_logado(usuario_logado: UsuarioModel = Depends(get_current_user)):
    return usuario_logado


# Criar conta
@router.post(
    '/signup',
    status_code=status.HTTP_201_CREATED,
    response_model=UsuarioSchemaBase
)
async def post_usuario(
    usuario: UsuarioSchemaCreate, db: AsyncSession = Depends(get_session)
):
    novo_usuario: UsuarioModel = UsuarioModel(
        nome=usuario.nome,
        sobrenome=usuario.sobrenome,
        email=usuario.email,
        senha=gerar_hash_senha(usuario.senha),
        is_admin=usuario.is_admin
    )
    async with db as session:
        try:

            session.add(novo_usuario)
            await session.commit()
            return novo_usuario
        except IntegrityError:
            raise HTTPException(
                detail='Esse email já está cadastrado',
                status_code=status.HTTP_406_NOT_ACCEPTABLE
            )


# Get Usuarios
@router.get(
    '/',
    response_model=List[UsuarioSchemaArtigos]
)
async def get_usuarios(db: AsyncSession = Depends(get_session)):
    async with db as session:
        query = select(UsuarioModel)
        result = await session.execute(query)
        usuarios: List[UsuarioSchemaArtigos] = result.scalars().unique().all()

        return usuarios


# Get Usuario
@router.get(
    '/{id_usuario}',
    response_model=UsuarioSchemaArtigos
)
async def get_usuario(id_usuario: int, db: AsyncSession = Depends(get_session)):
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.id == id_usuario)
        result = await session.execute(query)
        usuario: UsuarioSchemaArtigos = result.scalars().unique().one_or_none()

        if usuario:
            return usuario
        raise HTTPException(
            detail='Usuário não encontrado',
            status_code=status.HTTP_404_NOT_FOUND
        )


# Put usuário
@router.put(
    '/{id_usuario}',
    response_model=UsuarioSchemaBase,
    status_code=status.HTTP_202_ACCEPTED
)
async def put_usuario(
    id_usuario: int,
    usuario: UsuarioSchemaUp,
    db: AsyncSession = Depends(get_session)
):
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.id == id_usuario)
        result = await session.execute(query)
        usuario_up: UsuarioSchemaBase = result.scalars().unique().one_or_none()

        if usuario_up:
            if usuario.nome:
                usuario_up.nome = usuario.nome
            if usuario.email:
                usuario_up.email = usuario.email
            if usuario.sobrenome:
                usuario_up.sobrenome = usuario.sobrenome
            if usuario.is_admin:
                usuario_up.is_admin = usuario.is_admin
            if usuario.senha:
                usuario_up.senha = gerar_hash_senha(usuario.senha)

            return usuario_up

        raise HTTPException(
            detail='Usuário não encontrado',
            status_code=status.HTTP_404_NOT_FOUND
        )


# Delete usuário
@router.delete(
    '/{id_usuario}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_usuario(
    id_usuario: int,
    db: AsyncSession = Depends(get_session)
):
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.id == id_usuario)
        result = await session.execute(query)
        usuario_del: UsuarioSchemaArtigos = result.scalars().unique().one_or_none()

        if usuario_del:
            await session.delete(usuario_del)
            await session.commit()

            return Response(
                status_code=status.HTTP_204_NO_CONTENT
            )
        raise HTTPException(
            detail='Usuário não encontrado',
            status_code=status.HTTP_404_NOT_FOUND
        )


# Post Login
@router.post('/login')
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    usuario = await autenticar(
        email=form_data.username,
        senha=form_data.password,
        db=db
    )

    if not usuario:
        raise HTTPException(
            detail='Dados de acesso incorretos',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return JSONResponse(
        content={
            "acess_token": criar_token_acesso(sub=str(usuario.id)),
            "token_type": "bearer"
        },
        status_code=status.HTTP_200_OK
    )
