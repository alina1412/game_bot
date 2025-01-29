import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_setup.models import User


class DbAccessor:
    def __init__(self, session: AsyncSession):
        self.session = session


class UserAccessor(DbAccessor):

    async def create_user(self, vals: dict) -> int | None:
        try:
            user = User(**vals)
            self.session.add(user)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(user)
        except sa.exc.IntegrityError as exc:
            logger.error("Error adding user: ", exc_info=exc)
            await self.session.rollback()
            return None
        logger.info("added user %s", user.id)
        return user.id

    async def get_user_by_id(self, id_: int) -> User | None:
        return await self.session.get(User, id_)

    def filter_edited_vals(self, edited_vals: dict) -> dict:
        PASWD_MIN_LEN = 3
        user_edit_fields = ("username", "password")
        not_empty_vals = {
            key: val
            for key, val in edited_vals.items()
            if val is not None
            and key in user_edit_fields
            and (len(val) >= PASWD_MIN_LEN if key == "password" else True)
        }
        return not_empty_vals

    async def patch_user_by_id(
        self, id_: int, edited_vals: dict
    ) -> User | None:
        new_vals = self.filter_edited_vals(edited_vals)
        if not new_vals:
            return None
        query_result = await self.session.get(User, id_)
        if not query_result:
            return None
        try:
            for key, value in new_vals.items():
                setattr(query_result, key, value)
            await self.session.flush()
            await self.session.commit()
        except sa.exc.IntegrityError as exc:
            logger.error("Error paching user: ", exc_info=exc)
            await self.session.rollback()
            return None
        return query_result

    async def delete_user(self, id_: int) -> bool:
        query = sa.delete(User).where(User.id == id_)
        result = await self.session.execute(query)
        await self.session.commit()
        return bool(result.rowcount)
