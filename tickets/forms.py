from django import forms
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.contrib.auth.forms import UserCreationForm

from .models import Seguimiento, Ticket, Usuario


class RegistroForm(UserCreationForm):
    """Registro público: siempre crea usuarios con rol Cliente."""

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = Usuario.ROL_CLIENTE
        if commit:
            user.save()
        return user


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'categoria', 'prioridad']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo'].strip()
        if len(titulo) < 5:
            raise forms.ValidationError('El título debe tener al menos 5 caracteres.')
        return titulo

    def clean_descripcion(self):
        descripcion = self.cleaned_data['descripcion'].strip()
        if len(descripcion) < 10:
            raise forms.ValidationError(
                'La descripción debe tener al menos 10 caracteres.'
            )
        return descripcion


class SeguimientoForm(forms.ModelForm):
    class Meta:
        model = Seguimiento
        fields = ['comentario']
        widgets = {
            'comentario': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Escribe un comentario...',
                }
            ),
        }
        labels = {'comentario': 'Comentario'}

    es_interno = forms.BooleanField(
        required=False,
        label='Comentario interno (solo staff)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean_comentario(self):
        comentario = self.cleaned_data['comentario'].strip()
        if len(comentario) < 2:
            raise forms.ValidationError('El comentario es demasiado corto.')
        return comentario


class AsignacionForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['agente']
        widgets = {'agente': forms.Select(attrs={'class': 'form-select'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agente'].queryset = Usuario.objects.filter(
            rol=Usuario.ROL_AGENTE, is_active=True
        )
        self.fields['agente'].required = True


class CierreForm(forms.Form):
    resolucion = forms.CharField(
        label='Resolución',
        min_length=10,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe la solución del problema (mínimo 10 caracteres)...',
            }
        ),
    )

    def clean_resolucion(self):
        resolucion = self.cleaned_data['resolucion'].strip()
        if len(resolucion) < 10:
            raise forms.ValidationError(
                'La resolución debe tener al menos 10 caracteres.'
            )
        return resolucion


class ReaperturaForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo de reapertura',
        min_length=10,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explica por qué se reabre el ticket...',
            }
        ),
    )

    def clean_motivo(self):
        motivo = self.cleaned_data['motivo'].strip()
        if len(motivo) < 10:
            raise forms.ValidationError('El motivo debe tener al menos 10 caracteres.')
        return motivo


class PrioridadForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['prioridad']
        widgets = {'prioridad': forms.Select(attrs={'class': 'form-select'})}


class FiltroTicketsForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Título o descripción'}
        ),
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(Ticket.ESTADOS),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    prioridad = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas')] + list(Ticket.PRIORIDADES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    agente = forms.ModelChoiceField(
        required=False,
        queryset=Usuario.objects.none(),
        empty_label='Todos los agentes',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        mostrar_agente = kwargs.pop('mostrar_agente', False)
        super().__init__(*args, **kwargs)
        if mostrar_agente:
            self.fields['agente'].queryset = Usuario.objects.filter(
                rol=Usuario.ROL_AGENTE, is_active=True
            )
        else:
            del self.fields['agente']


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PasswordChangeForm(BasePasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
