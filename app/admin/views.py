from starlette_admin.contrib.sqla import Admin, ModelView

from app.database_initializer import engine
from app.database.models.goal import Goal
from app.database.models.story import Story
from app.database.models.user import User


admin = Admin(engine, title="Goals Admin")


admin.add_view(ModelView(User))
admin.add_view(ModelView(Goal))
admin.add_view(ModelView(Story))
