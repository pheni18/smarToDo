from unittest import TestCase
from nose.tools import eq_
from mock import MagicMock, patch


class DBMock:
    class Model:
        pass

    class Column:
        pass

    class Integer:
        pass
    
    class String:
        pass
    
    class Boolean:
        pass


class TestData:
    class Message:
        get = "g 1"

    class Todo:
        id = 1
        title = "タイトルA"
        complete = True


@patch("linebot.LineBotApi", MagicMock(return_value=None))
@patch("linebot.WebhookHandler", MagicMock(return_value=None))
@patch("flask_sqlalchemy.SQLAlchemy", MagicMock(return_value=DBMock))
class TestSmartodo(TestCase):

    # TODO:
    @patch("app.smartodo.TodoDAO.find_by_id", MagicMock(return_value=TestData.Todo))
    def test_create_reply(self):
        from app.smartodo import create_reply
        # get
        reply = create_reply(TestData.Message.get)
        eq_("get\n"
            f"id: {TestData.Todo.id}, title: {TestData.Todo.title}", reply)
