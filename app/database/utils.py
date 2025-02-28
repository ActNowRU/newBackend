from sqlalchemy.ext.asyncio import AsyncSession


async def create_model_instance(session: AsyncSession, model, **kwargs):
    instance = model(**kwargs)
    session.add(instance)

    await session.commit()
    await session.refresh(instance)

    return instance


async def update_model_instance(session: AsyncSession, instance, **kwargs):
    for key, value in kwargs.items():
        setattr(instance, key, value)

    session.add(instance)

    await session.commit()
    await session.refresh(instance)

    return instance
