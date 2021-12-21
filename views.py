from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json

from .models import User, Post


class PostForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={'rows':'4', 'cols':'150', 'id':'input-area'}), label='New Post', required=True)

#@login_required
def index(request):
    return render(request, "network/index.html", {'post_form': PostForm().as_table()})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


@login_required
def load_posts(request, scope):

    # Filter emails returned based on mailbox
    if scope == 'all':
        posts = Post.objects.all()
    elif scope == "following":
        posts = Post.objects.filter(user__in=request.user.following.all())
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)

    # Return emails in reverse chronologial order
    posts = posts.order_by("-timestamp").all()
    return JsonResponse([post.serialize(request.user) for post in posts], safe=False)


@login_required
@csrf_exempt
def new_post(request):

    # Composing a new email must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Get contents of email
    data = json.loads(request.body)
    content = data.get("body", "")
    post = Post(user=request.user, content=content)
    post.save()
    return JsonResponse({"message": "Posted successfully."}, status=201)

@login_required
@csrf_exempt
def like_post(request, post_id):
    if request.method == "GET":
        post = Post.objects.get(pk=post_id)
        user = request.user
        if post.liked(user):
            post.likers.remove(user)
        else:
            post.likers.add(user)

        return HttpResponse(status=204)
    

@login_required
@csrf_exempt
def follow_user(request, user):
    if request.method == "GET":
        target_user = User.objects.get(username=user)
        iam = request.user
        if target_user ==  iam:
            pass
        else:
            if target_user.followed_by(iam):
                target_user.followers.remove(iam)
                return JsonResponse({"message": f"You unfollowed {target_user.username}."}, status=204)
            else:
                target_user.followers.add(iam)
                return JsonResponse({"message": f"You unfollowed {target_user.username}."}, status=204)
    else:
        return HttpResponse(status=403)

        
#-----------------smile---------------
import QuantLib as ql

today = ql.Date().todaysDate()
dayCounter = ql.Actual365Fixed()
maturity = [today + ql.Period('3M'), today + ql.Period('6M')]
deltas = [-0.9, -0.75, -0.5, -0.25, -0.1]
vols = [[0.04, 0.03, 0.032, 0.035, 0.05], [0.042,0.031,0.0315,0.033,0.06]]

import numpy as np 

k = 6.517025874832917
spot = 6.5
rd, rf = 0.025, 0.01
ratesTs = ql.YieldTermStructureHandle(ql.FlatForward(today, rd, dayCounter))
dividendTs = ql.YieldTermStructureHandle(ql.FlatForward(today, rf, dayCounter))

class TargetFun:
    strike = None
    rTs = None
    maturity = None
    smile_section = None
    def __init__(self, strike, rTs, maturity, smile_section):
        self.strike = strike
        self.rTs = rTs
        self.maturity = maturity
        self.smile_section = smile_section
    def __call__(self, v0):
        optionType = ql.Option.Put
        deltaType = ql.DeltaVolQuote.Spot      # Also supports: Spot, PaSpot, PaFwd, Fwd
        localDcf, foreignDcf = self.rTs.discount(self.maturity), dividendTs.discount(self.maturity)
        stdDev = np.sqrt(ql.Actual365Fixed().yearFraction(today, self.maturity)) * v0
        calc = ql.BlackDeltaCalculator(optionType, deltaType, spot, localDcf, foreignDcf, stdDev)

        d = calc.deltaFromStrike(self.strike)
        #atmType = ql.DeltaVolQuote.AtmDeltaNeutral     # Also supports: AtmSpot, AtmDeltaNeutral, AtmVegaMax, AtmGammaMax, AtmPutCall50
        #print(f'ATM strike={calc.atmStrike(atmType)}')
        v = interp(d, allowExtrapolation=True)
        return (v - v0)

solver = ql.Brent()
accuracy = 1e-16
step = 1e-6
volatilities = []

print(f'Strike={k}')
for i in range(2):
    smile = vols[i]
    interp = ql.LinearInterpolation(deltas, smile)
    target = TargetFun(k, ratesTs, maturity[i], interp)
    guess = smile[2]   
    print(f'Maturity={maturity[i]}, volatility={solver.solve(target, accuracy, guess, step)}')
    volatilities.append(solver.solve(target, accuracy, guess, step))

vc_handle = ql.BlackVolTermStructureHandle(ql.BlackVarianceCurve(today, maturity, volatilities, ql.Actual365Fixed()))

# OPTION
maturity = ql.Date(15,6,2022)
option_type = ql.Option.Call
payoff = ql.PlainVanillaPayoff(option_type, k)
europeanExercise = ql.EuropeanExercise(maturity)
europeanOption = ql.VanillaOption(payoff, europeanExercise)

# ENGINE
process = ql.BlackScholesMertonProcess(ql.QuoteHandle(ql.SimpleQuote(spot)), dividendTs, ratesTs, vc_handle)
engine = ql.AnalyticEuropeanEngine(process)
europeanOption.setPricingEngine(engine)
print(f'NPV={europeanOption.NPV()}')
