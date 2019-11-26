from django.shortcuts import render, render_to_response
#from django.http import HttpResponse, HttepResponseRedirect
from django.urls import reverse

from molnet.forms import AnalysisIDForm
#from molnet.models import AnalysisID
from molnet.data_api import view

from bokeh.resources import INLINE, CDN


resources = INLINE.render()


def index(request):
    response = render(request, 'molnet/index.html', {})
    return response


def get_data(request):
    if request.method == 'POST':
        analysis_form = AnalysisIDForm(request.POST)
        
        if analysis_form.is_valid():
            a_id = analysis_form.cleaned_data['analysis_id']
            similarity_tolerance = analysis_form.cleaned_data['similarity_tolerance']
            min_match = analysis_form.cleaned_data['min_match']
            k = analysis_form.cleaned_data['k']
            score_threshold = analysis_form.cleaned_data['score_threshold']
            max_shift = analysis_form.cleaned_data['max_shift']
            mc = 1
            
            m_networks, hit_list, script = view(a_id, similarity_tolerance, min_match, score_threshold, k, mc, max_shift) 
    
            r = render_to_response('molnet/output.html', {'script':script, 'm_networks':m_networks, 'resources':resources}) 
            
            return r
            
    else:
        analysis_form = AnalysisIDForm()
    
    response = render(request, 'molnet/get_data.html', {'form': analysis_form})
    
    return response

    


#def user_auth(request):
#    if request.method == 'POST':
#        user_form = UserAuthForm(request.POST)
#        
#        if user_form.is_valid():
#            username = user_form.cleaned_data['analysis_id']
#            password = user_form.cleaned_data['password']
#            
#            return render_to_response('molnet/get_data.html', {'username':username, 'password':password})
#        else:
#            user_form = UserAuthForm()
#            
#        response = render(request, 'molnet/user_auth.html', {'form': user_form})
#        return response