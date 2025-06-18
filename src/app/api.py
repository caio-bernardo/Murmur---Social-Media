from ninja import NinjaAPI


app = NinjaAPI()

@app.get("/")
async def checkhealth(request):
    return {"detail": "API is on the air"}
