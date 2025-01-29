from sqlalchemy import select, update, or_, delete
from sqlalchemy.dialects.postgresql import insert


from service.db_setup.models import User


async def get_some_data(session):
    q = select(User).where(User.id == 1)
    result = await session.execute(q)
    res = result.scalars().all()
    data = [{"username": u.username, "id": u.id} for u in res]
    return data


async def put_some_data(session, data):
    q = (
        insert(User)
        .values(username=data["name"], password=data["password"])
        .on_conflict_do_nothing()
    )

    result = await session.execute(q)
    if result.rowcount:
        return result.returned_defaults[0]  # id
    else:
        return None


async def update_some_data(session, data):
    stmt = (
        update(User)
        .where(
            User.id == data["id"],
            or_(
                User.active == 1,
                User.password.is_(None),
            ),
        )
        .values(**{User.active.key: User.active or data["active"]})
        .returning(User.id)
    )
    result = list(await session.execute(stmt))
    return result


async def delete_some_data(session, data):
    stmt = delete(User).where(User.id == data["id"])
    result = await session.execute(stmt)
    return
