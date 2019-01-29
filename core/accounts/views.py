from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from .forms import UserCreationForm


class SignUp(FormView):
    form_class = UserCreationForm
    fields = ["email", "password"]
    success_url = reverse_lazy("login")
    template_name = "accounts/signup.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        form.send_email()
        self.object.save()

        return super().form_valid(form)

