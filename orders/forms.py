from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.models import User
from .models import Order, ProcessStep, EmployeeRating
from customers.models import Customer
from employees.models import Employee


class OrderForm(forms.ModelForm):
    # Custom employee choice fields with custom labels (only name and position, no last name)
    assigned_cutter = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Эсгүүрчин"
    )
    assigned_tailor = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Оёдолчин"
    )
    assigned_trouser_maker = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Өмдний оёдолчин"
    )
    assigned_shirt_cutter = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Цамцны эсгүүрчин"
    )
    assigned_shirt_sewer = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Цамцны оёдолчин"
    )
    
    class Meta:
        model = Order
        fields = [
            'customer', 'item_type', 'material_code', 'has_shirt',
            'assigned_tailor', 'assigned_cutter', 'assigned_trouser_maker',
            'assigned_shirt_cutter', 'assigned_shirt_sewer',
            'total_amount', 'advance_amount', 'start_date', 'due_date', 'notes',
            'design_front', 'design_back', 'design_side', 'design_reference'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-control'}),
            'material_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Материалын код'}),
            'has_shirt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'total_amount': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Жишээ: 1,800,000'}),
            'advance_amount': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Жишээ: 500,000'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'design_front': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'design_back': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'design_side': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'design_reference': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Allow selecting from all active employees except managers, ordered by employee type then name
        all_employees = Employee.objects.filter(is_active=True).exclude(employee_type='manager').order_by('employee_type', 'first_name')
        
        # Set queryset and custom label for each employee field
        self.fields['assigned_cutter'].queryset = all_employees
        self.fields['assigned_cutter'].label_from_instance = lambda obj: f"{obj.first_name} ({obj.get_employee_type_display()})"
        
        self.fields['assigned_tailor'].queryset = all_employees
        self.fields['assigned_tailor'].label_from_instance = lambda obj: f"{obj.first_name} ({obj.get_employee_type_display()})"
        
        self.fields['assigned_trouser_maker'].queryset = all_employees
        self.fields['assigned_trouser_maker'].label_from_instance = lambda obj: f"{obj.first_name} ({obj.get_employee_type_display()})"
        
        self.fields['assigned_shirt_cutter'].queryset = all_employees
        self.fields['assigned_shirt_cutter'].label_from_instance = lambda obj: f"{obj.first_name} ({obj.get_employee_type_display()})"
        
        self.fields['assigned_shirt_sewer'].queryset = all_employees
        self.fields['assigned_shirt_sewer'].label_from_instance = lambda obj: f"{obj.first_name} ({obj.get_employee_type_display()})"
        
        # Set default dates
        from datetime import date, timedelta
        from reports.models import SystemSettings
        
        if not self.instance.pk:  # Only for new orders
            # Default start date to today
            self.fields['start_date'].initial = date.today()
            
            # Default due date from settings or 14 days
            days_to_complete = SystemSettings.get_setting('default_order_duration', '14')
            try:
                days = int(days_to_complete)
            except ValueError:
                days = 14
            self.fields['due_date'].initial = date.today() + timedelta(days=days)
            
            # Default total amount from settings
            default_amount = SystemSettings.get_setting('default_order_amount', '100000')
            try:
                self.fields['total_amount'].initial = float(default_amount)
            except ValueError:
                self.fields['total_amount'].initial = 100000
            
            self.fields['advance_amount'].initial = 0
    
    def clean_total_amount(self):
        """Clean and validate total_amount field - remove commas and convert to decimal"""
        value = self.cleaned_data.get('total_amount')
        if value:
            # Remove commas from the formatted number
            if isinstance(value, str):
                value = value.replace(',', '')
            try:
                # Convert to Decimal to validate it's a number
                return Decimal(value)
            except (InvalidOperation, ValueError, TypeError):
                raise forms.ValidationError('Зөвхөн тоо оруулна уу')
        return value
    
    def clean_advance_amount(self):
        """Clean and validate advance_amount field - remove commas and convert to decimal"""
        value = self.cleaned_data.get('advance_amount')
        if value is not None:
            if isinstance(value, str):
                value = value.replace(',', '')
            try:
                return Decimal(value)
            except (InvalidOperation, ValueError, TypeError):
                raise forms.ValidationError('Зөвхөн тоо оруулна уу')
        return Decimal('0')

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_amount') or Decimal('0')
        advance = cleaned_data.get('advance_amount') or Decimal('0')

        if advance < Decimal('0'):
            self.add_error('advance_amount', 'Урьдчилгаа дүн 0-ээс бага байж болохгүй.')

        if advance > total and advance != Decimal('0'):
            self.add_error('advance_amount', 'Урьдчилгаа дүн нийт дүнгээс их байж болохгүй.')

        return cleaned_data


class ProcessStepForm(forms.ModelForm):
    class Meta:
        model = ProcessStep
        fields = ['step_type', 'title', 'description', 'status']
        widgets = {
            'step_type': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class EmployeeRatingForm(forms.ModelForm):
    class Meta:
        model = EmployeeRating
        fields = ['employee', 'rating', 'comment']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'step': 1}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
