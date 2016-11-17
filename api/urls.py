from api import views
from api.utils.common import Url


urlpatterns = [
    Url('/yardstick/test/action', views.Test, 'test')
]
