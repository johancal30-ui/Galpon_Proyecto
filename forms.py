from django import forms
from  models import TuModeloDeConsumoForm

class RegistroConsumoForm(forms.ModelForm):
    class Meta:
        model = TuModeloDeConsumoForm
        fields = '__all__' 