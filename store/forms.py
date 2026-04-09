from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Product, User


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            if field.widget.__class__.__name__ in ("Select", "SelectMultiple"):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER
        if commit:
            user.save()
        return user


class StaffRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            if field.widget.__class__.__name__ in ("Select", "SelectMultiple"):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STAFF
        if commit:
            user.save()
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "price")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
        }


class AddToBasketForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )


class StaffCustomerSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={"placeholder": "Username or email", "class": "form-control"},
        ),
    )
