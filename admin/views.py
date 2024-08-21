from sqladmin import Admin
from sqladmin import ModelView
from sqlalchemy import inspect

from database_initializer import engine
from main import app
from services.database.models.goal import Goal
from services.database.models.story import Story
from services.database.models.user import User

admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]
    column_details_exclude_list = [User.hashed_password]
    can_delete = False


class GoalAdmin(ModelView):
    model = Goal
    column_list = [
                      c_attr.key for c_attr in inspect(Goal).mapper.column_attrs
                  ] + Goal.owner


class StoryAdmin(ModelView):
    model = Story
    column_list = [
                      c_attr.key for c_attr in inspect(Story).mapper.column_attrs
                  ] + Story.owner


admin.add_view(UserAdmin)
admin.add_view(GoalAdmin)
admin.add_view(StoryAdmin)
