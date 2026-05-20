#!/usr/bin/env python3
"""Generate model, schema, service, and CRUD route files for a resource.

Usage examples:
  /usr/local/bin/python3 scripts/generate_crud.py Category
  /usr/local/bin/python3 scripts/generate_crud.py Product --fields name:str:120 price:float description:str?:300
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
ROUTES_DIR = APP_DIR / "routes"


@dataclass
class FieldSpec:
    name: str
    type_name: str
    optional: bool
    max_length: int | None


def to_snake(name: str) -> str:
    step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    step2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1)
    return step2.replace("-", "_").lower()


def to_pascal(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def pluralize(word: str) -> str:
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return f"{word[:-1]}ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return f"{word}es"
    return f"{word}s"


def parse_field(spec: str) -> FieldSpec:
    # Format: name:type[:max_length], optional with type? e.g. description:str?:300
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid field spec '{spec}'. Use name:type[:max_length].")

    field_name = parts[0].strip()
    raw_type = parts[1].strip()
    optional = raw_type.endswith("?")
    type_name = raw_type[:-1] if optional else raw_type

    if type_name not in {"str", "int", "float", "bool"}:
        raise ValueError(f"Unsupported type '{type_name}' in '{spec}'.")

    max_length: int | None = None
    if len(parts) >= 3 and parts[2].strip():
        max_length = int(parts[2].strip())

    if type_name == "str" and max_length is None:
        max_length = 255

    return FieldSpec(name=field_name, type_name=type_name, optional=optional, max_length=max_length)


def py_type(field: FieldSpec, make_optional: bool = False) -> str:
    base = {"str": "str", "int": "int", "float": "float", "bool": "bool"}[field.type_name]
    optional = make_optional or field.optional
    return f"{base} | None" if optional else base


def sql_type_expr(field: FieldSpec) -> str:
    if field.type_name == "str":
        return f"String({field.max_length})"
    if field.type_name == "int":
        return "Integer()"
    if field.type_name == "float":
        return "Float()"
    return "Boolean()"


def pydantic_field(field: FieldSpec, mode: str) -> str:
    # mode in {create, update}
    is_optional = mode == "update" or field.optional
    annotation = py_type(field, make_optional=(mode == "update"))

    if field.type_name == "str":
        max_len = field.max_length or 255
        if is_optional:
            return f"    {field.name}: {annotation} = Field(default=None, max_length={max_len})"
        return f"    {field.name}: {annotation} = Field(min_length=1, max_length={max_len})"

    if is_optional:
        return f"    {field.name}: {annotation} = None"
    return f"    {field.name}: {annotation}"


def build_model_file(class_name: str, table_name: str, fields: list[FieldSpec]) -> str:
    sql_types = {"String"}
    for field in fields:
        if field.type_name == "int":
            sql_types.add("Integer")
        elif field.type_name == "float":
            sql_types.add("Float")
        elif field.type_name == "bool":
            sql_types.add("Boolean")
        else:
            sql_types.add("String")

    imports = ", ".join(sorted(sql_types))

    lines = [
        f"from sqlalchemy import {imports}",
        "from sqlalchemy.orm import Mapped, mapped_column",
        "",
        "from .db import Base",
        "",
        "",
        f"class {class_name}(Base):",
        f"    __tablename__ = \"{table_name}\"",
        "",
        "    id: Mapped[int] = mapped_column(primary_key=True)",
    ]

    for field in fields:
        annotation = py_type(field)
        nullable = "True" if field.optional else "False"
        lines.append(
            f"    {field.name}: Mapped[{annotation}] = mapped_column({sql_type_expr(field)}, nullable={nullable})"
        )

    lines.append("")
    return "\n".join(lines)


def build_schema_file(class_name: str, fields: list[FieldSpec]) -> str:
    lines = [
        "from pydantic import BaseModel, ConfigDict, Field",
        "",
        "",
        f"class {class_name}Create(BaseModel):",
    ]

    for field in fields:
        lines.append(pydantic_field(field, mode="create"))

    lines.extend(["", "", f"class {class_name}Update(BaseModel):"])

    for field in fields:
        lines.append(pydantic_field(field, mode="update"))

    lines.extend([
        "",
        "",
        f"class {class_name}Read({class_name}Create):",
        "    id: int",
        "    model_config = ConfigDict(from_attributes=True)",
        "",
    ])

    return "\n".join(lines)


def build_service_file(class_name: str, snake: str, fields: list[FieldSpec]) -> str:
    field_names = [f.name for f in fields]

    lines = [
        "from sqlalchemy import select",
        "from sqlalchemy.orm import Session",
        "",
        f"from .models_{snake} import {class_name}",
        f"from .schemas_{snake} import {class_name}Create, {class_name}Read, {class_name}Update",
        "",
        "",
        f"class {class_name}NotFoundError(Exception):",
        "    pass",
        "",
        "",
        f"class {class_name}Service:",
        f"    def list_{pluralize(snake)}(self, db: Session) -> list[{class_name}Read]:",
        f"        rows = db.execute(select({class_name}).order_by({class_name}.id)).scalars().all()",
        f"        return [{class_name}Read.model_validate(row) for row in rows]",
        "",
        f"    def get_{snake}(self, db: Session, item_id: int) -> {class_name}Read:",
        f"        row = db.get({class_name}, item_id)",
        "        if row is None:",
        f"            raise {class_name}NotFoundError",
        f"        return {class_name}Read.model_validate(row)",
        "",
        f"    def create_{snake}(self, db: Session, payload: {class_name}Create) -> {class_name}Read:",
        f"        row = {class_name}(**payload.model_dump())",
        "        db.add(row)",
        "        db.commit()",
        "        db.refresh(row)",
        f"        return {class_name}Read.model_validate(row)",
        "",
        f"    def update_{snake}(self, db: Session, item_id: int, payload: {class_name}Update) -> {class_name}Read:",
        f"        row = db.get({class_name}, item_id)",
        "        if row is None:",
        f"            raise {class_name}NotFoundError",
        "",
        "        changes = payload.model_dump(exclude_unset=True)",
    ]

    for field_name in field_names:
        lines.extend([
            f"        if \"{field_name}\" in changes:",
            f"            row.{field_name} = changes[\"{field_name}\"]",
        ])

    lines.extend([
        "",
        "        db.commit()",
        "        db.refresh(row)",
        f"        return {class_name}Read.model_validate(row)",
        "",
        f"    def delete_{snake}(self, db: Session, item_id: int) -> None:",
        f"        row = db.get({class_name}, item_id)",
        "        if row is None:",
        f"            raise {class_name}NotFoundError",
        "",
        "        db.delete(row)",
        "        db.commit()",
        "",
        "",
        f"{snake}_service = {class_name}Service()",
        "",
    ])

    return "\n".join(lines)


def build_route_file(class_name: str, snake: str, plural: str) -> str:
    return "\n".join([
        "from fastapi import APIRouter, Depends, HTTPException, status",
        "from sqlalchemy.orm import Session",
        "",
        "from ..db import get_db",
        f"from ..schemas_{snake} import {class_name}Create, {class_name}Read, {class_name}Update",
        f"from ..services_{snake} import {class_name}NotFoundError, {snake}_service",
        "",
        f"router = APIRouter(prefix=\"/{plural}\", tags=[\"{plural}\"])",
        "",
        "",
        f"@router.get(\"\", response_model=list[{class_name}Read])",
        f"def list_{plural}(db: Session = Depends(get_db)) -> list[{class_name}Read]:",
        f"    return {snake}_service.list_{plural}(db)",
        "",
        "",
        f"@router.get(\"/{{item_id}}\", response_model={class_name}Read)",
        f"def get_{snake}(item_id: int, db: Session = Depends(get_db)) -> {class_name}Read:",
        "    try:",
        f"        return {snake}_service.get_{snake}(db, item_id)",
        f"    except {class_name}NotFoundError as exc:",
        f"        raise HTTPException(status_code=404, detail=\"{class_name} not found\") from exc",
        "",
        "",
        f"@router.post(\"\", response_model={class_name}Read, status_code=status.HTTP_201_CREATED)",
        f"def create_{snake}(payload: {class_name}Create, db: Session = Depends(get_db)) -> {class_name}Read:",
        f"    return {snake}_service.create_{snake}(db, payload)",
        "",
        "",
        f"@router.put(\"/{{item_id}}\", response_model={class_name}Read)",
        f"def update_{snake}(item_id: int, payload: {class_name}Update, db: Session = Depends(get_db)) -> {class_name}Read:",
        "    try:",
        f"        return {snake}_service.update_{snake}(db, item_id, payload)",
        f"    except {class_name}NotFoundError as exc:",
        f"        raise HTTPException(status_code=404, detail=\"{class_name} not found\") from exc",
        "",
        "",
        "@router.delete(\"/{item_id}\", status_code=status.HTTP_204_NO_CONTENT)",
        f"def delete_{snake}(item_id: int, db: Session = Depends(get_db)) -> None:",
        "    try:",
        f"        {snake}_service.delete_{snake}(db, item_id)",
        f"    except {class_name}NotFoundError as exc:",
        f"        raise HTTPException(status_code=404, detail=\"{class_name} not found\") from exc",
        "",
    ])


def update_main_py(route_module: str, router_var: str) -> None:
    main_path = APP_DIR / "main.py"
    content = main_path.read_text()

    import_line = f"from .routes.{route_module} import router as {router_var}"
    include_line = f"app.include_router({router_var})"

    if import_line not in content:
        lines = content.splitlines()
        insert_index = 0
        for idx, line in enumerate(lines):
            if line.startswith("from .routes"):
                insert_index = idx + 1
        lines.insert(insert_index, import_line)
        content = "\n".join(lines) + "\n"

    if include_line not in content:
        lines = content.splitlines()
        insert_index = len(lines)
        for idx, line in enumerate(lines):
            if line.startswith("app.include_router("):
                insert_index = idx + 1
        lines.insert(insert_index, include_line)
        content = "\n".join(lines) + "\n"

    main_path.write_text(content)


def write_new_file(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate model + full CRUD route files.")
    parser.add_argument("entity", help="Entity name, e.g. Category or blog_post")
    parser.add_argument(
        "--fields",
        nargs="*",
        default=["name:str:100", "description:str?:300"],
        help="Field specs like name:str:120 price:float active:bool description:str?:300",
    )
    args = parser.parse_args()

    class_name = to_pascal(args.entity)
    snake = to_snake(args.entity)
    plural = pluralize(snake)
    table_name = plural

    fields = [parse_field(item) for item in args.fields]

    model_path = APP_DIR / f"models_{snake}.py"
    schema_path = APP_DIR / f"schemas_{snake}.py"
    service_path = APP_DIR / f"services_{snake}.py"
    route_path = ROUTES_DIR / f"{plural}.py"

    write_new_file(model_path, build_model_file(class_name, table_name, fields))
    write_new_file(schema_path, build_schema_file(class_name, fields))
    write_new_file(service_path, build_service_file(class_name, snake, fields))
    write_new_file(route_path, build_route_file(class_name, snake, plural))

    update_main_py(route_module=plural, router_var=f"{plural}_router")

    print("Generated:")
    print(f"- {model_path.relative_to(PROJECT_ROOT)}")
    print(f"- {schema_path.relative_to(PROJECT_ROOT)}")
    print(f"- {service_path.relative_to(PROJECT_ROOT)}")
    print(f"- {route_path.relative_to(PROJECT_ROOT)}")
    print("Updated: app/main.py")
    print("Next steps:")
    print(f"- alembic revision --autogenerate -m 'create {table_name} table'")
    print("- alembic upgrade head")


if __name__ == "__main__":
    main()
