from django.shortcuts import render, redirect

# Create your views here.

def landing_page(request):
    """
    View function for the landing page of the site.
    """
    return render(request, 'core/landing.html')

def about(request):
    """
    View function for the about page.
    """
    return render(request, 'core/about.html')

def login_redirect(request):
    """
    Redirect to the API token endpoint for login.
    """
    return redirect('/api/token/')

def signup_redirect(request):
    """
    Redirect to the API account registration endpoint.
    """
    return redirect('/api/accounts/register')
