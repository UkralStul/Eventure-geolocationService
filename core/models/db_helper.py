from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


from core.config import settings


class DbHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )


db_helper = DbHelper(
    url=settings.db_url,
    echo=settings.echo,
)
