from django.test import SimpleTestCase, Client
from molnet.forms import AnalysisIDForm
from django.core.urlresolvers import reverse
import json
#

class TestForms(SimpleTestCase):
    
    def test_analysis_id_form_valid_data(self):
        form = AnalysisIDForm(data={
            'analysis_id': '1321',
            'similarity_tolerance': '0.1',
            'min_match': '2',
            'k': '10',
            'score_threshold': '0.3',
            'max_shift': '99'
        })
    
        self.assertTrue(form.is_valid())
        
        
    def test_analysis_id_form_no_data(self):
        form = AnalysisIDForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 6)
        
        
        
class TestApi(SimpleTestCase):
    def test_get_api_ms2(self):
        
#    def test_get_api_ms2(self):
#        token = 'e77570ee7f5665c604449ffb4ceba52b06c8603a'
#        host = 'polyomics.mvls.gla.ac.uk'
#        resp = self.APIClient.get(host,{'token':token}, format='json')
#        self.assertValidJSONResponse(resp)        
