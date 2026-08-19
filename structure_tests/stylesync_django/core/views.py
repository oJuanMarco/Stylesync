from django.shortcuts import render
from django.http import HttpResponse

def ola_mundo(request):
    return HttpResponse("<h1>Ola mundo</h1>")