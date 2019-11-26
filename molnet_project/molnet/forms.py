from django import forms

class AnalysisIDForm(forms.Form):
    analysis_id = forms.IntegerField(initial=1321, help_text="Analysis ID")
    similarity_tolerance = forms.FloatField(initial=0.2, help_text="MS2 Tolerance")
    min_match = forms.IntegerField(initial=2, help_text="Min Matches")
    k = forms.IntegerField(initial=10, help_text="Max Number of Neighbour Nodes to One Node")
    score_threshold = forms.FloatField(initial=0.6, help_text="Threshold Score")
    max_shift = forms.IntegerField(initial=100, help_text="Max Connected Component Size")
    
    class Meta:
        fields = ('analysis_id', 'similarity_tolerance', 'min_match', 'k', 'score_threshold', 'max_shift')
        
        
#class UserAuthForm(forms.ModelForm):
#    username = forms.CharField(help_text="PiMP Account Login")
#    password = forms.CharField(widget=forms.PasswordInput())
#    
#    class Meta:
#        fields = ('username', 'password')