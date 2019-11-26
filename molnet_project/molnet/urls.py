from django.conf.urls import url
from molnet import views

# app_name = 'molnet'
urlpatterns = [
    url(r'^$', views.index, name='index'),
#    url(r'^user_auth/$', views.user_auth, name='user_auth'),
    url(r'^get_data/$', views.get_data, name='get_data'),
#    url(r'^output/$', views.output, name='output')
    ]