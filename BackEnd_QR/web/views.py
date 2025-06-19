from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'logIn.html')

def register(request):
    return render(request, 'register.html')

def login_exitoso(request):
    return render(request, 'logInExitoso.html')

def user_edit(request):
    return render(request, 'userEdit.html')